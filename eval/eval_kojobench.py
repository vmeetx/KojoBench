"""
eval_kojobench.py

Runs an LM Studio model on KojoNewDataset tasks 1-10.
Each task gets only its KojoQuery{N}.md description + the Kojo API reference.
No Python code, no reference solution is shown to the model.

Usage (from repo root):
    python eval/eval_kojobench.py
    python eval/eval_kojobench.py --tasks 1 2 3   # subset
    python eval/eval_kojobench.py --no-ui          # print table only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.kojo_renderer import render
from utils.kojo_preprocess import preprocess_response
from utils.shape_similarity import nss_score
from utils.prompts_kojo import KOJO_API_REF
from models.lm_studio import LMStudioModel

BASE        = Path(__file__).parent.parent
DATASET_DIR = BASE / "KojoNewDataset"

KOJO_HEADER = "clear()\nsetSpeed(fast)\nsetHeading(0)\nsetPenColor(black)\ninvisible()\n"

SYSTEM_PROMPT = (
    "You are a Kojo turtle graphics programmer.\n"
    "Given a description of a shape to draw, write Kojo code to draw it.\n"
    "Use ONLY the commands in the API reference below.\n"
    "Keep the code simple and direct — no classes, no objects, no main method.\n"
    "Output ONLY the Kojo code inside a ```scala ... ``` code fence. Nothing else.\n\n"
    + KOJO_API_REF
)


def _ensure_header(code: str) -> str:
    """Prepend standard boilerplate if the model omitted it."""
    if "clear()" not in code:
        code = KOJO_HEADER + "\n" + code
    elif "invisible()" not in code:
        code = code.replace("clear()", "clear()\ninvisible()", 1)
    return code


def run_task(task_id: int, model: LMStudioModel) -> dict:
    task_dir   = DATASET_DIR / f"Task{task_id}"
    query_path = task_dir / f"KojoQuery{task_id}.md"
    gt_path    = task_dir / "generated.png"
    out_path   = task_dir / "llm_generated.png"

    result = {
        "id":       task_id,
        "desc":     "",
        "score":    0.0,
        "status":   "error",
        "out_path": out_path,
        "gt_path":  gt_path,
    }

    if not query_path.exists():
        result["status"] = "no query file"
        return result
    if not gt_path.exists():
        result["status"] = "no reference render (run build_new_dataset.py first)"
        return result

    query_text = query_path.read_text(encoding="utf-8").strip()
    result["desc"] = query_text.splitlines()[0][:65]

    # ── Call the model ─────────────────────────────────────────────────────────
    print(f"  Task {task_id}: querying model...", end=" ", flush=True)
    try:
        response = model.get_response(
            system_message=SYSTEM_PROMPT,
            user_message=query_text,
        )
    except Exception as e:
        print(f"FAILED ({e})")
        result["status"] = f"model error: {e}"
        return result

    # ── Extract + fix up code ──────────────────────────────────────────────────
    code = preprocess_response(response)
    if not code:
        print("no code extracted")
        result["status"] = "no code"
        return result
    code = _ensure_header(code)

    # ── Render ────────────────────────────────────────────────────────────────
    ok, err = render(code, str(out_path))
    if not ok:
        short = err.splitlines()[0][:80] if err else "unknown"
        print(f"render failed: {short}")
        result["status"] = f"render failed: {short}"
        return result

    # ── Score ─────────────────────────────────────────────────────────────────
    score = nss_score(str(gt_path), str(out_path))
    result.update({
        "score":  score,
        "status": "ok",
    })
    print(f"NSS={score*100:.1f}%")
    return result


# ── UI ────────────────────────────────────────────────────────────────────────

def show_ui(results: list[dict], model_name: str):
    import numpy as np
    from PIL import Image
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    ok_tasks = [r for r in results if r["status"] == "ok"]
    n = len(results)
    avg = sum(r["score"] for r in ok_tasks) / len(ok_tasks) if ok_tasks else 0.0

    def score_color(s):
        if s >= 0.75: return "#2ecc71"
        if s >= 0.50: return "#f39c12"
        return "#e74c3c"

    fig = plt.figure(figsize=(15, 3.8 * n), facecolor="#1a1a2e")
    fig.canvas.manager.set_window_title(f"KojoBench — {model_name}")
    fig.suptitle(
        f"Model: {model_name}   |   Tasks: {n}   |   Avg NSS: {avg*100:.1f}%   "
        f"({len(ok_tasks)}/{n} rendered)",
        fontsize=13, color="white", y=1.001, fontweight="bold",
    )

    outer = gridspec.GridSpec(n, 1, figure=fig, hspace=0.6)

    for row, r in enumerate(results):
        inner = gridspec.GridSpecFromSubplotSpec(
            2, 3,
            subplot_spec=outer[row],
            width_ratios=[1, 1, 0.55],
            height_ratios=[0.18, 1],
            hspace=0.08, wspace=0.15,
        )

        # Header row
        ax_hdr = fig.add_subplot(inner[0, :])
        ax_hdr.set_facecolor("#16213e")
        ax_hdr.axis("off")
        color = score_color(r["score"])
        ax_hdr.text(0.01, 0.5, f"Task {r['id']}  —  {r['desc']}",
                    transform=ax_hdr.transAxes,
                    fontsize=10, color="white", va="center", ha="left")
        status_txt = (
            f"NSS: {r['score']*100:.1f}%"
            if r["status"] == "ok" else f"[{r['status']}]"
        )
        ax_hdr.text(0.99, 0.5, status_txt,
                    transform=ax_hdr.transAxes,
                    fontsize=9, color=color if r["status"] == "ok" else "#e74c3c",
                    va="center", ha="right", fontweight="bold")

        # Ground truth
        ax_gt = fig.add_subplot(inner[1, 0])
        ax_gt.imshow(np.array(Image.open(r["gt_path"]).convert("RGB")))
        ax_gt.set_title("Ground Truth", fontsize=8, color="#aaaaaa", pad=3)
        ax_gt.axis("off")

        # LLM generated
        ax_gen = fig.add_subplot(inner[1, 1])
        if r["status"] == "ok" and r["out_path"].exists():
            ax_gen.imshow(np.array(Image.open(r["out_path"]).convert("RGB")))
            ax_gen.set_title("LLM Generated", fontsize=8, color="#aaaaaa", pad=3)
        else:
            ax_gen.set_facecolor("#111111")
            ax_gen.text(0.5, 0.5, r["status"], transform=ax_gen.transAxes,
                        color="#e74c3c", ha="center", va="center", fontsize=9)
            ax_gen.set_title("LLM Generated", fontsize=8, color="#aaaaaa", pad=3)
        ax_gen.axis("off")

        # Score bars
        ax_bar = fig.add_subplot(inner[1, 2])
        ax_bar.set_facecolor("#0f3460")
        ax_bar.axis("off")
        if r["status"] == "ok":
            y = 0.5
            ax_bar.barh(y, r["score"], height=0.3, color=color, alpha=0.85, left=0)
            ax_bar.barh(y, 1.0, height=0.3, color="#ffffff", alpha=0.06, left=0)
            ax_bar.text(-0.02, y, "NSS", fontsize=8, color="white",
                        va="center", ha="right")
            ax_bar.text(r["score"] + 0.02, y, f"{r['score']*100:.0f}%",
                        fontsize=9, color=color, va="center", ha="left",
                        fontweight="bold")
            ax_bar.set_xlim(0, 1.35)
            ax_bar.set_ylim(0, 1.0)

    plt.tight_layout()
    plt.show()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate LM Studio model on KojoNewDataset tasks."
    )
    parser.add_argument("--tasks", type=int, nargs="+", metavar="N",
                        default=list(range(1, 11)),
                        help="Task IDs to run (default: 1-10)")
    parser.add_argument("--no-ui", action="store_true",
                        help="Print table only, skip matplotlib window")
    args = parser.parse_args()

    model = LMStudioModel()
    model_name = model.model

    print(f"\nKojoBench eval — model: {model_name}")
    print(f"Tasks: {args.tasks}\n")

    results = []
    for task_id in args.tasks:
        results.append(run_task(task_id, model))

    # Print summary table
    ok = [r for r in results if r["status"] == "ok"]
    avg = sum(r["score"] for r in ok) / len(ok) if ok else 0.0

    print(f"\n{'Task':<6} {'NSS Score':>10}  Description")
    print("-" * 60)
    for r in results:
        if r["status"] == "ok":
            print(f"  {r['id']:<4} {r['score']*100:>8.1f}%   {r['desc']}")
        else:
            print(f"  {r['id']:<4} {'---':>8}    [{r['status']}]")
    print("-" * 60)
    print(f"  {'AVG':<4} {avg*100:>8.1f}%   ({len(ok)}/{len(results)} rendered)\n")

    if not args.no_ui:
        show_ui(results, model_name)


if __name__ == "__main__":
    main()
