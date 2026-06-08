"""
crawl_tasks.py — KojoBench dataset crawler

Walks the Tasks/ directory and assembles dataset.jsonl.
Mirrors TurtleBench's crawl_tasks.py with Kojo-specific field names.

Task directory structure (identical to TurtleBench):
    Tasks/
      {id}/
        description.txt          (optional — text description of base shape)
        variables.txt            (variable declarations to seed the model)
        image/{id}.png           (base shape image)
        result_image/
          q1_image.png           (target image for question 1 = "copy exact")
          q2_image.png           (target image for question 2, etc.)
        QA/
          code/
            q1_code.txt          (reference Kojo code for question 1)
            q2_code.txt          (reference Kojo code for question 2, etc.)
          text/
            q1.txt               (q1 = "create the exact same shape")
            q2.txt               (query text for question 2, etc.)

Each row in dataset.jsonl:
    id                 : int   — task ID
    question_number    : int   — question index (1 = scratch, 2+ = tweak)
    description        : str|None
    variables          : str
    base_shape         : str   — path to Tasks/{id}/image/{id}.png
    result_shape       : str   — path to Tasks/{id}/result_image/q{n}_image.png
    base_shape_code    : str   — contents of QA/code/q1_code.txt (base shape code)
    query              : str   — contents of QA/text/q{n}.txt
"""

import os
import json
from pathlib import Path


TASKS_DIR   = "Tasks"
OUTPUT_FILE = "dataset.jsonl"


def _read_file(path: str) -> str | None:
    """Return file contents as a stripped string, or None if file absent."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def crawl_tasks() -> None:
    records = []

    task_ids = sorted(
        [d for d in os.listdir(TASKS_DIR)
         if os.path.isdir(os.path.join(TASKS_DIR, d))],
        key=lambda x: int(x) if x.isdigit() else x,
    )

    for task_id in task_ids:
        task_dir = os.path.join(TASKS_DIR, task_id)

        # ── Shared fields for all questions in this task ──────────────────
        description  = _read_file(os.path.join(task_dir, "description.txt"))
        variables    = _read_file(os.path.join(task_dir, "variables.txt")) or ""
        base_image   = os.path.join(task_dir, "image", f"{task_id}.png")
        base_code    = _read_file(
            os.path.join(task_dir, "QA", "code", "q1_code.txt")
        ) or ""

        # ── Discover questions ────────────────────────────────────────────
        qa_text_dir  = os.path.join(task_dir, "QA", "text")
        result_dir   = os.path.join(task_dir, "result_image")

        if not os.path.isdir(qa_text_dir):
            print(f"[crawl] Task {task_id}: missing QA/text/ directory, skipping.")
            continue

        question_files = sorted(
            [f for f in os.listdir(qa_text_dir) if f.endswith(".txt")],
            key=lambda x: int(x.replace("q", "").replace(".txt", "")),
        )

        for qf in question_files:
            q_num = int(qf.replace("q", "").replace(".txt", ""))
            query = _read_file(os.path.join(qa_text_dir, qf)) or ""

            result_image = os.path.join(result_dir, f"q{q_num}_image.png")

            record = {
                "id":               int(task_id) if task_id.isdigit() else task_id,
                "question_number":  q_num,
                "description":      description,
                "variables":        variables,
                "base_shape":       base_image,
                "result_shape":     result_image,
                "base_shape_code":  base_code,
                "query":            query,
            }
            records.append(record)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    print(f"[crawl] Wrote {len(records)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    crawl_tasks()
