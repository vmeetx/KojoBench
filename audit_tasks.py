# audit_tasks.py
# Runs every task through the renderer, compares IoU against ground truth,
# prints a sorted table of failures with their IoU scores, then loops until
# no new failures appear or a max-iterations limit is hit.

import subprocess
import sys
from pathlib import Path

from PIL import Image

from utils.kojo_renderer import render
from utils.shape_similarity import compute_iou_score

SOURCE     = Path("autotest/source")
TASKS      = Path("Tasks")
TMP        = Path(".audit_tmp")
THRESHOLD  = 0.95
MAX_PASSES = 3


def pad(img, size=500):
    img.thumbnail((size, size))
    out = Image.new("RGB", (size, size), (255, 255, 255))
    out.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
    return out


def inject_vars(code: str, var_file: Path) -> str:
    if not var_file.exists():
        return code
    for line in var_file.read_text().splitlines():
        line = line.strip()
        if "=" in line:
            name, val = line.split("=", 1)
            code = code.replace(
                "setSpeed(fast)",
                f"setSpeed(fast)\nval {name.strip()} = {val.strip()}"
            )
    return code


def run_pass():
    TMP.mkdir(exist_ok=True)
    failures = []

    task_dirs = sorted(
        [d for d in TASKS.iterdir() if d.is_dir()],
        key=lambda d: int(d.name) if d.name.isdigit() else d.name,
    )

    for task_dir in task_dirs:
        code_dir = task_dir / "QA" / "code"
        if not code_dir.exists():
            continue
        for code_file in sorted(code_dir.glob("q*_code.txt")):
            q = code_file.stem.replace("_code", "")   # e.g. q1
            task_name = f"{task_dir.name}_{q[1:]}"    # e.g. 17_1
            gt_png = SOURCE / f"{task_name}.png"
            if not gt_png.exists():
                continue

            code = inject_vars(code_file.read_text(), task_dir / "variables.txt")
            out_png = str(TMP / f"{task_name}.png")
            ok, err = render(code, out_png)

            if not ok:
                failures.append((task_name, 0.0, f"RENDER FAIL: {err[:80]}"))
                continue

            iou = compute_iou_score(task_name, str(SOURCE), str(TMP))
            if iou < THRESHOLD:
                failures.append((task_name, iou, ""))

    return failures


def main():
    for pass_num in range(1, MAX_PASSES + 1):
        print(f"\n{'='*50}")
        print(f"PASS {pass_num}")
        print(f"{'='*50}")
        failures = run_pass()

        if not failures:
            print("ALL TASKS PASS")
            break

        failures.sort(key=lambda x: x[1])  # worst IoU first
        print(f"\nFAILURES ({len(failures)}):")
        print(f"{'Task':<12} {'IoU':>6}  Note")
        print("-" * 40)
        for name, iou, note in failures:
            print(f"{name:<12} {iou:>6.3f}  {note}")

        if pass_num < MAX_PASSES:
            print("\nRe-running converter...")
            subprocess.run([sys.executable, "convert_to_kojo.py"], check=True)


if __name__ == "__main__":
    main()
