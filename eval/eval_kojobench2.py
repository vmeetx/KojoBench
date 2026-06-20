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
from utils.kojo_code_quality import analyze as kcss_analyze

BASE        = Path(__file__).parent.parent
DATASET_DIR = BASE / "KojoBench2"

SYSTEM_PROMPT = """\
You are a Kojo turtle graphics programmer.
When the user asks you to draw something, your task is to write Kojo code that can draw that thing when it is run.
Write Kojo code that draws exactly what the shape/drawing description from the user asks for.

For every drawing request, first produce a concise `<geometry>` section, then produce the Kojo code.

The `<geometry>` section should be a practical construction plan, not a private reasoning trace. Keep it short and concrete: describe the main shapes, approximate sizes, positions, and drawing order. Do not include trial-and-error, hidden thoughts, or long explanations.

If the description is underspecified, choose simple reasonable proportions. Prefer drawing from the turtle's default starting configuration: position (0,0), heading North. When practical, treat (0,0) as the lower-left or starting anchor of the drawing, so the drawing mostly stays in the top-right quadrant. Use the relative movement commands of the turtle, unless especially asked to use the absolute/global movement commands. If you need to change the turtle's initial orientation before it starts moving or drawing, use right(...) or left(...) instead of setHeading(...). Keep the drawing within about a 500x500 pixel area unless the user asks otherwise.

Output ONLY these two parts:

1. A `<geometry> ... </geometry>` section.
2. The Kojo code inside a ```scala ... ```  fence.

Do not output anything else.

--- KOJO API QUICK REFERENCE ---
The code must be written in Kojo (a Scala-based turtle graphics environment).
Do NOT use Python Turtle. Do NOT use any import statements. Kojo's built-ins
are always in scope.

The turtle starts out with position (0, 0) and heading 90 degrees (pointing up).

Unless the user explicitly asks to continue an existing drawing, start the code with:
clear()
setSpeed(fast)

Use top-level statements only. Do NOT use classes, objects, packages, imports, or a main method.
Do NOT use unavailable commands such as goto, circle, begin_fill, end_fill, fd, bk, rt, lt, speed, color, or fill.

Relative Movement:
forward(n)           — move forward n pixels in the direction of its nose, drawing a line if pen is down
back(n)              — move backward n pixels
right(angle)         — turn nose right by angle degrees (no movement)
left(angle)          — turn nose left by angle degrees (no movement)
right(angle, radius) — move along a right arc of given radius and angle
left(angle, radius)  — move along a left arc of given radius and angle
hop(n)               — move forward n pixels WITHOUT drawing; pen goes down after

Global/Absolute Movement:
setPosition(x, y)    — teleport to (x, y)
lineTo(x, y)         — draw a line to (x, y) from current position
setHeading(angle)    — point turtle in direction `angle` (0=East, 90=North, 180=West, 270=South)

Pen / appearance:
penUp()              — lift pen (stop drawing)
penDown()            — lower pen (resume drawing)
setPenColor(color)   — set line colour; e.g. setPenColor(blue), setPenColor(cm.rgb(255,0,0))
setFillColor(color)  — set fill colour for enclosed areas
setPenThickness(n)   — set line width in pixels
setBackground(color) — paint canvas background

Colors:
Named:  red, blue, green, yellow, orange, purple, pink, black, white,
        cyan, magenta, brown, gray, darkGray, lightGray, etc.
RGB:    cm.rgb(r, g, b)          — e.g. cm.rgb(255, 128, 0)
RGBA:   cm.rgba(r, g, b, alpha)  — alpha 0-255
HSL:    cm.hsl(hue, sat, light)  — hue 0-360, sat and light 0.0-1.0
HSLA:   cm.hsla(h, s, l, a)      — a is 0.0-1.0
noColor                          — transparent / no fill

Control:
repeat(n) { ... }                      — repeat a block n times
repeatFor(a to b) { i => ... }         — loop with counter i from a to b (inclusive)
repeatFor(a until b) { i => ... }      — exclusive upper bound
def name() { ... }                     — define a parameterless command
def name(x: Int) { ... }               — define a command with an Int parameter
def name(x: Double) { ... }            — define a command with a Double parameter
val x = expr                           — immutable binding
var x = expr                           — mutable variable
x = newValue                           — reassign a var

Canvas:
clear()      — reset canvas and turtle state (position→(0,0), heading→90°, pen down)
cleari()     — clear() and also hide the turtle
invisible()  — hide the turtle
visible()    — show the turtle
setSpeed(slow|medium|fast|superFast)   — animation speed

State save/restore:
savePosHe()    — save current position and heading
restorePosHe() — restore to saved position and heading

Example — equilateral triangle with side 100:
clear()
setSpeed(fast)

repeat(3) {
  forward(100)
  right(120)
}

Example — square with fill:
clear()
setSpeed(fast)

setFillColor(blue)
repeat(4) {
  forward(100)
  right(90)
}
setFillColor(noColor)

Example — circle with radius 50:
clear()
setSpeed(fast)

right(360, 50) // on right of turtle starting position/orientation

Note -- Use left(360, 50) if the circle should be on the left side of the turtle.

Example — arc (quarter circle, radius 100, rightward):
right(90, 100)

IMPORTANT: Output ONLY the `<geometry>` section followed by Kojo code inside a ```scala ... ``` fence.
Do NOT wrap in a main() or object. Write top-level statements only.
--- END KOJO API ---

--- MORE KOJO CODE EXAMPLES ---
These are real working Kojo scripts. Study the style: short, direct, no classes,
no imports, no main method. Use `def` only when you genuinely reuse a command.

Example A — regular hexagon, side 80:
clear()
setSpeed(fast)

repeat(6) {
  forward(80)
  right(60)
}

Example B — reusable polygon helper:
Note: use 360.0 (Double) so division is never truncated
clear()
setSpeed(fast)

def drawPolygon(sides: Int, length: Double) {
  val turn = 360.0 / sides
  repeat(sides) {
    forward(length)
    right(turn)
  }
}
drawPolygon(8, 60)   // octagon, side 60

WRONG — never wrap code like this:
object MyShape {
  def main(args: Array[String]) {
    repeat(6) { forward(80); right(60) }
   }
}

RIGHT — write drawing commands at the top level only:
repeat(6) {
  forward(80)
  right(60)
}

--- END EXAMPLES ---

--- RESPONSE FORMAT ---
<geometry>
Goal: ...
Canvas/scale: ...
Main shapes:
- ...
Drawing order:
1. ...
2. ...
3. ...
</geometry>

```scala
clear()
setSpeed(fast)

// Kojo code here
```
--- END RESPONSE FORMAT ---\
"""

# Lines to strip from model output before wrapping in Picture{}
_STRIP_RE = re.compile(
    r'^[ \t]*(clear\(\)|cleari\(\)|setSpeed\([^)]*\)|invisible\(\))[ \t]*\n',
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
        "kcss":     None,
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

    # ── Save full response (reasoning trace + raw output) ─────────────────────
    (task_dir / "llm_response.txt").write_text(response, encoding="utf-8")

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

    # ── Image score (NSS) ─────────────────────────────────────────────────────
    score = nss_score(str(gt_path), str(out_path))

    # ── Code quality score (KCSS) ─────────────────────────────────────────────
    gt_kojo_path = task_dir / f"KojoTask{task_id}.kojo"
    gt_code = gt_kojo_path.read_text(encoding="utf-8") if gt_kojo_path.exists() else None
    kcss = kcss_analyze(raw, gt_code)

    result.update({"score": score, "kcss": kcss, "status": "ok"})
    print(f"NSS={score*100:.1f}%  {kcss.one_line()}")
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
            # NSS bar (top)
            y_nss = 0.65
            ax_bar.barh(y_nss, r["score"], height=0.22, color=color, alpha=0.85)
            ax_bar.barh(y_nss, 1.0, height=0.22, color="#ffffff", alpha=0.06)
            ax_bar.text(-0.02, y_nss, "NSS", fontsize=7, color="white",
                        va="center", ha="right")
            ax_bar.text(r["score"] + 0.02, y_nss, f"{r['score']*100:.0f}%",
                        fontsize=8, color=color, va="center", ha="left", fontweight="bold")
            # KCSS bar (bottom)
            q = r.get("kcss")
            if q:
                ks = q.score
                kc = score_color(ks)
                y_kcss = 0.30
                ax_bar.barh(y_kcss, ks, height=0.22, color=kc, alpha=0.70)
                ax_bar.barh(y_kcss, 1.0, height=0.22, color="#ffffff", alpha=0.06)
                ax_bar.text(-0.02, y_kcss, "KCSS", fontsize=7, color="white",
                            va="center", ha="right")
                ax_bar.text(ks + 0.02, y_kcss, f"{ks*100:.0f}%",
                            fontsize=8, color=kc, va="center", ha="left", fontweight="bold")
                # Flag markers below the bars
                flag_txt = " ".join(
                    ["✗" + f for f in q.forbidden[:2]] +
                    ["△" + w.split("(")[0].strip() for w in q.warnings[:1]]
                )
                if flag_txt:
                    ax_bar.text(0.5, 0.05, flag_txt, fontsize=6, color="#e74c3c",
                                va="bottom", ha="center", transform=ax_bar.transAxes)
            ax_bar.set_xlim(0, 1.35)
            ax_bar.set_ylim(0, 1.0)

    plt.tight_layout()
    plt.show()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate a model on KojoBench2 tasks."
    )
    parser.add_argument("--tasks", type=int, nargs="+", metavar="N",
                        default=list(range(1, 26)),
                        help="Task IDs to run (default: 1-25)")
    parser.add_argument("--no-ui", action="store_true",
                        help="Print table only, skip matplotlib window")
    parser.add_argument("--model-backend", choices=["lmstudio", "hf"], default="lmstudio",
                        help="Model backend: lmstudio (default) or hf (HF Inference API)")
    args = parser.parse_args()

    if args.model_backend == "hf":
        from models.hf_api import HFApiModel
        model = HFApiModel()
    else:
        from models.lm_studio import LMStudioModel
        model = LMStudioModel()
    model_name = model.model

    print(f"\nKojoBench2 eval — model: {model_name}")
    print(f"Tasks: {args.tasks}\n")

    results = []
    for task_id in args.tasks:
        results.append(run_task(task_id, model))

    ok  = [r for r in results if r["status"] == "ok"]
    avg = sum(r["score"] for r in ok) / len(ok) if ok else 0.0

    print(f"\n{'Task':<6} {'NSS':>7}  {'KCSS':>6}  {'Bloat':>6}  {'Flags':<30}  Description")
    print("-" * 90)
    for r in results:
        if r["status"] == "ok":
            q     = r["kcss"]
            flags = ",".join(q.forbidden + q.warnings)[:28] if q else ""
            bloat = f"{q.metrics['bloat_ratio']:.1f}x" if q else "---"
            kcss_pct = f"{q.score*100:.0f}%" if q else "---"
            print(f"  {r['id']:<4} {r['score']*100:>6.1f}%  {kcss_pct:>6}  {bloat:>6}  {flags:<30}  {r['desc']}")
        else:
            print(f"  {r['id']:<4} {'---':>6}   {'---':>6}  {'---':>6}  [{r['status']}]")
    print("-" * 90)
    kcss_ok  = [r for r in ok if r["kcss"]]
    avg_kcss = sum(r["kcss"].score for r in kcss_ok) / len(kcss_ok) if kcss_ok else 0.0
    print(f"  {'AVG':<4} {avg*100:>6.1f}%  {avg_kcss*100:>5.0f}%   ({len(ok)}/{len(results)} rendered)\n")

    if not args.no_ui:
        show_ui(results, model_name)


if __name__ == "__main__":
    main()
