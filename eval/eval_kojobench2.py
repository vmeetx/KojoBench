"""
eval_kojobench2.py

Evaluates an LM Studio model on KojoBench2 tasks 1-10.

Key differences from eval_kojobench.py:
  - Dataset is KojoBench2/ (drawCentered ground-truth images)
  - LLM output is also wrapped in drawCentered(Picture{...}) before rendering
  - Queries are plain grade-6-style descriptions — no Kojo commands, no variable hints
  - System prompt reflects that queries come from a non-technical user

Usage (from repo root):
    python eval/eval_kojobench2.py
    python eval/eval_kojobench2.py --tasks 1 2 3
    python eval/eval_kojobench2.py --no-ui
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.kojo_renderer import render
from utils.kojo_preprocess import preprocess_response
from utils.shape_similarity import nss_score
from utils.prompts_kojo import KOJO_API_REF
from models.lm_studio import LMStudioModel

BASE        = Path(__file__).parent.parent
DATASET_DIR = BASE / "KojoBench2"

_KOJO_EXAMPLES = """\
--- KOJO CODE EXAMPLES ---
These are real working Kojo scripts. Study the style: short, direct, no classes,
no imports, no main method. Use `def` only when you genuinely reuse a command.

// Example A — regular hexagon, side 80
repeat(6) {
  forward(80)
  right(60)
}

// Example B — reusable polygon helper
// Note: use 360.0 (Double) so division is never truncated
def drawPolygon(sides: Int, length: Double) {
  val turn = 360.0 / sides
  repeat(sides) {
    forward(length)
    right(turn)
  }
}
drawPolygon(8, 60)   // octagon, side 60

// WRONG — never wrap code like this:
// object MyShape {
//   def main(args: Array[String]) {
//     repeat(6) { forward(80); right(60) }
//   }
// }
// RIGHT — write drawing commands at the top level only.

--- END EXAMPLES ---

RULES:
- right() turns CLOCKWISE; left() turns COUNTER-CLOCKWISE.
- setHeading(0)=East, setHeading(90)=North(up), setHeading(180)=West, setHeading(270)=South.
- Use hop(n) or penUp()/penDown() only when repositioning between separate sub-shapes.
- NEVER wrap code in object/class/def main. Write drawing commands at the top level only.
"""

SYSTEM_PROMPT = (
    "You are a Kojo turtle graphics programmer.\n"
    "A student has described a shape they want drawn. Your job is to write Kojo code that draws it.\n"
    "The description may be simple or imprecise — interpret it as best you can geometrically.\n"
    "Output ONLY the drawing commands inside a ```scala ... ``` fence. Nothing else.\n"
    "Do NOT include cleari(), clear(), setSpeed(), invisible(), or any setup — just the drawing commands.\n\n"
    + KOJO_API_REF
    + "\n"
    + _KOJO_EXAMPLES
)

# Lines to strip from model output before wrapping in Picture{}
_STRIP_RE = re.compile(
    r'^[ \t]*(clear\(\)|cleari\(\)|setSpeed\([^)]*\)|invisible\(\)|setPenColor\([^)]*\))[ \t]*\n',
    re.MULTILINE,
)


def _wrap_in_picture(code: str) -> str:
    """Wrap model drawing commands in drawCentered(Picture{...})."""
    code = _STRIP_RE.sub('', code).strip()
    body = "\n".join("    " + l for l in code.splitlines())
    return f"cleari()\n\ndef shape = Picture {{\n{body}\n}}\n\ndrawCentered(shape)\n"


def _save_prompt(task_dir: Path, system_message: str, user_message: str) -> None:
    out = (
        "=== SYSTEM PROMPT ===\n"
        + system_message
        + "\n\n=== USER MESSAGE ===\n"
        + user_message
        + "\n"
    )
    (task_dir / "llm_prompt.txt").write_text(out, encoding="utf-8")


def run_task(task_id: int, model: LMStudioModel) -> dict:
    task_dir   = DATASET_DIR / f"Task{task_id}"
    query_path = task_dir / f"KojoQuery{task_id}.md"
    gt_path    = task_dir / "ground_truth_kojo.png"
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
        result["status"] = "no ground truth (run build_kojobench2.py first)"
        return result

    query_text = query_path.read_text(encoding="utf-8").strip()
    result["desc"] = query_text.splitlines()[0][:65]

    # ── Call the model ─────────────────────────────────────────────────────────
    _save_prompt(task_dir, SYSTEM_PROMPT, query_text)
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

    # ── Extract + wrap in drawCentered ─────────────────────────────────────────
    raw = preprocess_response(response)
    if not raw:
        print("no code extracted")
        result["status"] = "no code"
        return result

    code = _wrap_in_picture(raw)
    (task_dir / "llm_generated.kojo").write_text(code, encoding="utf-8")

    # ── Render (with compile-error retry) ─────────────────────────────────────
    MAX_RETRIES = 2
    ok, err = render(code, str(out_path))
    for attempt in range(MAX_RETRIES):
        if ok:
            break
        print(f"compile error (attempt {attempt + 1}), asking model to fix...", end=" ", flush=True)
        fix_prompt = (
            f"The following Kojo code produced a compiler error.\n\n"
            f"CODE:\n```scala\n{raw}\n```\n\n"
            f"ERROR:\n{err}\n\n"
            f"Fix the error. Output ONLY the corrected drawing commands inside a ```scala ... ``` fence."
        )
        try:
            response = model.get_response(system_message=SYSTEM_PROMPT, user_message=fix_prompt)
        except Exception as e:
            break
        fixed = preprocess_response(response)
        if not fixed:
            break
        raw  = fixed
        code = _wrap_in_picture(raw)
        (task_dir / "llm_generated.kojo").write_text(code, encoding="utf-8")
        ok, err = render(code, str(out_path))

    if not ok:
        short = err.splitlines()[0][:80] if err else "unknown"
        print(f"render failed: {short}")
        result["status"] = f"render failed: {short}"
        return result

    # ── Score ─────────────────────────────────────────────────────────────────
    score = nss_score(str(gt_path), str(out_path))
    result.update({"score": score, "status": "ok"})
    print(f"NSS={score*100:.1f}%")
    return result


# ── UI ────────────────────────────────────────────────────────────────────────

def show_ui(results: list[dict], model_name: str):
    import numpy as np
    from PIL import Image
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    ok_tasks = [r for r in results if r["status"] == "ok"]
    n   = len(results)
    avg = sum(r["score"] for r in ok_tasks) / len(ok_tasks) if ok_tasks else 0.0

    def score_color(s):
        if s >= 0.75: return "#2ecc71"
        if s >= 0.50: return "#f39c12"
        return "#e74c3c"

    fig = plt.figure(figsize=(15, 3.8 * n), facecolor="#1a1a2e")
    fig.canvas.manager.set_window_title(f"KojoBench2 — {model_name}")
    fig.suptitle(
        f"Model: {model_name}   |   Tasks: {n}   |   Avg NSS: {avg*100:.1f}%   "
        f"({len(ok_tasks)}/{n} rendered)",
        fontsize=13, color="white", y=1.001, fontweight="bold",
    )

    outer = gridspec.GridSpec(n, 1, figure=fig, hspace=0.6)

    for row, r in enumerate(results):
        inner = gridspec.GridSpecFromSubplotSpec(
            2, 3, subplot_spec=outer[row],
            width_ratios=[1, 1, 0.55], height_ratios=[0.18, 1],
            hspace=0.08, wspace=0.15,
        )
        ax_hdr = fig.add_subplot(inner[0, :])
        ax_hdr.set_facecolor("#16213e")
        ax_hdr.axis("off")
        color = score_color(r["score"])
        ax_hdr.text(0.01, 0.5, f"Task {r['id']}  —  {r['desc']}",
                    transform=ax_hdr.transAxes, fontsize=10, color="white",
                    va="center", ha="left")
        status_txt = (f"NSS: {r['score']*100:.1f}%" if r["status"] == "ok"
                      else f"[{r['status']}]")
        ax_hdr.text(0.99, 0.5, status_txt, transform=ax_hdr.transAxes,
                    fontsize=9,
                    color=color if r["status"] == "ok" else "#e74c3c",
                    va="center", ha="right", fontweight="bold")

        ax_gt = fig.add_subplot(inner[1, 0])
        ax_gt.imshow(np.array(Image.open(r["gt_path"]).convert("RGB")))
        ax_gt.set_title("Ground Truth", fontsize=8, color="#aaaaaa", pad=3)
        ax_gt.axis("off")

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
        description="Evaluate LM Studio model on KojoBench2 tasks."
    )
    parser.add_argument("--tasks", type=int, nargs="+", metavar="N",
                        default=list(range(1, 11)),
                        help="Task IDs to run (default: 1-10)")
    parser.add_argument("--no-ui", action="store_true",
                        help="Print table only, skip matplotlib window")
    args = parser.parse_args()

    model      = LMStudioModel()
    model_name = model.model

    print(f"\nKojoBench2 eval — model: {model_name}")
    print(f"Tasks: {args.tasks}\n")

    results = []
    for task_id in args.tasks:
        results.append(run_task(task_id, model))

    ok  = [r for r in results if r["status"] == "ok"]
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
