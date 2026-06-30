#!/usr/bin/env python3
"""
sft/eval_baseline.py - HF-native baseline eval (no fine-tuning).

Runs a base HuggingFace model through the same KojoBench2 eval pipeline used
for the Qwen 7B baseline (runs/eval_lmstudio.py) — same system prompt, same
75 queries, same NSS/KCSS scoring, same matplotlib results window. Inference
goes straight through HF transformers (4-bit NF4) instead of an LM Studio
API server.

Run from repo root:
    python sft/eval_baseline.py
    python sft/eval_baseline.py --model Qwen/Qwen2.5-Coder-7B-Instruct
    python sft/eval_baseline.py --start 10 --skip-existing
"""
import argparse
import ast
import os
import re
import sys
import time
from pathlib import Path

os.environ["WANDB_DISABLED"] = "true"

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "runs"))

from eval_engine import TASKS as _ALL_TASKS, load_query, extract_code, render_code, score_task, show_window

_DROP_TASKS = {1, 16, 50, 60}   # NSS scorer blind spots — excluded from scoring
TASKS       = [t for t in _ALL_TASKS if t not in _DROP_TASKS]

MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B-Instruct"   # overridable via --model

_THINK_RE = re.compile(r'<think>.*?</think>', re.DOTALL)


# -- Extract SYSTEM_PROMPT (read file, don't import - module has Java deps) --
def _extract_system_prompt() -> str:
    src = (REPO_ROOT / "eval" / "eval_kojobench2.py").read_text(encoding="utf-8")
    m = re.search(r'(SYSTEM_PROMPT\s*=\s*""".*?""")', src, re.DOTALL)
    if not m:
        raise ValueError("SYSTEM_PROMPT triple-quoted string not found in eval_kojobench2.py")
    rhs = m.group(1).split("=", 1)[1].strip()
    return ast.literal_eval(rhs)


def load_model(model_id: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    use_bf16      = torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if use_bf16 else torch.float16
    print(f"CUDA: {torch.cuda.get_device_name(0)}  bf16={use_bf16}  "
          f"VRAM={torch.cuda.get_device_properties(0).total_memory // 1024**3}GB")
    print(f"Model: {model_id} (4-bit NF4, base -- no adapter)\n")

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return model, tokenizer


def generate(model, tokenizer, system_prompt: str, query: str) -> str:
    import torch

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": query},
    ]
    tokenized = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt",
    )
    # apply_chat_template returns BatchEncoding (dict-like); extract input_ids tensor
    input_ids = (tokenized["input_ids"] if hasattr(tokenized, "__getitem__") else tokenized).to("cuda")

    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=8192,
            do_sample=False,        # temperature=0.0 equivalent
            pad_token_id=tokenizer.eos_token_id,
        )

    new_tokens = out[0][input_ids.shape[-1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=MODEL_ID, help="HuggingFace model ID")
    parser.add_argument("--start", type=int, default=1, help="Resume from this task number")
    parser.add_argument("--skip-existing", action="store_true", help="Skip tasks that already have a rendered PNG")
    parser.add_argument("--no-window", action="store_true", help="Skip the blocking matplotlib results window")
    args = parser.parse_args()

    # Derive output dir from model name: Qwen/Qwen2.5-Coder-1.5B -> qwen2.5-coder-1.5b
    slug    = args.model.split("/")[-1].lower()
    OUT_DIR = Path(__file__).parent / "results" / slug
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    system_prompt = _extract_system_prompt()
    model, tokenizer = load_model(args.model)

    print(f"[baseline] model={args.model}\n")
    results = []

    for t in [t for t in TASKS if t >= args.start]:
        out_png = OUT_DIR / f"task{t}.png"
        if args.skip_existing and out_png.exists():
            print(f"  Task {t}: skip (already rendered)")
            continue

        query = load_query(t)
        print(f"  Task {t}: generating...", end=" ", flush=True)

        try:
            response = generate(model, tokenizer, system_prompt, query)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append(score_task(t, ""))
            continue

        clean = _THINK_RE.sub("", response).strip()
        code  = extract_code(clean) or extract_code(response)
        print(f"got {len(code)} chars code - rendering...", end=" ", flush=True)

        rendered = render_code(t, code, OUT_DIR)
        print("ok" if rendered else "FAILED")

        (OUT_DIR / f"task{t}_response.txt").write_text(response, encoding="utf-8")
        if code:
            (OUT_DIR / f"task{t}.kojo").write_text(code, encoding="utf-8")

        r = score_task(t, code, rendered)
        nss_str = f"NSS={r['nss']*100:.0f}%" if r["nss"] is not None else "NSS=n/a"
        print(f"    KCSS={r['kcss']*100:.0f}%  {nss_str}  lines={r['lines']}  idioms={r['idioms']}")
        results.append(r)
        time.sleep(0.2)

    avg_k = sum(r["kcss"] for r in results) / len(results)
    nss_v = [r["nss"] for r in results if r["nss"] is not None]
    avg_n = sum(nss_v) / len(nss_v) if nss_v else None
    print(f"\n  Avg KCSS: {avg_k*100:.0f}%  Avg NSS: {avg_n*100:.1f}%" if avg_n else f"\n  Avg KCSS: {avg_k*100:.0f}%")

    if args.no_window:
        return
    show_window(f"{args.model} (base, 4-bit)", results, accent="#fb923c")


if __name__ == "__main__":
    main()
