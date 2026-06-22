"""
Generates a self-contained HTML report: GT vs Claude side-by-side for all 75 tasks.
YES/NO = NSS >= 65%
"""
import base64, re, sys
from pathlib import Path

BASE        = Path(__file__).parent.parent
GT_DIR      = BASE / "benchmark"
CLAUDE_DIR  = Path(__file__).parent / "claude_rendered"
OUT_HTML    = Path(__file__).parent / "report_claude.html"
TASKS       = list(range(1, 76))
MATCH_THRESH = 0.65

NSS_LOG = Path(__file__).parent.parent / "runs" / "nss_scores.txt"

def img64(path):
    p = Path(path)
    if not p.exists():
        return None
    return base64.b64encode(p.read_bytes()).decode()

def query(task_id):
    f = GT_DIR / f"Task{task_id}" / f"KojoQuery{task_id}.md"
    if not f.exists():
        return f"Task {task_id}"
    t = f.read_text(encoding="utf-8").strip()
    return t[:120] + ("..." if len(t) > 120 else "")

def compute_nss(gt_png, cl_png):
    try:
        sys.path.insert(0, str(BASE))
        from utils.shape_similarity import nss_score
        return nss_score(str(gt_png), str(cl_png))
    except Exception:
        return None

rows = []
for t in TASKS:
    gt_png = GT_DIR / f"Task{t}" / "ground_truth_kojo.png"
    cl_png = CLAUDE_DIR / f"task{t}.png"
    nss    = compute_nss(gt_png, cl_png) if (gt_png.exists() and cl_png.exists()) else None
    rows.append({
        "task":  t,
        "query": query(t),
        "gt64":  img64(gt_png),
        "cl64":  img64(cl_png),
        "nss":   nss,
        "match": nss is not None and nss >= MATCH_THRESH,
    })
    print(f"  T{t}: NSS={nss*100:.0f}%" if nss is not None else f"  T{t}: NSS=?")

def card(r):
    nss_str  = f"{r['nss']*100:.0f}%" if r['nss'] is not None else "?"
    yes_no   = "YES" if r['match'] else "NO"
    yn_color = "#22c55e" if r['match'] else "#ef4444"
    gt_src   = f"data:image/png;base64,{r['gt64']}" if r['gt64'] else ""
    cl_src   = f"data:image/png;base64,{r['cl64']}" if r['cl64'] else ""
    gt_img   = f'<img src="{gt_src}">' if gt_src else '<div class="no-img">no image</div>'
    cl_img   = f'<img src="{cl_src}">' if cl_src else '<div class="no-img">no render</div>'
    return f"""
<div class="card">
  <div class="card-header">
    <span class="task-num">T{r['task']}</span>
    <span class="verdict" style="background:{yn_color}">{yes_no}</span>
    <span class="nss">NSS {nss_str}</span>
  </div>
  <p class="qtext">{r['query']}</p>
  <div class="imgs">
    <div class="img-wrap">
      <div class="img-label">Ground Truth</div>
      {gt_img}
    </div>
    <div class="img-wrap">
      <div class="img-label">Claude</div>
      {cl_img}
    </div>
  </div>
</div>"""

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>KojoBench2 — Claude Report</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #111; color: #eee; font-family: system-ui, sans-serif; padding: 24px; }}
  h1 {{ font-size: 1.6rem; text-align: center; margin-bottom: 6px; color: #fff; }}
  .subtitle {{ text-align: center; color: #888; margin-bottom: 28px; font-size: 0.9rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }}
  .card {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; overflow: hidden; }}
  .card-header {{ display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #222; }}
  .task-num {{ font-weight: 700; font-size: 1.1rem; color: #a78bfa; min-width: 36px; }}
  .verdict {{ font-weight: 800; font-size: 0.85rem; padding: 3px 10px; border-radius: 4px; color: #fff; letter-spacing: .04em; }}
  .nss {{ font-size: 0.8rem; color: #aaa; margin-left: auto; }}
  .qtext {{ font-size: 0.75rem; color: #888; padding: 8px 14px 6px; line-height: 1.4; }}
  .imgs {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding: 0 10px 10px; }}
  .img-wrap {{ display: flex; flex-direction: column; align-items: center; }}
  .img-label {{ font-size: 0.65rem; color: #666; margin-bottom: 4px; text-transform: uppercase; letter-spacing: .06em; }}
  .img-wrap img {{ width: 100%; border-radius: 4px; display: block; border: 1px solid #333; }}
  .no-img {{ width: 100%; height: 100px; display: flex; align-items: center; justify-content: center;
             color: #444; font-size: 0.75rem; border: 1px dashed #333; border-radius: 4px; }}
  .summary {{ text-align: center; color: #aaa; margin-bottom: 20px; font-size: 0.95rem; }}
  .yes {{ color: #22c55e; font-weight: 700; }}
  .no  {{ color: #ef4444; font-weight: 700; }}
</style>
</head>
<body>
<h1>KojoBench2 — Claude Sonnet 4.6</h1>
<p class="subtitle">Input: system prompt + query only &nbsp;·&nbsp; No ground-truth code seen</p>
<p class="summary">
  <span class="yes">YES (match): {sum(1 for r in rows if r['match'])}</span>
  &nbsp;/&nbsp;
  <span class="no">NO: {sum(1 for r in rows if not r['match'])}</span>
  &nbsp;·&nbsp; avg NSS {sum(r['nss'] for r in rows if r['nss'] is not None)/len([r for r in rows if r['nss'] is not None])*100:.1f}%
  &nbsp;·&nbsp; threshold ≥ {int(MATCH_THRESH*100)}%
</p>
<div class="grid">
{''.join(card(r) for r in rows)}
</div>
</body>
</html>"""

OUT_HTML.write_text(html, encoding="utf-8")
print(f"\nReport written to: {OUT_HTML}")
print(f"YES: {sum(1 for r in rows if r['match'])} / NO: {sum(1 for r in rows if not r['match'])}")
