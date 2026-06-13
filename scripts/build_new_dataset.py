"""
Builds KojoNewDataset/ for tasks 1-10.

Each Task subfolder contains:
  KojoTask{N}.kojo        — Kojo code (with variables prepended)
  ground_truth_python.png — Python turtle rendered reference (copied from Tasks/)
  ground_truth_kojo.png   — image rendered from KojoTask{N}.kojo via headless

Run from the repo root:
  python scripts/build_new_dataset.py
"""

import os
import shutil
import sys
from pathlib import Path

# Allow imports from the repo root (utils/, models/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.kojo_renderer import render

BASE = Path(__file__).parent.parent   # repo root
NEW_DATASET = BASE / "KojoNewDataset"
TASKS = BASE / "Tasks"

TASK_DESCRIPTIONS = {
    9: "Two semicircles connected by a vertical line"
}

TURTLE_HEADER = """\
import turtle

{vars}

t = turtle.Turtle()
t.speed(0)
t.hideturtle()
screen = turtle.Screen()
screen.bgcolor("white")

"""

TURTLE_FOOTER = """
turtle.done()
"""

KOJO_HEADER = """\
clear()
setSpeed(fast)
setHeading(0)
setPenColor(black)
invisible()
{vars}
"""


def parse_vars(variables_txt: str) -> dict:
    """Parse 'key=value' lines into a dict."""
    result = {}
    for line in variables_txt.strip().splitlines():
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def vars_as_python(var_dict: dict) -> str:
    lines = []
    for k, v in var_dict.items():
        try:
            float(v)
            lines.append(f"{k} = {v}")
        except ValueError:
            lines.append(f'{k} = "{v}"')
    return "\n".join(lines)


def vars_as_kojo(var_dict: dict) -> str:
    lines = []
    for k, v in var_dict.items():
        try:
            val = float(v)
            if val == int(val):
                lines.append(f"val {k} = {int(val)}")
            else:
                lines.append(f"val {k} = {val}")
        except ValueError:
            lines.append(f'val {k} = "{v}"')
    return "\n".join(lines)


def strip_kojo_header(code: str) -> str:
    """Remove the boilerplate header lines already in q1_code.txt."""
    skip = {"clear()", "setSpeed(fast)", "setHeading(0)", "setPenColor(black)"}
    lines = []
    for line in code.splitlines():
        if line.strip() in skip:
            continue
        lines.append(line)
    # drop leading blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines)




def build_task(task_id: int):
    task_dir = TASKS / str(task_id)
    out_dir = NEW_DATASET / f"Task{task_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── variables ──────────────────────────────────────────────────────────────
    vars_file = task_dir / "variables.txt"
    variables_txt = vars_file.read_text(encoding="utf-8") if vars_file.exists() else ""
    var_dict = parse_vars(variables_txt)

    # ── Python turtle file ─────────────────────────────────────────────────────
    py_orig = task_dir / "QA" / "code" / "q1_code.py_orig"
    py_core = py_orig.read_text(encoding="utf-8").strip() if py_orig.exists() else "# code not found"
    py_content = (
        TURTLE_HEADER.format(vars=vars_as_python(var_dict))
        + py_core
        + TURTLE_FOOTER
    )
    (out_dir / f"TurtleTask{task_id}.py").write_text(py_content, encoding="utf-8")

    # ── Kojo file ──────────────────────────────────────────────────────────────
    kojo_orig = task_dir / "QA" / "code" / "q1_code.txt"
    kojo_core_raw = kojo_orig.read_text(encoding="utf-8").strip() if kojo_orig.exists() else "// code not found"
    kojo_body = strip_kojo_header(kojo_core_raw)
    kojo_content = KOJO_HEADER.format(vars=vars_as_kojo(var_dict)) + "\n" + kojo_body + "\n"
    (out_dir / f"KojoTask{task_id}.kojo").write_text(kojo_content, encoding="utf-8")

    # ── ground truth image ─────────────────────────────────────────────────────
    gt_src = task_dir / "image" / f"{task_id}.png"
    if gt_src.exists():
        shutil.copy2(gt_src, out_dir / "ground_truth_python.png")
    else:
        print(f"  WARNING: ground truth missing for Task {task_id}: {gt_src}")

    # ── generated image ────────────────────────────────────────────────────────
    gen_out = str(out_dir / "ground_truth_kojo.png")
    ok, err = render(kojo_content, gen_out)
    if not ok:
        print(f"  WARNING: Task {task_id} render failed: {err}")

    print(f"Task {task_id:>2}  ->  {out_dir}")


if __name__ == "__main__":
    NEW_DATASET.mkdir(exist_ok=True)
    for i in range(1, 11):
        build_task(i)
    print("\nDone. KojoNewDataset/ populated for Tasks 1-10.")
