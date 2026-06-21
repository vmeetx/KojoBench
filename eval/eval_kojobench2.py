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


def run_task(task_id: int, model) -> dict:
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


# ── Results window ────────────────────────────────────────────────────────────

def show_ui(results: list[dict], model_name: str) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.gridspec import GridSpec

    BG      = "#0d0d0d"
    PANEL   = "#1a1a1a"
    WHITE   = "#f0f0f0"
    DIM     = "#555555"
    DIMMER  = "#2a2a2a"
    ACCENT  = "#ffffff"
    BAR_FG  = "#e0e0e0"
    BAR_BG  = "#2e2e2e"

    ok      = [r for r in results if r["status"] == "ok"]
    avg_nss = sum(r["score"] for r in ok) / len(ok) if ok else 0.0
    kcss_ok = [r for r in ok if r["kcss"]]
    avg_kcs = sum(r["kcss"].score for r in kcss_ok) / len(kcss_ok) if kcss_ok else 0.0
    n       = len(results)

    ROW_H   = 0.44        # inches per task row
    HDR_H   = 1.1         # header panel height
    COL_H   = 0.32        # column header strip
    FOOT_H  = 0.55        # footer / averages strip
    FIG_H   = HDR_H + COL_H + n * ROW_H + FOOT_H + 0.2
    FIG_W   = 13.0

    fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG)
    fig.canvas.manager.set_window_title("KojoBench2 Results")

    # ── absolute axes helper ───────────────────────────────────────────────────
    def ax_abs(left, bottom, width, height, bg=BG):
        a = fig.add_axes([left / FIG_W, bottom / FIG_H, width / FIG_W, height / FIG_H])
        a.set_facecolor(bg)
        a.set_xlim(0, 1); a.set_ylim(0, 1)
        a.axis("off")
        return a

    PAD = 0.22   # outer margin inches

    # ── header ────────────────────────────────────────────────────────────────
    ax_h = ax_abs(PAD, FIG_H - HDR_H, FIG_W - 2*PAD, HDR_H - 0.12, bg=BG)
    ax_h.text(0, 0.82, "KojoBench2", fontsize=22, color=ACCENT,
              fontweight="bold", va="top", fontfamily="monospace")
    ax_h.text(0, 0.46, model_name, fontsize=11, color=DIM,
              va="top", fontfamily="monospace")

    stats = [
        ("NSS",    f"{avg_nss*100:.1f}%"),
        ("KCSS",   f"{avg_kcs*100:.1f}%"),
        ("TASKS",  f"{len(ok)}/{n}"),
    ]
    for i, (label, val) in enumerate(stats):
        x = 0.52 + i * 0.165
        ax_h.text(x, 0.80, val,   fontsize=20, color=ACCENT, fontweight="bold",
                  va="top", ha="center", fontfamily="monospace")
        ax_h.text(x, 0.38, label, fontsize=7,  color=DIM,
                  va="top", ha="center", fontfamily="monospace", letterspacing=2)

    # separator line under header
    ax_h.axhline(0.02, color=DIM, linewidth=0.5)

    # ── column headers ─────────────────────────────────────────────────────────
    body_top = FIG_H - HDR_H
    ax_c = ax_abs(PAD, body_top - COL_H, FIG_W - 2*PAD, COL_H - 0.04, bg=BG)
    cols = [("#",0.012), ("DESCRIPTION",0.055), ("NSS",0.42), ("KCSS",0.64), ("BLOAT",0.84), ("FLAGS",0.90)]
    for label, x in cols:
        ax_c.text(x, 0.35, label, fontsize=6.5, color=DIM,
                  va="center", fontfamily="monospace", fontweight="bold", letterspacing=1)
    ax_c.axhline(0.0, color=DIMMER, linewidth=0.5)

    # ── task rows ─────────────────────────────────────────────────────────────
    rows_top = body_top - COL_H
    for idx, r in enumerate(results):
        y0     = rows_top - (idx + 1) * ROW_H
        bg_row = DIMMER if idx % 2 == 0 else BG
        ax_r   = ax_abs(PAD, y0, FIG_W - 2*PAD, ROW_H - 0.03, bg=bg_row)

        ax_r.text(0.012, 0.5, str(r["id"]), fontsize=8, color=DIM,
                  va="center", fontfamily="monospace")

        desc = (r["desc"][:42] + "…") if len(r["desc"]) > 42 else r["desc"]
        ax_r.text(0.055, 0.5, desc, fontsize=7.5, color=WHITE,
                  va="center", fontfamily="monospace")

        if r["status"] == "ok":
            nss = r["score"]
            q   = r["kcss"]
            kcs = q.score if q else 0.0

            # NSS bar
            ax_r.barh(0.5, 0.18,  height=0.38, left=0.42, color=BAR_BG)
            ax_r.barh(0.5, nss*0.18, height=0.38, left=0.42, color=BAR_FG)
            ax_r.text(0.615, 0.5, f"{nss*100:.0f}%", fontsize=7.5, color=ACCENT,
                      va="center", fontfamily="monospace")

            # KCSS bar
            ax_r.barh(0.5, 0.18,  height=0.38, left=0.64, color=BAR_BG)
            ax_r.barh(0.5, kcs*0.18, height=0.38, left=0.64, color=BAR_FG)
            ax_r.text(0.835, 0.5, f"{kcs*100:.0f}%", fontsize=7.5, color=ACCENT,
                      va="center", fontfamily="monospace")

            bloat = f"{q.metrics['bloat_ratio']:.1f}x" if q else "─"
            ax_r.text(0.84, 0.5, bloat, fontsize=7.5, color=DIM,
                      va="center", fontfamily="monospace")

            flags = ",".join((q.forbidden + q.warnings))[:22] if q else ""
            ax_r.text(0.90, 0.5, flags, fontsize=6.5, color=DIM,
                      va="center", fontfamily="monospace")
        else:
            ax_r.text(0.42, 0.5, r["status"], fontsize=7, color=DIM,
                      va="center", fontfamily="monospace", style="italic")

        ax_r.axhline(0.0, color=DIM, linewidth=0.3, alpha=0.4)

    # ── footer / averages ─────────────────────────────────────────────────────
    foot_y = rows_top - n * ROW_H
    ax_f   = ax_abs(PAD, foot_y - FOOT_H, FIG_W - 2*PAD, FOOT_H - 0.05, bg=PANEL)
    ax_f.axhline(1.0, color=DIM, linewidth=0.5)

    ax_f.text(0.012, 0.5, "AVG", fontsize=8, color=DIM,
              va="center", fontfamily="monospace", fontweight="bold")

    ax_f.barh(0.5, 0.18,        height=0.38, left=0.42, color=BAR_BG)
    ax_f.barh(0.5, avg_nss*0.18, height=0.38, left=0.42, color=ACCENT)
    ax_f.text(0.615, 0.5, f"{avg_nss*100:.1f}%", fontsize=8, color=ACCENT,
              va="center", fontfamily="monospace", fontweight="bold")

    ax_f.barh(0.5, 0.18,        height=0.38, left=0.64, color=BAR_BG)
    ax_f.barh(0.5, avg_kcs*0.18, height=0.38, left=0.64, color=ACCENT)
    ax_f.text(0.835, 0.5, f"{avg_kcs*100:.1f}%", fontsize=8, color=ACCENT,
              va="center", fontfamily="monospace", fontweight="bold")

    plt.show()


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate a model on KojoBench2 tasks."
    )
    parser.add_argument("--tasks", type=int, nargs="+", metavar="N",
                        default=list(range(1, 26)),
                        help="Task IDs to run (default: 1-25)")
    parser.add_argument("--provider", default=None,
                        help="Provider preset: lmstudio, groq, together, openrouter, fireworks")
    parser.add_argument("--base-url", default=None,
                        help="Override provider base URL")
    parser.add_argument("--api-key", default=None,
                        help="Override API key")
    parser.add_argument("--model-name", default=None,
                        help="Model identifier")
    args = parser.parse_args()

    from models.openai_compat import OpenAICompatModel
    model = OpenAICompatModel(
        provider=args.provider,
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model_name,
    )
    model_name = model.model

    print(f"\nKojoBench2 eval — model: {model_name}")
    print(f"Tasks: {args.tasks}\n")

    results = []
    for task_id in args.tasks:
        results.append(run_task(task_id, model))

    show_ui(results, model_name)


if __name__ == "__main__":
    main()
