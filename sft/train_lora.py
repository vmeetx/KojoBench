#!/usr/bin/env python3
"""
sft/train_lora.py  --  LoRA SFT on KojoBench2 data.

Model    : Qwen/Qwen2.5-Coder-1.5B-Instruct (4-bit NF4)
Hardware : RTX 3050 6GB (Ampere, bf16)
Framework: HF transformers + peft + trl  (no Unsloth)

Dataset  : 75 GT examples -> 80/20 train/val split (60 train, 15 val)
           Val split exists solely to detect overfitting; with 15 examples
           the signal is noisy but still catches catastrophic divergence.

Run from repo root:
    python sft/train_lora.py

Adapter saved to: sft/kojo-lora/
"""

import ast
import math
import os
import re
from pathlib import Path

os.environ["WANDB_DISABLED"] = "true"   # prevent wandb stdout hook on Windows cp1252

# -- Paths & hyperparameters --------------------------------------------------
REPO_ROOT     = Path(__file__).resolve().parent.parent
EVAL_PY       = REPO_ROOT / "eval" / "eval_kojobench2.py"
BENCHMARK_DIR = REPO_ROOT / "benchmark"
ADAPTER_OUT   = REPO_ROOT / "sft" / "adapters" / "qwen-1.5b-kojo-lora"

MODEL_ID      = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
MAX_SEQ_LEN   = 2048   # system prompt alone is ~1676 tokens; 1024 truncates targets
SEED          = 42
VAL_SPLIT     = 0.2    # 75 examples -> 60 train / 15 val

LORA_R        = 4
LORA_ALPHA    = 16
LORA_DROPOUT  = 0.05   # small regularization -- critical on a 60-example train set
EPOCHS        = 5      # EarlyStopping will cut this short if val loss stops improving
LR            = 2e-4
WARMUP_STEPS  = 8      # ~10% of 75 total steps (60 examples / eff_bs=4 * 5 epochs)
PER_DEVICE_BS = 1
GRAD_ACCUM    = 4      # effective batch size = 4


# -- 1. Extract SYSTEM_PROMPT (read file, don't import -- Java deps) ----------
def _extract_system_prompt() -> str:
    src = EVAL_PY.read_text(encoding="utf-8")
    m = re.search(r'(SYSTEM_PROMPT\s*=\s*""".*?""")', src, re.DOTALL)
    if not m:
        raise ValueError("SYSTEM_PROMPT triple-quoted string not found in eval_kojobench2.py")
    rhs = m.group(1).split("=", 1)[1].strip()
    return ast.literal_eval(rhs)


# -- 2. Extract raw drawing commands from a GT .kojo file ---------------------
def _extract_inner_code(kojo_path: Path) -> str:
    """
    GT structure:
        cleari()
        def shape = Picture {
            [4-space indented commands]
        }
        drawCentered(shape)

    Returns the inner commands with indent stripped, or "" on failure.
    """
    lines = kojo_path.read_text(encoding="utf-8").splitlines()
    start = end = None
    for i, line in enumerate(lines):
        if start is None and re.search(r"Picture\s*\{", line):
            start = i + 1
        if start is not None and "drawCentered" in line:
            end = i
            break
    if start is None or end is None:
        return ""

    inner = lines[start:end]
    while inner and inner[-1].strip() in ("", "}"):
        popped = inner.pop()
        if popped.strip() == "}":
            break

    dedented = []
    for line in inner:
        if line.startswith("    "):
            dedented.append(line[4:])
        elif line.strip() == "":
            dedented.append("")
        else:
            dedented.append(line.lstrip())
    return "\n".join(dedented).strip()


# -- 3. Build dataset with train/val split ------------------------------------
def build_dataset(system_prompt: str, tokenizer):
    """Returns (train_dataset, val_dataset) as HF Dataset objects."""
    from datasets import Dataset

    task_dirs = sorted(
        (d for d in BENCHMARK_DIR.iterdir() if d.name.startswith("Task")),
        key=lambda d: int(d.name[4:]),
    )

    records, skipped = [], []
    for task_dir in task_dirs:
        n          = task_dir.name[4:]
        query_path = task_dir / f"KojoQuery{n}.md"
        kojo_path  = task_dir / f"KojoTask{n}.kojo"
        if not query_path.exists() or not kojo_path.exists():
            skipped.append(n)
            continue
        code = _extract_inner_code(kojo_path)
        if not code:
            skipped.append(n)
            continue

        query      = query_path.read_text(encoding="utf-8").strip()
        first_line = query.splitlines()[0].rstrip(".").strip()
        geometry   = (
            f"<geometry>\n"
            f"Goal: {first_line}.\n"
            f"Canvas/scale: 500x500 pixels.\n"
            f"</geometry>"
        )
        assistant = f"{geometry}\n\n```scala\n{code}\n```"

        messages = [
            {"role": "system",    "content": system_prompt},
            {"role": "user",      "content": query},
            {"role": "assistant", "content": assistant},
        ]
        records.append({"messages": messages, "task": int(n)})

    if skipped:
        print(f"  Skipped: {skipped}")

    # Token-length audit before split
    lengths = [
        len(tokenizer.apply_chat_template(r["messages"], tokenize=True))
        for r in records
    ]
    over = sum(1 for l in lengths if l > MAX_SEQ_LEN)
    print(f"  Total examples  : {len(records)}")
    print(f"  Token lengths   : min={min(lengths)}  max={max(lengths)}  "
          f"mean={sum(lengths)//len(lengths)}  over {MAX_SEQ_LEN}: {over}")

    ds    = Dataset.from_list(records)
    split = ds.train_test_split(test_size=VAL_SPLIT, seed=SEED, shuffle=True)
    print(f"  Train / val     : {len(split['train'])} / {len(split['test'])}")
    return split["train"], split["test"]


# -- 4. Perplexity callback ---------------------------------------------------
def _make_callbacks():
    """Returns callbacks for perplexity logging and early stopping."""
    from transformers import TrainerCallback, EarlyStoppingCallback

    class PerplexityCallback(TrainerCallback):
        """Adds eval_perplexity to metrics dict and prints a tidy summary row."""

        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs is None:
                return
            parts = []
            if "loss" in logs:
                ppl = math.exp(min(logs["loss"], 100))
                parts.append(f"train_loss={logs['loss']:.4f}  train_ppl={ppl:.2f}")
            if "eval_loss" in logs:
                ppl = math.exp(min(logs["eval_loss"], 100))
                logs["eval_perplexity"] = ppl
                parts.append(f"eval_loss={logs['eval_loss']:.4f}  eval_ppl={ppl:.2f}")
            if parts:
                ep = logs.get("epoch", state.epoch or 0)
                print(f"  [ep {ep:.2f}] " + "  |  ".join(parts))

    return [
        PerplexityCallback(),
        EarlyStoppingCallback(early_stopping_patience=2),
    ]


# -- 5. Train -----------------------------------------------------------------
def train():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer, SFTConfig

    use_bf16      = torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if use_bf16 else torch.float16
    vram_gb       = torch.cuda.get_device_properties(0).total_memory // 1024**3
    print(f"CUDA  : {torch.cuda.get_device_name(0)}  bf16={use_bf16}  VRAM={vram_gb}GB")
    print(f"Model : {MODEL_ID}")
    print(f"LoRA  : r={LORA_R}  alpha={LORA_ALPHA}  dropout={LORA_DROPOUT}")
    print(f"Train : epochs={EPOCHS}  lr={LR}  eff_batch={PER_DEVICE_BS * GRAD_ACCUM}  "
          f"warmup_steps={WARMUP_STEPS}  seed={SEED}\n")

    system_prompt = _extract_system_prompt()
    print(f"System prompt: {len(system_prompt)} chars")

    # Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token    = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Dataset
    train_ds, val_ds = build_dataset(system_prompt, tokenizer)

    # 4-bit quantisation
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

    # LoRA
    lora = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    # Training config
    ADAPTER_OUT.mkdir(parents=True, exist_ok=True)
    args = SFTConfig(
        output_dir=str(ADAPTER_OUT),
        seed=SEED,
        # epochs & batching
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=PER_DEVICE_BS,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=GRAD_ACCUM,
        # LR schedule
        learning_rate=LR,
        warmup_steps=WARMUP_STEPS,
        lr_scheduler_type="cosine",
        max_grad_norm=1.0,
        # precision
        bf16=use_bf16,
        fp16=not use_bf16,
        # memory
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        # sequence
        max_length=MAX_SEQ_LEN,
        assistant_only_loss=True,      # loss only on assistant tokens, not 1676-token prompt
        # eval & checkpointing
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,            # keep only best + last checkpoint
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        # logging
        logging_steps=5,
        report_to="none",
        # misc
        dataloader_num_workers=0,      # avoid fork issues on Windows
        remove_unused_columns=False,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        args=args,
        callbacks=_make_callbacks(),
    )

    print("\n-- Training ----------------------------------------------------")
    result = trainer.train()

    # Print final summary
    train_loss = result.training_loss
    print(f"\n-- Final metrics -----------------------------------------------")
    print(f"  train_loss      : {train_loss:.4f}")
    print(f"  train_ppl       : {math.exp(min(train_loss, 100)):.2f}")

    metrics = trainer.evaluate()
    eval_loss = metrics.get("eval_loss", float("nan"))
    eval_ppl  = math.exp(min(eval_loss, 100))
    print(f"  eval_loss       : {eval_loss:.4f}")
    print(f"  eval_perplexity : {eval_ppl:.2f}")
    print(f"  stopped at epoch: {result.metrics.get('epoch', EPOCHS):.0f} / {EPOCHS}")

    model.save_pretrained(str(ADAPTER_OUT))
    tokenizer.save_pretrained(str(ADAPTER_OUT))
    print(f"\nAdapter saved -> {ADAPTER_OUT}")


# -- 6. Sanity check: base vs fine-tuned side-by-side ------------------------
def sanity_check():
    """Run Task 1 through both the raw base model and the LoRA adapter."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel

    print("\n-- Sanity check: base vs fine-tuned on Task 1 -----------------")

    system_prompt = _extract_system_prompt()
    query = (BENCHMARK_DIR / "Task1" / "KojoQuery1.md").read_text(encoding="utf-8").strip()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": query},
    ]

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

    def _generate(model, label):
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs  = tokenizer(prompt, return_tensors="pt").to("cuda")
        n_input = inputs["input_ids"].shape[1]
        print(f"\n  [{label}]  prompt={n_input} tokens")
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        response = tokenizer.decode(out[0][n_input:], skip_special_tokens=True)
        print(response)
        print(f"  <geometry>  : {'<geometry>' in response}")
        print(f"  ```scala    : {'```scala' in response}")
        return response

    # Load base model once and test it
    base = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, quantization_config=bnb, device_map="auto", trust_remote_code=True
    )
    base.eval()
    _generate(base, "BASE (no adapter)")

    # Attach LoRA adapter and test again
    ft = PeftModel.from_pretrained(base, str(ADAPTER_OUT))
    ft.eval()
    _generate(ft, "FINE-TUNED (LoRA adapter)")


if __name__ == "__main__":
    train()
    sanity_check()
