"""
calculate_score_kojo.py

Re-scores a directory of already-saved model responses.
Run this if eval_kojo.py was interrupted before completion.

Usage:
    python calculate_score_kojo.py <responses_path>

Where <responses_path> is a directory like:
    .responses/hf_model|scratch|code_generation|image_only|cot|01-06_14:30

Each .txt file in that directory is a raw model response for one task.
The filename format is:  <task_id>_<question_number>.txt
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from utils.kojo_renderer import code_to_image
from utils.kojo_preprocess import preprocess_response
from utils.shape_similarity import calculate_accuracy


REPORT_PATH  = "reports/report.csv"
SOURCE_PATH  = "autotest/source"


def _get_settings_from_path(path: str) -> dict:
    """Extract run settings from the directory name (pipe-delimited)."""
    folder = os.path.basename(path.rstrip("/"))
    parts  = folder.split("|")
    keys   = ["model_name", "task_type", "task_mode", "modalities",
               "prompting_mode", "time"]
    return dict(zip(keys, parts))


def _update_report(run_setting: dict, solved_counter: int, accuracy: float) -> None:
    if not os.path.exists(REPORT_PATH):
        # Create report file with headers
        df = pd.DataFrame(columns=[
            "model_name", "task_type", "task_mode", "modalities",
            "prompting_mode", "time", "solved", "accuracy",
        ])
        df.to_csv(REPORT_PATH, index=False)

    df = pd.read_csv(REPORT_PATH)

    mask = True
    for k, v in run_setting.items():
        if k in df.columns:
            mask = mask & (df[k] == v)

    if hasattr(mask, "any") and mask.any():
        df.loc[mask, "solved"]   = solved_counter
        df.loc[mask, "accuracy"] = accuracy
    else:
        new_row = {**run_setting, "solved": solved_counter, "accuracy": accuracy}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_csv(REPORT_PATH, index=False)
    print(f"[report] Updated {REPORT_PATH}")


def calculate_score(responses_path: str) -> None:
    settings   = _get_settings_from_path(responses_path)
    task_files = [f for f in os.listdir(responses_path) if f.endswith(".txt")]

    if not task_files:
        print(f"[calculate_score] No .txt files found in {responses_path}")
        return

    images_path    = responses_path.rstrip("/") + "_images/"
    os.makedirs(images_path, exist_ok=True)

    solved_counter = 0

    for task_file in sorted(task_files):
        task_name = task_file.replace(".txt", "")
        response_path_full = os.path.join(responses_path, task_file)

        with open(response_path_full, "r", encoding="utf-8") as f:
            response = f.read()

        code = preprocess_response(response)
        rendered = code_to_image(code, task_name, save_path=images_path)

        if rendered:
            solved = calculate_accuracy(
                task_name,
                source_path=SOURCE_PATH,
                response_path=images_path,
            )
            if solved:
                solved_counter += 1

    accuracy = solved_counter / len(task_files) if task_files else 0.0
    print(
        f"\n[calculate_score] {responses_path}\n"
        f"  Solved {solved_counter} / {len(task_files)} = {accuracy * 100:.2f}%"
    )
    _update_report(settings, solved_counter, accuracy)


def main():
    parser = argparse.ArgumentParser(description="Re-score saved model responses.")
    parser.add_argument("responses_path", type=str,
                        help="Path to directory of saved .txt response files")
    args = parser.parse_args()
    calculate_score(args.responses_path)


if __name__ == "__main__":
    main()
