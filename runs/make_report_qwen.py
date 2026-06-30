"""
Generates a self-contained HTML report: GT vs Qwen side-by-side for all 71 scored tasks.
YES/NO = NSS >= 65%
"""
import base64, sys
from pathlib import Path

BASE        = Path(__file__).parent.parent
GT_DIR      = BASE / "benchmark"
QWEN_DIR    = Path(__file__).parent / "qwen_rendered"
OUT_HTML    = Path(__file__).parent / "reports" / "report_qwen.html"
_DROP_TASKS = {1, 16, 50, 60}   # NSS scorer blind spots — excluded from scoring
TASKS       = [t for t in range(1, 76) if t not in _DROP_TASKS]
MATCH_THRESH = 0.65

sys.path.insert(0, str(BASE))

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

def compute_nss(gt_png, qw_png):
    try:
        from utils.shape_similarity import nss_score
        return nss_score(str(gt_png), str(qw_png))
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
    gt_png  = GT_DIR / f"Task{t}" / "ground_truth_kojo.png"
    qw_png  = QWEN_DIR / f"task{t}.png"
    nss     = compute_nss(gt_png, qw_png) if (gt_png.exists() and qw_png.exists()) else None
    kcss, struct, idiom, simpl = compute_kcss(t)
    rows.append({
        "task":   t,
        "query":  query(t),
        "gt64":   img64(gt_png),
        "qw64":   img64(qw_png),
        "nss":    nss,
        "kcss":   kcss,
        "struct": struct,
        "idiom":  idiom,
        "simpl":  simpl,
        "match":  nss is not None and nss >= MATCH_THRESH,
    })
    print(f"  T{t}: NSS={nss*100:.0f}% KCSS={kcss*100:.0f}%" if (nss and kcss) else f"  T{t}: NSS={'?' if nss is None else f'{nss*100:.0f}%'} KCSS={'?' if kcss is None else f'{kcss*100:.0f}%'}")

def score_color(v):
    if v is None: return "#555"
    if v >= 0.75: return "#22c55e"
    if v >= 0.50: return "#f59e0b"
    return "#ef4444"

def card(r):
    nss_pct  = f"{r['nss']*100:.0f}%"  if r['nss']  is not None else "?"
    kcss_pct = f"{r['kcss']*100:.0f}%" if r['kcss'] is not None else "?"
    yes_no   = "YES" if r['match'] else "NO"
    yn_color = "#22c55e" if r['match'] else "#ef4444"
    gt_src   = f"data:image/png;base64,{r['gt64']}" if r['gt64'] else ""
    qw_src   = f"data:image/png;base64,{r['qw64']}" if r['qw64'] else ""
    gt_img   = f'<img src="{gt_src}">' if gt_src else '<div class="no-img">no image</div>'
    qw_img   = f'<img src="{qw_src}">' if qw_src else '<div class="no-img">no render</div>'
    nc = score_color(r['nss'])
    kc = score_color(r['kcss'])
    struct_pct = f"{r['struct']*100:.0f}" if r['struct'] is not None else "0"
    idiom_pct  = f"{r['idiom']*100:.0f}"  if r['idiom']  is not None else "0"
    simpl_pct  = f"{r['simpl']*100:.0f}"  if r['simpl']  is not None else "0"
    return f"""
<div class="card">
  <div class="card-header">
    <span class="task-num">T{r['task']}</span>
    <span class="verdict" style="background:{yn_color}">{yes_no}</span>
  </div>
  <p class="qtext">{r['query']}</p>
  <div class="scores">
    <div class="score-row">
      <span class="score-label">Visual (NSS)</span>
      <div class="bar-bg"><div class="bar-fill" style="width:{r['nss']*100 if r['nss'] else 0:.0f}%;background:{nc}"></div></div>
      <span class="score-val" style="color:{nc}">{nss_pct}</span>
    </div>
    <div class="score-row">
      <span class="score-label">Code (KCSS)</span>
      <div class="bar-bg"><div class="bar-fill" style="width:{r['kcss']*100 if r['kcss'] else 0:.0f}%;background:{kc}"></div></div>
      <span class="score-val" style="color:{kc}">{kcss_pct}</span>
    </div>
    <div class="sub-bars">
      <div class="sub-row"><span>Structure</span><div class="bar-bg s"><div class="bar-fill" style="width:{struct_pct}%;background:#4fc3f7"></div></div><span>{struct_pct}%</span></div>
      <div class="sub-row"><span>Idioms</span><div class="bar-bg s"><div class="bar-fill" style="width:{idiom_pct}%;background:#81c784"></div></div><span>{idiom_pct}%</span></div>
      <div class="sub-row"><span>Simplicity</span><div class="bar-bg s"><div class="bar-fill" style="width:{simpl_pct}%;background:#ffb74d"></div></div><span>{simpl_pct}%</span></div>
    </div>
  </div>
  <div class="imgs">
    <div class="img-wrap"><div class="img-label">Ground Truth</div>{gt_img}</div>
    <div class="img-wrap"><div class="img-label">Qwen</div>{qw_img}</div>
  </div>
</div>"""

nss_vals  = [r['nss']  for r in rows if r['nss']  is not None]
kcss_vals = [r['kcss'] for r in rows if r['kcss'] is not None]
avg_nss   = sum(nss_vals)  / len(nss_vals)  * 100 if nss_vals  else 0
avg_kcss  = sum(kcss_vals) / len(kcss_vals) * 100 if kcss_vals else 0
yes_count = sum(1 for r in rows if r['match'])

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>KojoBench2 - Qwen Report</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #111; color: #eee; font-family: system-ui, sans-serif; padding: 24px; }}
  h1 {{ font-size: 1.6rem; text-align: center; margin-bottom: 6px; color: #fff; }}
  .subtitle {{ text-align: center; color: #888; margin-bottom: 14px; font-size: 0.9rem; }}
  .nav {{ display: flex; justify-content: center; gap: 12px; margin-bottom: 20px; }}
  .nav a {{ padding: 8px 22px; border-radius: 6px; text-decoration: none; font-weight: 600;
             font-size: 0.9rem; border: 1px solid #333; color: #aaa; }}
  .nav a.active {{ background: #34d399; color: #111; border-color: #34d399; }}
  .nav a:not(.active):hover {{ background: #1f1f1f; color: #eee; }}
  .summary {{ text-align: center; color: #aaa; margin-bottom: 24px; font-size: 0.9rem; display:flex; justify-content:center; gap:24px; flex-wrap:wrap; }}
  .stat {{ background:#1a1a1a; border:1px solid #2a2a2a; border-radius:8px; padding:10px 20px; }}
  .stat-val {{ font-size:1.4rem; font-weight:700; }}
  .stat-lbl {{ font-size:0.7rem; color:#666; text-transform:uppercase; letter-spacing:.06em; margin-top:2px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
  .card {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 10px; overflow: hidden; }}
  .card-header {{ display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #222; }}
  .task-num {{ font-weight: 700; font-size: 1.1rem; color: #34d399; min-width: 36px; }}
  .verdict {{ font-weight: 800; font-size: 0.8rem; padding: 3px 10px; border-radius: 4px; color: #fff; }}
  .qtext {{ font-size: 0.72rem; color: #777; padding: 8px 12px 4px; line-height: 1.4; }}
  .scores {{ padding: 8px 12px 4px; display:flex; flex-direction:column; gap:5px; }}
  .score-row {{ display:grid; grid-template-columns:80px 1fr 36px; align-items:center; gap:6px; }}
  .score-label {{ font-size:0.7rem; color:#999; }}
  .score-val {{ font-size:0.75rem; font-weight:700; text-align:right; }}
  .bar-bg {{ background:#2a2a2a; border-radius:3px; height:7px; overflow:hidden; }}
  .bar-bg.s {{ height:5px; }}
  .bar-fill {{ height:100%; border-radius:3px; }}
  .sub-bars {{ margin-top:4px; display:flex; flex-direction:column; gap:3px; }}
  .sub-row {{ display:grid; grid-template-columns:60px 1fr 30px; align-items:center; gap:5px; font-size:0.62rem; color:#666; }}
  .imgs {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding: 8px 10px 10px; }}
  .img-wrap {{ display: flex; flex-direction: column; align-items: center; }}
  .img-label {{ font-size: 0.6rem; color: #555; margin-bottom: 3px; text-transform: uppercase; letter-spacing: .06em; }}
  .img-wrap img {{ width: 100%; border-radius: 4px; display: block; border: 1px solid #2a2a2a; }}
  .no-img {{ width:100%; height:80px; display:flex; align-items:center; justify-content:center; color:#333; font-size:0.7rem; border:1px dashed #2a2a2a; border-radius:4px; }}
</style>
</head>
<body>
<h1>KojoBench2 - Qwen 2.5 Coder 7B</h1>
<p class="subtitle">Input: system prompt + query only &nbsp;·&nbsp; No ground-truth code seen &nbsp;·&nbsp; 71 tasks</p>
<nav class="nav">
  <a href="report_claude.html">Claude Sonnet 4.6</a>
  <a href="report_qwen.html" class="active">Qwen 2.5 Coder 7B</a>
</nav>
<div class="summary">
  <div class="stat"><div class="stat-val" style="color:{score_color(yes_count/len(rows))};font-size:2rem">{yes_count/len(rows):.2f}</div><div class="stat-lbl">Benchmark Score (0–1)</div></div>
  <div class="stat"><div class="stat-val" style="color:{score_color(yes_count/len(rows))}">{yes_count}/{len(rows)}</div><div class="stat-lbl">Visual Match (NSS >= 65%)</div></div>
  <div class="stat"><div class="stat-val" style="color:{score_color(avg_nss/100)}">{avg_nss:.1f}%</div><div class="stat-lbl">Avg Visual Accuracy (NSS)</div></div>
  <div class="stat"><div class="stat-val" style="color:{score_color(avg_kcss/100)}">{avg_kcss:.1f}%</div><div class="stat-lbl">Avg Code Quality (KCSS)</div></div>
</div>
<div class="grid">
{''.join(card(r) for r in rows)}
</div>
</body>
</html>"""

OUT_HTML.write_text(html, encoding="utf-8")
print(f"\nReport written to: {OUT_HTML}")
print(f"YES: {yes_count}/{len(rows)}  |  avg NSS {avg_nss:.1f}%  |  avg KCSS {avg_kcss:.1f}%")
