"""
eval_kojo.py — KojoBench main evaluation script

Mirrors TurtleBench's eval.py with the following changes:
  - Python Turtle → Kojo (Scala)
  - code_to_image uses Kojo online renderer
  - prompts reference Kojo API
  - model is the generic HFModel (HuggingFace Inference API)

Usage:
    python eval_kojo.py \\
      --task_type   scratch          # scratch | tweak
      --task_mode   code_generation  # code_generation | code_edit
      --modalities  image_only       # image_only | text_only | image+text | image+image
      --prompting_mode cot           # cot | basic | few-shot
      --save_responses               # keep raw LLM responses on disk

Before running:
  1. Edit models/hf_model.py — set HF_TOKEN and HF_API_URL.
  2. Run crawl_tasks.py to build dataset.jsonl from your Tasks/ directory.
  3. Make sure autotest/source/ contains ground-truth PNGs named {id}_{q}.png

If interrupted, resume scoring with:
    python calculate_score_kojo.py .responses/<run_name>
"""

import argparse
import datetime
import json
import os
import random
import tempfile

from tqdm import tqdm

from models.hf_model import HFModel
from prompts_kojo import system_prompts, user_prompts, user_prompt_final_piece
from utils.kojo_renderer import code_to_image
from utils.kojo_preprocess import preprocess_response
from utils.shape_similarity import calculate_accuracy
from calculate_score_kojo import _update_report


# ── Constants ─────────────────────────────────────────────────────────────────
DATASET_PATH = "dataset.jsonl"
SOURCE_PATH  = "autotest/source"
REPORT_PATH  = "reports/report.csv"


# ── Dataset loading ───────────────────────────────────────────────────────────

def _load_dataset() -> list[dict]:
    records = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))
    return records


def _filter_subset(
    config: list[dict],
    task_type: str,
    modalities: str,
) -> list[dict]:
    """
    Filter dataset rows to the relevant subset, exactly as TurtleBench does.
    """
    if task_type == "scratch" and "text" in modalities:
        # Only tasks that have a description
        return [c for c in config
                if c["question_number"] == 1 and c.get("description")]
    elif task_type == "scratch":
        return [c for c in config if c["question_number"] == 1]
    else:  # tweak
        return [c for c in config if c["question_number"] != 1]


# ── Prompt construction ───────────────────────────────────────────────────────

def _construct_prompts(
    task: dict,
    task_type: str,
    task_mode: str,
    modalities: str,
    prompting_mode: str,
) -> tuple[str, str, str | None, str | None]:
    """
    Build (system_prompt, user_prompt, image1_path, image2_path).
    image2_path is only non-None for image+image modality.
    """
    assert task_type in ("scratch", "tweak"), f"Unknown task_type: {task_type}"

    # ── System prompt ──────────────────────────────────────────────────────
    try:
        if task_type == "scratch":
            system_prompt = system_prompts[prompting_mode]["scratch"][modalities]
        else:
            system_prompt = (
                system_prompts[prompting_mode]["tweak"][task_mode][modalities]
            )
    except KeyError as e:
        raise ValueError(
            f"No prompt found for combination: "
            f"mode={prompting_mode}, type={task_type}, "
            f"task_mode={task_mode}, modalities={modalities}"
        ) from e

    # ── User prompt ────────────────────────────────────────────────────────
    if task_type == "scratch":
        user_prompt = user_prompts["scratch"][modalities]
    else:
        user_prompt = user_prompts["tweak"][task_mode][modalities]

    user_prompt = user_prompt.format(
        description=task.get("description", ""),
        code=task.get("base_shape_code", ""),
        query=task.get("query", ""),
        variables=task.get("variables", ""),
    )
    user_prompt += "\n" + user_prompt_final_piece.format(
        variables=task.get("variables", "")
    )

    image1 = task.get("base_shape")
    image2 = task.get("result_shape") if modalities == "image+image" else None

    return system_prompt, user_prompt, image1, image2


def _construct_prompts_few_shot(
    task: dict,
    subset: list[dict],
) -> tuple[str, list[tuple[str, str | None]], str | None, None]:
    """
    Build few-shot prompt: 4 random examples + the target task.
    Returns (system_prompt, [(user_prompt, image_path), ...], base_image, None)
    """
    system_prompt = system_prompts["few-shot"]["scratch"]["image_only"]

    population = [t for t in subset if t["id"] != task["id"]]
    examples   = random.sample(population, min(4, len(population)))

    example_prompts: list[tuple[str, str | None]] = []
    for ex in examples:
        ep = user_prompts["few_shot"]["scratch"].format(
            code=ex.get("base_shape_code", ""),
            variables=ex.get("variables", ""),
        )
        example_prompts.append((ep, ex.get("base_shape")))

    # Final query
    final_query = (
        user_prompts["scratch"]["image_only"]
        + "\n"
        + user_prompt_final_piece.format(variables=task.get("variables", ""))
    )
    example_prompts.append((final_query, task.get("base_shape")))

    return system_prompt, example_prompts, task.get("base_shape"), None


# ── Initialise report CSV ─────────────────────────────────────────────────────

def _init_report() -> None:
    os.makedirs("reports", exist_ok=True)
    if not os.path.exists(REPORT_PATH):
        import pandas as pd
        pd.DataFrame(columns=[
            "model_name", "task_type", "task_mode", "modalities",
            "prompting_mode", "time", "solved", "accuracy",
        ]).to_csv(REPORT_PATH, index=False)


# ── Main eval ─────────────────────────────────────────────────────────────────

def eval(
    task_type:      str = "scratch",
    task_mode:      str = "code_generation",
    modalities:     str = "image_only",
    prompting_mode: str = "cot",
    save_responses: bool = False,
) -> None:

    _init_report()
    config = _load_dataset()
    subset = _filter_subset(config, task_type, modalities)

    print(
        f"\n[eval] Running KojoBench\n"
        f"  task_type      = {task_type}\n"
        f"  task_mode      = {task_mode}\n"
        f"  modalities     = {modalities}\n"
        f"  prompting_mode = {prompting_mode}\n"
        f"  subset size    = {len(subset)}\n"
    )

    model = HFModel()   # reads HF_TOKEN / HF_API_URL from models/hf_model.py

    timestamp = datetime.datetime.now().strftime("%d-%m_%H:%M")
    run_name  = "|".join([
        "hf_model", task_type, task_mode, modalities, prompting_mode, timestamp,
    ])
    run_settings = {
        "model_name":    "hf_model",
        "task_type":     task_type,
        "task_mode":     task_mode,
        "modalities":    modalities,
        "prompting_mode": prompting_mode,
        "time":          timestamp,
    }

    # ── Set up response storage ────────────────────────────────────────────
    if save_responses:
        responses_path = os.path.join(".responses", run_name)
        images_path    = responses_path + "_images/"
        os.makedirs(responses_path, exist_ok=True)
        os.makedirs(images_path,    exist_ok=True)
    else:
        _tmpdir     = tempfile.mkdtemp(prefix="kojobench_")
        responses_path = os.path.join(_tmpdir, run_name)
        images_path    = responses_path + "_images/"
        os.makedirs(responses_path, exist_ok=True)
        os.makedirs(images_path,    exist_ok=True)

    # ── Initialise report entry ────────────────────────────────────────────
    _update_report(run_setting=run_settings.copy(), solved_counter=0, accuracy=0.0)

    # ── Evaluation loop ────────────────────────────────────────────────────
    solved_counter = 0
    pbar = tqdm(total=len(subset), desc="KojoBench eval")

    prompt_kwargs = dict(
        task_type=task_type,
        task_mode=task_mode,
        modalities=modalities,
        prompting_mode=prompting_mode,
    )

    for task in subset:
        task_name = f"{task['id']}_{task['question_number']}"

        # ── Build prompts ──────────────────────────────────────────────────
        if prompting_mode == "few-shot":
            system_prompt, few_shot_turns, image1, image2 = (
                _construct_prompts_few_shot(task, subset)
            )
            # For few-shot, collapse turns into a single user message
            # (simple models don't support multi-turn few-shot natively)
            user_message = "\n\n---\n\n".join(
                f"Example {i+1}:\n{turn[0]}" for i, turn in enumerate(few_shot_turns[:-1])
            )
            user_message += "\n\n---\n\nNow solve this task:\n" + few_shot_turns[-1][0]
        else:
            system_prompt, user_message, image1, image2 = _construct_prompts(
                task=task, **prompt_kwargs
            )

        # ── Call model ─────────────────────────────────────────────────────
        try:
            response = model.get_response(
                system_message=system_prompt,
                user_message=user_message,
                base_image=image1,
                result_image=image2,
                few_shot=(prompting_mode == "few-shot"),
            )
        except Exception as e:
            print(f"\n[eval] Task {task_name}: model call failed: {e}")
            response = ""

        # ── Save raw response ──────────────────────────────────────────────
        with open(os.path.join(responses_path, task_name + ".txt"), "w",
                  encoding="utf-8") as f:
            f.write(response or "")

        # ── Extract code + render ──────────────────────────────────────────
        code = preprocess_response(response)
        rendered = code_to_image(code, task_name, save_path=images_path)

        # ── Score ──────────────────────────────────────────────────────────
        if rendered:
            solved = calculate_accuracy(
                task_name,
                source_path=SOURCE_PATH,
                response_path=images_path,
            )
            if solved:
                solved_counter += 1

        current_accuracy = solved_counter / (pbar.n + 1) * 100
        pbar.set_postfix(accuracy=f"{current_accuracy:.2f}%")
        pbar.update(1)

    pbar.close()

    final_accuracy = solved_counter / len(subset) * 100 if subset else 0.0
    print(
        f"\n[eval] DONE — Accuracy: {final_accuracy:.2f}%  "
        f"({solved_counter}/{len(subset)})"
    )
    _update_report(run_settings, solved_counter, final_accuracy)

    if not save_responses:
        import shutil
        shutil.rmtree(_tmpdir, ignore_errors=True)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KojoBench — evaluate LLMs on Kojo turtle geometry tasks.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--task_type", type=str, default="scratch",
        help="scratch | tweak  (default: scratch)",
    )
    parser.add_argument(
        "--task_mode", type=str, default="code_generation",
        help="code_generation | code_edit  (default: code_generation)",
    )
    parser.add_argument(
        "--modalities", type=str, default="image_only",
        help=(
            "image_only | text_only | image+text | image+image\n"
            "(default: image_only)"
        ),
    )
    parser.add_argument(
        "--prompting_mode", type=str, default="cot",
        help="cot | basic | few-shot  (default: cot)",
    )
    parser.add_argument(
        "--save_responses", action="store_true",
        help="Save raw LLM responses to .responses/<run_name>/",
    )
    args = parser.parse_args()

    eval(
        task_type=args.task_type,
        task_mode=args.task_mode,
        modalities=args.modalities,
        prompting_mode=args.prompting_mode,
        save_responses=args.save_responses,
    )


if __name__ == "__main__":
    main()
