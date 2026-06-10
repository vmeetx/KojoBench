#!/usr/bin/env python3
"""
audit_tasks.py

Runs every task through the Kojo renderer, compares IoU against ground truth,
and prints a failure table sorted worst-first.

Speed strategy:
- Renders are sequential (kojo-headless uses a shared p1/ dir — parallelism
  causes race conditions and ClassNotFound errors).
- The render cache in kojo_renderer.py is SHA-256 keyed, so unchanged tasks
  render instantly on re-runs. First pass is slow; subsequent passes are fast.
- Skip tasks with no ground-truth PNG immediately.
- Print progress live so you can see what's happening.

Usage:
    python audit_tasks.py              # full run
    python audit_tasks.py --task 88   # single task debug
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.kojo_renderer import render
from utils.shape_similarity import compute_iou_score

SOURCE    = Path("autotest/source")
TASKS     = Path("Tasks")
TMP       = Path(".audit_tmp")
THRESHOLD = 0.95


def inject_vars(code: str, var_file: Path) -> str:
    """
    Inject variables from variables.txt into the code, exactly matching
    test_render.py's injection logic. Converts Python list syntax to Scala Array.
    """
    if not var_file.exists():
        return code
    for line in var_file.read_text().splitlines():
        line = line.strip()
        if "=" in line:
            name, val = line.split("=", 1)
            name = name.strip()
            val  = val.strip()
            # Python list → Scala Array
            if val.startswith("[") and val.endswith("]"):
                val = "Array(" + val[1:-1] + ")"
            code = code.replace(
                "setAnimationDelay(0)",
                f"setAnimationDelay(0)\nval {name} = {val}"
            )
    return code


def run_task(task_dir: Path, code_file: Path) -> tuple[str, float, str]:
    """Render one task and return (task_name, iou, error_note)."""
    q = code_file.stem.replace("_code", "")   # q1, q2, ...
    task_name = f"{task_dir.name}_{q[1:]}"    # e.g. 88_1

    gt_png = SOURCE / f"{task_name}.png"
    if not gt_png.exists():
        return task_name, -1.0, "no ground truth"

    code    = inject_vars(code_file.read_text(encoding="utf-8"),
                          task_dir / "variables.txt")
    out_png = str(TMP / f"{task_name}.png")
    ok, err = render(code, out_png)

    if not ok:
        short_err = err.splitlines()[0][:100] if err else "unknown"
        return task_name, 0.0, f"RENDER FAIL: {short_err}"

    iou = compute_iou_score(task_name, str(SOURCE), str(TMP))
    return task_name, iou, ""


def collect_jobs(task_filter: int | None = None):
    task_dirs = sorted(
        [d for d in TASKS.iterdir() if d.is_dir()],
        key=lambda d: int(d.name) if d.name.isdigit() else d.name,
    )
    if task_filter is not None:
        task_dirs = [d for d in task_dirs if d.name == str(task_filter)]

    return [
        (task_dir, code_file)
        for task_dir in task_dirs
        if (task_dir / "QA" / "code").exists()
        for code_file in sorted((task_dir / "QA" / "code").glob("q*_code.txt"))
    ]


def run_audit(task_filter: int | None = None):
    TMP.mkdir(exist_ok=True)
    jobs = collect_jobs(task_filter)

    if not jobs:
        print("No tasks found.")
        return []

    failures = []
    passes   = 0

    for idx, (task_dir, code_file) in enumerate(jobs, 1):
        task_name, iou, note = run_task(task_dir, code_file)

        # Live progress line
        status = "SKIP" if iou < 0 else ("PASS" if iou >= THRESHOLD else "FAIL")
        print(f"[{idx:>4}/{len(jobs)}] {task_name:<12} {status}  IoU={iou:>6.3f}  {note}",
              flush=True)

        if iou >= THRESHOLD:
            passes += 1
        elif iou >= 0:
            failures.append((task_name, iou, note))

    return failures, passes, len(jobs)


def print_report(failures, passes, total):
    scored = total - sum(1 for _, iou, _ in failures if iou < 0)
    print(f"\n{'='*60}")
    print(f"RESULTS:  {passes} pass / {len(failures)} fail / {total} total")
    print(f"{'='*60}")

    if not failures:
        print("ALL TASKS PASS ✓")
        return

    # Split into render failures and low-IoU
    render_fails = [(n, i, e) for n, i, e in failures if "RENDER FAIL" in e]
    low_iou      = [(n, i, e) for n, i, e in failures if "RENDER FAIL" not in e]

    if render_fails:
        # Group render failures by error type
        from collections import defaultdict
        by_error: dict[str, list[str]] = defaultdict(list)
        for name, _, note in render_fails:
            # Collapse to error category
            if "IO error while decoding" in note:
                key = "encoding error (CRLF/UTF-8)"
            elif "illegal start of simple" in note:
                key = "Scala syntax error"
            elif "No such file or class" in note or "ClassNotFoundException" in note:
                key = "class not found (race condition)"
            elif "cannot remove" in note:
                key = "p1/ dir race condition"
            else:
                key = note[:60]
            by_error[key].append(name)

        print(f"\nRENDER FAILURES ({len(render_fails)}) by error type:")
        for err_type, names in sorted(by_error.items(), key=lambda x: -len(x[1])):
            print(f"  [{len(names):>3}]  {err_type}")
            print(f"         tasks: {', '.join(names[:10])}" +
                  (f" ... +{len(names)-10} more" if len(names) > 10 else ""))

    if low_iou:
        low_iou.sort(key=lambda x: x[1])
        print(f"\nLOW IoU FAILURES ({len(low_iou)}) — worst first:")
        print(f"  {'Task':<12} {'IoU':>6}")
        print(f"  {'-'*20}")
        for name, iou, _ in low_iou:
            print(f"  {name:<12} {iou:>6.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, default=None,
                        help="Run a single task number only")
    args = parser.parse_args()

    result = run_audit(args.task)
    if not result:
        return
    failures, passes, total = result
    print_report(failures, passes, total)


if __name__ == "__main__":
    main()