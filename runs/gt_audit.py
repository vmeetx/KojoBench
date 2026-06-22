"""
Compares original Python Turtle images (archive) vs our Kojo GT renders (benchmark).
Generates a self-contained HTML report.
"""
import base64, sys
from pathlib import Path

BASE      = Path(__file__).parent.parent
ARCHIVE   = BASE / "archive" / "Tasks"
BENCHMARK = BASE / "benchmark"
OUT_HTML  = Path(__file__).parent / "report_gt_audit.html"
TASKS     = list(range(1, 76))

def img64(path):
    p = Path(path)
    if not p.exists():
        return None
    return base64.b64encode(p.read_bytes()).decode()

def compute_nss(p1, p2):
    try:
        sys.path.insert(0, str(BASE))
        from utils.shape_similarity import nss_score
        return nss_score(str(p1), str(p2))
    except Exception:
        return None

def query(task_id):
    f = BENCHMARK / f"Task{task_id}" / f"KojoQuery{task_id}.md"
    if not f.exists():
        return f"Task {task_id}"
    t = f.read_text(encoding="utf-8").strip()
    return t[:100] + ("..." if len(t) > 100 else "")

rows = []
for t in TASKS:
    orig_png = ARCHIVE / str(t) / "image" / f"{t}.png"
    gt_png   = BENCHMARK / f"Task{t}" / "ground_truth_kojo.png"
    nss      = compute_nss(orig_png, gt_png) if (orig_png.exists() and gt_png.exists()) else None
    rows.append({
        "task":  t,
        "query": query(t),
        "orig64": img64(orig_png),
        "gt64":   img64(gt_png),
        "nss":    nss,
        "good":   nss is not None and nss >= 0.65,
        "orig_exists": orig_png.exists(),
        "gt_exists":   gt_png.exists(),
    })
    status = f"NSS={nss*100:.0f}%" if nss is not None else ("no orig" if not orig_png.exists() else "no GT")
    print(f"  T{t}: {status}")

def card(r):
    nss_str  = f"{r['nss']*100:.0f}%" if r['nss'] is not None else "?"
    verdict  = "GOOD" if r['good'] else ("NO ORIG" if not r['orig_exists'] else "DRIFT")
    vc       = "#22c55e" if r['good'] else ("#888" if not r['orig_exists'] else "#f59e0b")
    o_src    = f"data:image/png;base64,{r['orig64']}" if r['orig64'] else ""
    g_src    = f"data:image/png;base64,{r['gt64']}"   if r['gt64']   else ""
    o_img    = f'<img src="{o_src}">' if o_src else '<div class="no-img">no original</div>'
    g_img    = f'<img src="{g_src}">' if g_src else '<div class="no-img">no GT render</div>'
    return f"""
<div class="card">
  <div class="card-header">
    <span class="task-num">T{r['task']}</span>
    <span class="verdict" style="background:{vc}">{verdict}</span>
    <span class="nss">NSS {nss_str}</span>
  </div>
  <p class="qtext">{r['query']}</p>
  <div class="imgs">
    <div class="img-wrap"><div class="img-label">Python Original</div>{o_img}</div>
    <div class="img-wrap"><div class="img-label">Kojo GT Render</div>{g_img}</div>
  </div>
</div>"""

good  = sum(1 for r in rows if r['good'])
drift = sum(1 for r in rows if r['nss'] is not None and not r['good'])
nss_vals = [r['nss'] for r in rows if r['nss'] is not None]
avg_nss  = sum(nss_vals) / len(nss_vals) * 100 if nss_vals else 0

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>KojoBench2 — GT Accuracy Audit</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #111; color: #eee; font-family: system-ui, sans-serif; padding: 24px; }}
  h1 {{ font-size: 1.6rem; text-align: center; margin-bottom: 6px; color: #fff; }}
  .subtitle {{ text-align: center; color: #888; margin-bottom: 20px; font-size: 0.9rem; }}
  .summary {{ text-align: center; color: #aaa; margin-bottom: 20px; font-size: 0.95rem; }}
  .good  {{ color: #22c55e; font-weight: 700; }}
  .drift {{ color: #f59e0b; font-weight: 700; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }}
  .card {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; overflow: hidden; }}
  .card-header {{ display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #222; }}
  .task-num {{ font-weight: 700; font-size: 1.1rem; color: #60a5fa; min-width: 36px; }}
  .verdict {{ font-weight: 800; font-size: 0.85rem; padding: 3px 10px; border-radius: 4px; color: #111; letter-spacing: .04em; }}
  .nss {{ font-size: 0.8rem; color: #aaa; margin-left: auto; }}
  .qtext {{ font-size: 0.75rem; color: #888; padding: 8px 14px 6px; line-height: 1.4; }}
  .imgs {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding: 0 10px 10px; }}
  .img-wrap {{ display: flex; flex-direction: column; align-items: center; }}
  .img-label {{ font-size: 0.65rem; color: #666; margin-bottom: 4px; text-transform: uppercase; letter-spacing: .06em; }}
  .img-wrap img {{ width: 100%; border-radius: 4px; display: block; border: 1px solid #333; }}
  .no-img {{ width: 100%; height: 100px; display: flex; align-items: center; justify-content: center;
             color: #444; font-size: 0.75rem; border: 1px dashed #333; border-radius: 4px; }}
</style>
</head>
<body>
<h1>GT Accuracy Audit — Python Original vs Kojo GT Render</h1>
<p class="subtitle">How faithful is our Kojo ground truth to the original Python Turtle image?</p>
<p class="summary">
  <span class="good">GOOD (NSS ≥ 65%): {good}</span>
  &nbsp;/&nbsp;
  <span class="drift">DRIFT: {drift}</span>
  &nbsp;·&nbsp; avg NSS {avg_nss:.1f}%
  &nbsp;·&nbsp; {len([r for r in rows if r['nss'] is not None])} comparable tasks
</p>
<div class="grid">
{''.join(card(r) for r in rows)}
</div>
</body>
</html>"""

OUT_HTML.write_text(html, encoding="utf-8")
print(f"\nReport: {OUT_HTML}")
print(f"GOOD: {good}  DRIFT: {drift}  avg NSS: {avg_nss:.1f}%")
