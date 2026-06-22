"""
Side-by-side comparison: Ground Truth vs Claude vs Qwen (LM Studio).
Big images, one row per task.
Run: python ClaudeSelfEval/run.py compare
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import numpy as np

GT_DIR      = Path(__file__).parent.parent / "benchmark"
CLAUDE_DIR  = Path(__file__).parent / "claude_rendered"
QWEN_DIR    = Path(__file__).parent / "qwen_rendered"
TASKS       = list(range(1, 76))

LABELS = ["Ground Truth", "Claude Sonnet 4.6", "Qwen (LM Studio)"]
COLORS = ["#888888",      "#a78bfa",           "#34d399"]
BG     = "#0d0d0d"
ROW_BG = ["#141414", "#1a1a1a"]

def load(path):
    try:
        return mpimg.imread(str(path)) if path and Path(path).exists() else None
    except Exception:
        return None

def get_paths(task_id):
    gt   = GT_DIR    / f"Task{task_id}" / "ground_truth_kojo.png"
    cl   = CLAUDE_DIR / f"task{task_id}.png"
    qw   = QWEN_DIR   / f"task{task_id}.png"
    return gt, cl, qw

def query_short(task_id):
    f = GT_DIR / f"Task{task_id}" / f"KojoQuery{task_id}.md"
    if not f.exists():
        return f"Task {task_id}"
    txt = f.read_text(encoding="utf-8").strip()
    line = next((l for l in txt.splitlines() if l.strip()), txt)
    return line[:60] + ("..." if len(line) > 60 else "")

def main():
    n = len(TASKS)
    col_w = 4.5
    row_h = 3.8
    label_w = 0.5

    fig_w = label_w + 3 * col_w + 0.4
    fig_h = n * row_h + 1.2

    fig = plt.figure(figsize=(fig_w, fig_h), num="GT vs Claude vs Qwen")
    fig.patch.set_facecolor(BG)

    # Header
    fig.text(0.5, 0.995, "KojoBench2  —  Ground Truth  vs  Claude Sonnet 4.6  vs  Qwen (LM Studio)",
             ha="center", va="top", fontsize=13, fontweight="bold", color="white")

    # Column headers
    total_w = fig_w
    for ci, (lbl, col) in enumerate(zip(LABELS, COLORS)):
        x = (label_w + ci * col_w + col_w * 0.5) / total_w
        fig.text(x, 0.988, lbl, ha="center", va="top",
                 fontsize=11, fontweight="bold", color=col)

    for ri, task_id in enumerate(TASKS):
        gt_path, cl_path, qw_path = get_paths(task_id)
        imgs = [load(gt_path), load(cl_path), load(qw_path)]
        q    = query_short(task_id)

        # Row y range (top to bottom)
        y_top = 1.0 - (1.2 / fig_h) - ri * (row_h / fig_h)
        y_h   = (row_h - 0.25) / fig_h
        y_bot = y_top - y_h

        # Row background
        bg_ax = fig.add_axes([0, y_bot - 0.005, 1.0, y_h + 0.012])
        bg_ax.set_facecolor(ROW_BG[ri % 2])
        bg_ax.axis("off")

        # Task label on left
        fig.text(label_w * 0.5 / total_w, y_bot + y_h * 0.5,
                 f"T{task_id}", ha="center", va="center",
                 fontsize=14, fontweight="bold", color="white")
        fig.text(label_w * 0.5 / total_w, y_bot + y_h * 0.18,
                 q, ha="center", va="center",
                 fontsize=5.5, color="#777", wrap=True,
                 transform=fig.transFigure)

        for ci, (img, col) in enumerate(zip(imgs, COLORS)):
            x0 = (label_w + ci * col_w + 0.12) / total_w
            x1 = (label_w + (ci + 1) * col_w - 0.12) / total_w
            ax = fig.add_axes([x0, y_bot + 0.01, x1 - x0, y_h - 0.01])
            ax.set_facecolor("#111")
            ax.axis("off")

            # Colored border
            for spine in ax.spines.values():
                spine.set_visible(True)
                spine.set_color(col)
                spine.set_linewidth(1.5)

            if img is not None:
                ax.imshow(img, aspect="equal")
            else:
                ax.text(0.5, 0.5, "not rendered", ha="center", va="center",
                        color="#444", fontsize=9, transform=ax.transAxes)

    plt.tight_layout(rect=[0, 0, 1, 0.985])
    plt.show(block=True)

if __name__ == "__main__":
    main()
