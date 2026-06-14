"""
scripts/build_kojobench2.py

Builds KojoBench2/ — a clean version of the benchmark where:
  - Each KojoTask uses the drawCentered(Picture{...}) pattern for better cropping
  - Queries are plain grade-6-style descriptions (no Kojo commands)
  - No Python ground-truth files

Run from repo root:
    python scripts/build_kojobench2.py
"""

import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.kojo_renderer import render

BASE       = Path(__file__).parent.parent
SRC        = BASE / "KojoNewDataset"
DEST       = BASE / "KojoBench2"

# Lines to strip from the old-style header before wrapping in Picture{}
_STRIP_RE = re.compile(
    r'^\s*(clear\(\)|cleari\(\)|setSpeed\([^)]*\)|invisible\(\))\s*$'
)


def wrap_in_picture(kojo_src: str) -> str:
    """
    Convert old-style Kojo script to drawCentered(Picture{...}) form.

    Old header lines (clear, setSpeed, invisible) are dropped — cleari()
    at the top replaces them.  Everything else (setHeading, val, drawing
    commands) moves inside the Picture block.
    """
    lines = kojo_src.splitlines()
    body_lines = [l for l in lines if not _STRIP_RE.match(l)]
    # Drop leading blank lines from body
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    body = "\n".join("    " + l for l in body_lines)
    return f"cleari()\n\ndef shape = Picture {{\n{body}\n}}\n\ndrawCentered(shape)\n"


def build_task(task_id: int):
    src_dir  = SRC  / f"Task{task_id}"
    dest_dir = DEST / f"Task{task_id}"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # ── Kojo file with drawCentered wrapper ───────────────────────────────────
    kojo_src_path = src_dir / f"KojoTask{task_id}.kojo"
    if not kojo_src_path.exists():
        print(f"  Task {task_id}: KojoTask file missing, skipping")
        return

    kojo_src = kojo_src_path.read_text(encoding="utf-8")
    wrapped  = wrap_in_picture(kojo_src)
    kojo_dest = dest_dir / f"KojoTask{task_id}.kojo"
    kojo_dest.write_text(wrapped, encoding="utf-8")

    # ── Render ground truth ───────────────────────────────────────────────────
    gt_out = str(dest_dir / "ground_truth_kojo.png")
    ok, err = render(wrapped, gt_out)
    if not ok:
        print(f"  Task {task_id}: render FAILED — {err.splitlines()[0][:80] if err else '?'}")
    else:
        print(f"  Task {task_id}: rendered -> {gt_out}")

    # ── Query file ────────────────────────────────────────────────────────────
    query_src = src_dir / f"KojoQuery{task_id}.md"
    if query_src.exists():
        shutil.copy2(query_src, dest_dir / f"KojoQuery{task_id}.md")


if __name__ == "__main__":
    print(f"Building KojoBench2 -> {DEST}\n")
    DEST.mkdir(exist_ok=True)
    for i in range(1, 11):
        build_task(i)
    print("\nDone.")
