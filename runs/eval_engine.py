"""
Shared engine: rendering, NSS scoring, KCSS scoring, matplotlib UI window.
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.image as mpimg
import numpy as np

from utils.kojo_code_quality import analyze
from utils.shape_similarity   import nss_score
from utils.kojo_renderer      import render, code_to_image

# ── Read system prompt from eval pipeline ─────────────────────────────────────
_EVAL_PY = Path(__file__).parent.parent / "eval" / "eval_kojobench2.py"
_src = _EVAL_PY.read_text(encoding="utf-8")
_m   = re.search(r'SYSTEM_PROMPT\s*=\s*"""(.*?)"""', _src, re.DOTALL)
SYSTEM_PROMPT = _m.group(1).strip() if _m else ""

TASKS   = list(range(1, 76))
GT_DIR  = Path(__file__).parent.parent / "benchmark"

_FENCE_RE = re.compile(r'```(?:scala|kojo)?\s*(.*?)```', re.DOTALL)

def load_query(task_id: int) -> str:
    f = GT_DIR / f"Task{task_id}" / f"KojoQuery{task_id}.md"
    return f.read_text(encoding="utf-8").strip()

def extract_code(text: str) -> str:
    m = _FENCE_RE.search(text)
    return m.group(1).strip() if m else ""

_STRIP_RE = re.compile(r'^\s*(//.*|clear[i]?\(.*\)|setSpeed\(.*\)|setPenColor\(.*\)|setBackground\(.*\))\s*$', re.MULTILINE)

def render_code(task_id: int, code: str, out_dir: Path) -> Path | None:
    """Render kojo code to PNG using drawCentered Picture wrapper."""
    if not code.strip():
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    out_png = out_dir / f"task{task_id}.png"
    try:
        if "drawCentered" in code:
            final = code
        else:
            # Strip comments and canvas-level commands before wrapping
            inner = _STRIP_RE.sub("", code).strip()
            body  = "\n".join("  " + l for l in inner.splitlines())
            final = f"cleari()\n\ndef shape = Picture {{\n{body}\n}}\n\ndrawCentered(shape)\n"
        ok, err = render(final, str(out_png))
        if not ok:
            print(f"    [render] task {task_id} failed: {err[:120]}")
        return out_png if ok else None
    except Exception as e:
        print(f"    [render] task {task_id} exception: {e}")
        return None

def score_task(task_id: int, code: str, rendered_png: Path | None = None) -> dict:
    gt_file = GT_DIR / f"Task{task_id}" / f"KojoTask{task_id}.kojo"
    gt_png  = GT_DIR / f"Task{task_id}" / "ground_truth_kojo.png"
    gt_code = gt_file.read_text(encoding="utf-8") if gt_file.exists() else None

    r = analyze(code, gt_code)

    nss = None
    if rendered_png and rendered_png.exists() and gt_png.exists():
        try:
            nss = nss_score(str(gt_png), str(rendered_png))
        except Exception as e:
            print(f"    [nss] task {task_id} failed: {e}")

    return {
        "task":       task_id,
        "query":      load_query(task_id),
        "kcss":       r.score,
        "structure":  r.metrics["structure_score"],
        "idiom":      r.metrics["idiom_score"],
        "simplicity": r.metrics["simplicity_score"],
        "bloat":      r.metrics["bloat_ratio"],
        "lines":      r.metrics["llm_lines"],
        "forbidden":  r.forbidden,
        "warnings":   r.warnings,
        "idioms":     r.idioms,
        "nss":        nss,
        "code":       code,
        "rendered":   rendered_png,
        "gt_png":     gt_png if gt_png.exists() else None,
    }


def show_window(model_name: str, results: list, accent: str = "#4fc3f7"):
    avg_kcss = np.mean([r["kcss"] for r in results])
    nss_vals = [r["nss"] for r in results if r["nss"] is not None]
    avg_nss  = np.mean(nss_vals) if nss_vals else None

    fig = plt.figure(figsize=(18, 11), num=f"{model_name}")
    fig.patch.set_facecolor("#0d0d0d")

    # ── Header ────────────────────────────────────────────────────────────────
    fig.text(0.5, 0.975, model_name,
             ha="center", va="top", fontsize=14, fontweight="bold", color="white")
    sub = f"KCSS avg {avg_kcss*100:.0f}%"
    if avg_nss is not None:
        sub += f"   |   NSS avg {avg_nss*100:.1f}%"
    sub += "   |   Input: system prompt + query only — no GT code seen"
    fig.text(0.5, 0.950, sub, ha="center", va="top", fontsize=9, color="#888")

    # ── Image strip: GT vs rendered (top row) ─────────────────────────────────
    n = len(results)
    img_h = 0.12
    img_y = 0.80

    for i, r in enumerate(results):
        x = 0.01 + i * (0.98 / n)
        w = (0.98 / n) - 0.005

        # GT image
        ax_gt = fig.add_axes([x, img_y + img_h * 0.52, w, img_h * 0.46])
        ax_gt.axis("off")
        if r["gt_png"]:
            try:
                ax_gt.imshow(mpimg.imread(str(r["gt_png"])))
            except Exception:
                ax_gt.set_facecolor("#1a1a1a")
        ax_gt.set_title(f"T{r['task']}", color="#888", fontsize=7, pad=1)

        # Rendered image
        ax_llm = fig.add_axes([x, img_y, w, img_h * 0.48])
        ax_llm.axis("off")
        if r["rendered"] and Path(r["rendered"]).exists():
            try:
                ax_llm.imshow(mpimg.imread(str(r["rendered"])))
            except Exception:
                ax_llm.set_facecolor("#1a1a1a")
                ax_llm.text(0.5, 0.5, "err", ha="center", va="center",
                            color="#555", fontsize=6, transform=ax_llm.transAxes)
        else:
            ax_llm.set_facecolor("#111")
            ax_llm.text(0.5, 0.5, "no render", ha="center", va="center",
                        color="#444", fontsize=6, transform=ax_llm.transAxes)

    # ── Bar chart ─────────────────────────────────────────────────────────────
    bar_ax = fig.add_axes([0.06, 0.44, 0.90, 0.33])
    bar_ax.set_facecolor("#181818")

    x  = np.arange(n)
    w  = 0.16

    bar_ax.bar(x - 2*w, [r["structure"]   for r in results], w, label="Structure (40%)",  color="#4fc3f7", alpha=0.85)
    bar_ax.bar(x - 1*w, [r["idiom"]       for r in results], w, label="Idiom (30%)",      color="#81c784", alpha=0.85)
    bar_ax.bar(x + 0*w, [r["simplicity"]  for r in results], w, label="Simplicity (30%)", color="#ffb74d", alpha=0.85)
    bar_ax.bar(x + 1*w, [r["kcss"]        for r in results], w, label="KCSS",             color=accent,    alpha=0.95)
    if nss_vals:
        bar_ax.bar(x + 2*w, [r["nss"] if r["nss"] is not None else 0 for r in results],
                   w, label="NSS (image)", color="#f06292", alpha=0.85)

    bar_ax.axhline(avg_kcss, color=accent, linestyle="--", linewidth=1, alpha=0.7)
    bar_ax.text(n - 0.4, avg_kcss + 0.025, f"KCSS {avg_kcss*100:.0f}%",
                color=accent, fontsize=8)

    bar_ax.set_ylim(0, 1.2)
    bar_ax.set_xticks(x)
    bar_ax.set_xticklabels([f"T{r['task']}" for r in results], color="white", fontsize=10)
    bar_ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    bar_ax.set_yticklabels(["0%","25%","50%","75%","100%"], color="white", fontsize=8)
    bar_ax.tick_params(colors="white")
    bar_ax.spines[:].set_color("#2a2a2a")
    bar_ax.legend(loc="upper left", facecolor="#1e1e1e", labelcolor="white",
                  edgecolor="#333", fontsize=8, ncol=3)
    bar_ax.set_title("Sub-scores per task", color="white", fontsize=10, pad=5)

    # ── Detail table ──────────────────────────────────────────────────────────
    tbl = fig.add_axes([0.01, 0.01, 0.98, 0.40])
    tbl.set_facecolor("#141414")
    tbl.axis("off")

    cols  = ["T", "Query", "KCSS", "NSS", "Struct", "Idiom", "Simpl", "Bloat", "Lines", "Flags"]
    xpos  = [0.00, 0.04,   0.36,  0.42,  0.48,    0.54,   0.60,   0.66,   0.72,  0.77]
    row_h = 1.0 / (n + 1.5)
    hy    = 0.97

    def txt(ax, x, y, s, color="white", bold=False, size=8):
        ax.text(x + 0.004, y, s, transform=ax.transAxes,
                fontsize=size, color=color,
                fontweight="bold" if bold else "normal",
                va="top", clip_on=True)

    for lbl, xp in zip(cols, xpos):
        txt(tbl, xp, hy, lbl, color="#aaa", bold=True)

    for i, r in enumerate(results):
        y  = hy - row_h * (i + 1)
        bg = "#1a1a1a" if i % 2 == 0 else "#202020"
        tbl.add_patch(mpatches.FancyBboxPatch(
            (0, y - row_h*0.85), 1.0, row_h*0.82,
            boxstyle="round,pad=0.003",
            facecolor=bg, edgecolor="none",
            transform=tbl.transAxes, clip_on=False))

        kc = r["kcss"]
        kc_col = "#81c784" if kc >= 0.8 else ("#ffb74d" if kc >= 0.6 else "#ef5350")
        nss_str = f"{r['nss']*100:.0f}%" if r["nss"] is not None else "-"
        nss_col = ("#81c784" if r["nss"] and r["nss"] >= 0.6 else
                   "#ffb74d" if r["nss"] and r["nss"] >= 0.35 else
                   "#ef5350" if r["nss"] is not None else "#555")

        flags = []
        if r["forbidden"]: flags.append("! " + ", ".join(r["forbidden"]))
        if r["warnings"]:  flags.append("~ " + "; ".join(w.split("(")[0].strip() for w in r["warnings"]))
        if r["idioms"]:    flags.append("+ " + ", ".join(r["idioms"]))
        flag_str = "  ".join(flags)[:52] if flags else "-"

        row = [
            (f"T{r['task']}",                                              "white",   False),
            (r["query"][:36] + ("..." if len(r["query"]) > 36 else ""),   "#bbb",    False),
            (f"{kc*100:.0f}%",                                             kc_col,    True),
            (nss_str,                                                      nss_col,   True),
            (f"{r['structure']:.2f}",                                      "white",   False),
            (f"{r['idiom']:.2f}",                                          "white",   False),
            (f"{r['simplicity']:.2f}",                                     "white",   False),
            (f"{r['bloat']:.1f}x", "#ffb74d" if r["bloat"] > 2 else "w",  False),
            (str(r["lines"]),                                               "white",   False),
            (flag_str,                                                      "#999",    False),
        ]
        # fix color ref
        row[7] = (row[7][0], "#ffb74d" if r["bloat"] > 2 else "white", False)

        for (s, col, bold), xp in zip(row, xpos):
            txt(tbl, xp, y, s, color=col, bold=bold)

    tbl.set_title("Detailed Results", color="white", fontsize=10, pad=4, loc="left")
    plt.show(block=True)
