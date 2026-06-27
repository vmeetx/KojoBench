"""
Compact score-only report for Qwen: NSS section then KCSS section, no images.
"""
import sys
from pathlib import Path

BASE         = Path(__file__).parent.parent
GT_DIR       = BASE / "benchmark"
QWEN_DIR     = Path(__file__).parent / "qwen_rendered"
OUT_HTML     = Path(__file__).parent / "report_qwen_compact.html"
_DROP_TASKS  = {1, 16, 50, 60}
TASKS        = [t for t in range(1, 76) if t not in _DROP_TASKS]
MATCH_THRESH = 0.65

sys.path.insert(0, str(BASE))

def query(task_id):
    f = GT_DIR / f"Task{task_id}" / f"KojoQuery{task_id}.md"
    if not f.exists():
        return f"Task {task_id}"
    t = f.read_text(encoding="utf-8").strip()
    return t[:80] + ("..." if len(t) > 80 else "")

def compute_nss(task_id):
    try:
        from utils.shape_similarity import nss_score
        gt  = GT_DIR / f"Task{task_id}" / "ground_truth_kojo.png"
        qw  = QWEN_DIR / f"task{task_id}.png"
        if not gt.exists() or not qw.exists():
            return None
        return nss_score(str(gt), str(qw))
    except Exception:
        return None

def compute_kcss(task_id):
    try:
        from utils.kojo_code_quality import analyze
        kojo_f = QWEN_DIR / f"task{task_id}.kojo"
        gt_f   = GT_DIR / f"Task{task_id}" / f"KojoTask{task_id}.kojo"
        if not kojo_f.exists():
            return None, None, None, None
        code    = kojo_f.read_text(encoding="utf-8")
        gt_code = gt_f.read_text(encoding="utf-8") if gt_f.exists() else None
        r = analyze(code, gt_code)
        return r.score, r.metrics["structure_score"], r.metrics["idiom_score"], r.metrics["simplicity_score"]
    except Exception:
        return None, None, None, None

rows = []
for t in TASKS:
    nss = compute_nss(t)
    kcss, struct, idiom, simpl = compute_kcss(t)
    rows.append({
        "task":   t,
        "query":  query(t),
        "nss":    nss,
        "kcss":   kcss,
        "struct": struct,
        "idiom":  idiom,
        "simpl":  simpl,
        "match":  nss is not None and nss >= MATCH_THRESH,
    })
    print(f"  T{t}: NSS={nss*100:.0f}% KCSS={kcss*100:.0f}%" if (nss and kcss) else f"  T{t}: ?")

def col(v):
    if v is None: return "#444"
    if v >= 0.75: return "#22c55e"
    if v >= 0.50: return "#f59e0b"
    if v >= 0.25: return "#ef4444"
    return "#7f1d1d"

def pct(v):
    return f"{v*100:.0f}%" if v is not None else "?"

def bar(v, color):
    w = f"{v*100:.0f}" if v is not None else "0"
    return f'<div class="bar-bg"><div class="bar-fill" style="width:{w}%;background:{color}"></div></div>'

# Sort for each section
nss_sorted  = sorted(rows, key=lambda r: r["nss"]  if r["nss"]  is not None else -1, reverse=True)
kcss_sorted = sorted(rows, key=lambda r: r["kcss"] if r["kcss"] is not None else -1, reverse=True)

def nss_row(r):
    nc    = col(r["nss"])
    badge = f'<span class="yes">YES</span>' if r["match"] else f'<span class="no">NO</span>'
    return f"""<div class="row">
  <span class="tid">T{r['task']}</span>
  {badge}
  {bar(r['nss'], nc)}
  <span class="val" style="color:{nc}">{pct(r['nss'])}</span>
  <span class="qtxt">{r['query']}</span>
</div>"""

def kcss_row(r):
    kc  = col(r["kcss"])
    sc  = col(r["struct"])
    ic  = col(r["idiom"])
    sic = col(r["simpl"])
    return f"""<div class="krow">
  <div class="krow-top">
    <span class="tid">T{r['task']}</span>
    {bar(r['kcss'], kc)}
    <span class="val" style="color:{kc}">{pct(r['kcss'])}</span>
    <span class="qtxt">{r['query']}</span>
  </div>
  <div class="krow-sub">
    <span class="sub-lbl">Structure</span>{bar(r['struct'], sc)}<span class="sub-val" style="color:{sc}">{pct(r['struct'])}</span>
    <span class="sub-lbl">Idioms</span>{bar(r['idiom'],  ic)}<span class="sub-val" style="color:{ic}">{pct(r['idiom'])}</span>
    <span class="sub-lbl">Simplicity</span>{bar(r['simpl'], sic)}<span class="sub-val" style="color:{sic}">{pct(r['simpl'])}</span>
  </div>
</div>"""

nss_vals  = [r["nss"]  for r in rows if r["nss"]  is not None]
kcss_vals = [r["kcss"] for r in rows if r["kcss"] is not None]
avg_nss   = sum(nss_vals)  / len(nss_vals)  * 100 if nss_vals  else 0
avg_kcss  = sum(kcss_vals) / len(kcss_vals) * 100 if kcss_vals else 0
yes_count = sum(1 for r in rows if r["match"])

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Qwen — Compact Score Report</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background:#111; color:#ddd; font-family:system-ui,sans-serif; padding:20px; font-size:13px; }}
  h1 {{ font-size:1.3rem; color:#fff; text-align:center; margin-bottom:4px; }}
  .sub {{ text-align:center; color:#666; font-size:0.75rem; margin-bottom:18px; }}
  .stats {{ display:flex; gap:16px; justify-content:center; margin-bottom:24px; flex-wrap:wrap; }}
  .stat {{ background:#1a1a1a; border:1px solid #2a2a2a; border-radius:8px; padding:8px 18px; text-align:center; }}
  .stat-v {{ font-size:1.2rem; font-weight:700; }}
  .stat-l {{ font-size:0.65rem; color:#555; text-transform:uppercase; letter-spacing:.05em; margin-top:2px; }}
  .section {{ margin-bottom:28px; }}
  .section-title {{ font-size:0.8rem; font-weight:700; text-transform:uppercase;
                    letter-spacing:.08em; color:#888; border-bottom:1px solid #222;
                    padding-bottom:6px; margin-bottom:10px; }}
  .row {{ display:grid; grid-template-columns:32px 36px 120px 36px 1fr; align-items:center;
          gap:6px; padding:3px 4px; border-radius:4px; }}
  .row:hover {{ background:#1a1a1a; }}
  .row.has-sub {{ grid-template-columns:32px 120px 36px 1fr 1fr; }}
  .tid {{ font-weight:700; color:#888; font-size:0.72rem; }}
  .yes {{ background:#14532d; color:#4ade80; font-size:0.6rem; font-weight:800;
          padding:2px 5px; border-radius:3px; text-align:center; }}
  .no  {{ background:#3f0f0f; color:#f87171; font-size:0.6rem; font-weight:800;
          padding:2px 5px; border-radius:3px; text-align:center; }}
  .val {{ font-size:0.75rem; font-weight:700; text-align:right; white-space:nowrap; }}
  .bar-bg {{ background:#2a2a2a; border-radius:2px; height:6px; overflow:hidden; }}
  .bar-fill {{ height:100%; border-radius:2px; }}
  .qtxt {{ font-size:0.65rem; color:#555; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .sub-lbl {{ font-size:0.6rem; color:#555; white-space:nowrap; }}
  .sub-val {{ font-size:0.6rem; font-weight:600; white-space:nowrap; }}
  .krow {{ padding:4px 4px 2px; border-radius:4px; margin-bottom:2px; }}
  .krow:hover {{ background:#1a1a1a; }}
  .krow-top {{ display:grid; grid-template-columns:32px 140px 36px 1fr;
               align-items:center; gap:6px; }}
  .krow-sub {{ display:grid; grid-template-columns:32px 55px 140px 28px 55px 140px 28px 55px 140px 28px;
               align-items:center; gap:4px; margin-top:3px; padding-left:2px; }}
  .nav {{ display:flex; justify-content:center; gap:12px; margin-bottom:20px; }}
  .nav a {{ padding:6px 18px; border-radius:6px; text-decoration:none; font-weight:600;
             font-size:0.85rem; border:1px solid #333; color:#aaa; }}
  .nav a.active {{ background:#34d399; color:#111; border-color:#34d399; }}
  .nav a:not(.active):hover {{ background:#1f1f1f; color:#eee; }}
</style>
</head>
<body>
<h1>Qwen 2.5 Coder 7B — Score Summary</h1>
<p class="sub">71 tasks · no images · sorted by score</p>
<nav class="nav">
  <a href="report_claude.html">Claude Sonnet 4.6</a>
  <a href="report_qwen.html">Full Report</a>
  <a href="report_qwen_compact.html" class="active">Compact</a>
</nav>
<div class="stats">
  <div class="stat"><div class="stat-v" style="color:#ef4444">{yes_count}/{len(rows)}</div><div class="stat-l">Visual Match ≥65%</div></div>
  <div class="stat"><div class="stat-v" style="color:{col(avg_nss/100)}">{avg_nss:.1f}%</div><div class="stat-l">Avg NSS</div></div>
  <div class="stat"><div class="stat-v" style="color:{col(avg_kcss/100)}">{avg_kcss:.1f}%</div><div class="stat-l">Avg KCSS</div></div>
</div>

<div class="section">
  <div class="section-title">Visual Accuracy (NSS) — sorted high to low</div>
  {''.join(nss_row(r) for r in nss_sorted)}
</div>

<div class="section">
  <div class="section-title">Code Quality (KCSS) — sorted high to low &nbsp;·&nbsp; S=Structure &nbsp;I=Idioms &nbsp;X=Simplicity</div>
  {''.join(kcss_row(r) for r in kcss_sorted)}
</div>

</body>
</html>"""

OUT_HTML.write_text(html, encoding="utf-8")
print(f"\nWritten: {OUT_HTML}")
print(f"YES: {yes_count}/{len(rows)}  |  avg NSS {avg_nss:.1f}%  |  avg KCSS {avg_kcss:.1f}%")
