"""
GT Validity Audit — KojoBench2
Quantifies construct-validity defects in the 75 ground-truth tasks.

Outputs:
  runs/report_gt_validity.md   — markdown report with defect catalogue + tally
  runs/gt_contact_sheet.png    — 75-cell grid for manual eyeballing

Steps:
  1. DUPLICATE QUERIES   — exact + near-identical query text (difflib ratio > 0.92)
  2. COLLISION CHECK     — same query / different image  &  same image / different query
                           using perceptual hash (pHash, Hamming distance threshold)
  3. RENDER SANITY       — GT PNG missing or blank (no drawn pixels)
  4. CONTACT SHEET       — grid of all 75 GT renders, labeled T{N}: query[:40]

Pure read + render — does NOT touch any shared pipeline code.
"""

import sys, textwrap, itertools, re
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime

import imagehash
from PIL import Image, ImageDraw, ImageFont
import numpy as np

BASE        = Path(__file__).parent.parent
BENCH       = BASE / "benchmark"
OUT_MD      = Path(__file__).parent / "report_gt_validity.md"
OUT_SHEET   = Path(__file__).parent / "gt_contact_sheet.png"
TASKS       = list(range(1, 76))

# Thresholds
QUERY_SIM_THRESH    = 0.92   # SequenceMatcher ratio — near-duplicate query
PHASH_EXCL_THRESH   = 22     # pHash Hamming distance ABOVE this → skip NSS (reliably different)
                              # pHash is only used as a fast EXCLUSION filter, not for similarity judgement
PHASH_DIFF_THRESH   = 18     # for 2a: same-query/diff-image detection (high dist = reliably different)
NSS_SAME_THRESH     = 0.88   # NSS >= this → visually same image (NSS is the actual similarity measure)
BLANK_PIXEL_THRESH  = 50     # fewer drawn pixels than this → blank render

sys.path.insert(0, str(BASE))

# ── Load all task data ────────────────────────────────────────────────────────

def load_query(t):
    f = BENCH / f"Task{t}" / f"KojoQuery{t}.md"
    return f.read_text(encoding="utf-8").strip() if f.exists() else ""

def load_gt_png(t):
    p = BENCH / f"Task{t}" / "ground_truth_kojo.png"
    return p if p.exists() else None

def load_gt_code(t):
    f = BENCH / f"Task{t}" / f"KojoTask{t}.kojo"
    return f.read_text(encoding="utf-8").strip() if f.exists() else ""

def query_sim(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def phash(png_path):
    try:
        return imagehash.phash(Image.open(png_path))
    except Exception:
        return None

def is_blank(png_path):
    try:
        img = Image.open(png_path).convert("L")
        arr = np.array(img)
        drawn = np.sum(arr < 240)
        return drawn < BLANK_PIXEL_THRESH
    except Exception:
        return True

print("Loading task data...")
queries = {t: load_query(t) for t in TASKS}
gt_pngs = {t: load_gt_png(t) for t in TASKS}
gt_codes = {t: load_gt_code(t) for t in TASKS}

print("Computing perceptual hashes...")
hashes = {}
for t in TASKS:
    p = gt_pngs[t]
    hashes[t] = phash(p) if p else None
    print(f"  T{t}: {'ok' if hashes[t] is not None else 'NO PNG'}")

# ── Step 1: DUPLICATE QUERIES ─────────────────────────────────────────────────
print("\n--- Step 1: Duplicate queries ---")
dup_pairs = []   # (t1, t2, ratio, exact)
for t1, t2 in itertools.combinations(TASKS, 2):
    q1, q2 = queries[t1], queries[t2]
    if not q1 or not q2:
        continue
    ratio = query_sim(q1, q2)
    exact = q1.lower().strip() == q2.lower().strip()
    if exact or ratio >= QUERY_SIM_THRESH:
        dup_pairs.append((t1, t2, ratio, exact))
        print(f"  T{t1} vs T{t2}: ratio={ratio:.3f} exact={exact}")

# ── Step 2: COLLISION CHECK ───────────────────────────────────────────────────
print("\n--- Step 2: Collision check ---")
# 2a. Same (similar) query but visually different image
query_diff_image = []
for t1, t2, ratio, exact in dup_pairs:
    h1, h2 = hashes[t1], hashes[t2]
    if h1 is None or h2 is None:
        continue
    dist = h1 - h2
    if dist >= PHASH_DIFF_THRESH:
        query_diff_image.append((t1, t2, ratio, dist))
        print(f"  SAME-QUERY/DIFF-IMAGE: T{t1} vs T{t2}  query_sim={ratio:.3f}  phash_dist={dist}")

# 2b. Visually same image but different query
# NSS is the actual similarity measure for thin-line graphics on white backgrounds.
# pHash is used ONLY as a fast exclusion filter: if pHash distance is high (> PHASH_EXCL_THRESH)
# the images are reliably different and NSS can be skipped. If pHash is low/medium, we cannot
# conclude anything — we must run NSS. This is correct because pHash collapses exactly the
# high-frequency differences that matter for line art while preserving the white background
# structure that doesn't. Low pHash distance means "same coarse luminance" not "same shape."
sys.path.insert(0, str(BASE))
from utils.shape_similarity import nss_score

same_image_diff_query = []
nss_run = 0
nss_skipped = 0
pairs_checked = list(itertools.combinations(TASKS, 2))
n_total = len(pairs_checked)

for i, (t1, t2) in enumerate(pairs_checked):
    if i % 200 == 0:
        print(f"  2b progress: {i}/{n_total}  (NSS run={nss_run} skipped={nss_skipped})", flush=True)
    q_sim = query_sim(queries[t1], queries[t2])
    if q_sim >= 0.70:          # queries too similar — not a "different query" case
        nss_skipped += 1
        continue
    p1, p2 = gt_pngs[t1], gt_pngs[t2]
    if p1 is None or p2 is None:
        nss_skipped += 1
        continue
    h1, h2 = hashes[t1], hashes[t2]
    if h1 is not None and h2 is not None and (h1 - h2) > PHASH_EXCL_THRESH:
        nss_skipped += 1        # pHash says reliably different — skip NSS
        continue
    nss = nss_score(str(p1), str(p2))
    nss_run += 1
    if nss >= NSS_SAME_THRESH:
        same_image_diff_query.append((t1, t2, round(nss, 3), q_sim))
        print(f"  SAME-IMAGE/DIFF-QUERY: T{t1} vs T{t2}  NSS={nss:.3f}  query_sim={q_sim:.3f}")

print(f"  2b done: NSS run={nss_run}  skipped by pHash exclusion={nss_skipped}")

# ── Step 3: RENDER SANITY ─────────────────────────────────────────────────────
print("\n--- Step 3: Render sanity ---")
missing_png   = [t for t in TASKS if gt_pngs[t] is None]
blank_png     = [t for t in TASKS if gt_pngs[t] and is_blank(gt_pngs[t])]
missing_code  = [t for t in TASKS if not gt_codes[t]]
missing_query = [t for t in TASKS if not queries[t]]
print(f"  Missing PNG:   {missing_png}")
print(f"  Blank PNG:     {blank_png}")
print(f"  Missing code:  {missing_code}")
print(f"  Missing query: {missing_query}")

# ── Step 4: CONTACT SHEET ─────────────────────────────────────────────────────
print("\n--- Step 4: Contact sheet ---")
COLS = 5
ROWS = 15
CELL_W, CELL_H = 210, 210
LABEL_H = 40
IMG_W = COLS * CELL_W
IMG_H = ROWS * (CELL_H + LABEL_H)

sheet = Image.new("RGB", (IMG_W, IMG_H), (240, 240, 240))
draw  = ImageDraw.Draw(sheet)

try:
    font_lbl = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 11)
    font_id  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 13)
except Exception:
    font_lbl = ImageFont.load_default()
    font_id  = font_lbl

# Collect defect flags per task for contact sheet markup
defect_tasks = set()
defect_tasks.update(missing_png)
defect_tasks.update(blank_png)
defect_tasks.update([t for pair in dup_pairs for t in pair[:2]])
defect_tasks.update([t for pair in query_diff_image for t in pair[:2]])
defect_tasks.update([t for pair in same_image_diff_query for t in pair[:2]])

for idx, t in enumerate(TASKS):
    col = idx % COLS
    row = idx // COLS
    x = col * CELL_W
    y = row * (CELL_H + LABEL_H)

    # Border colour: red = defect, green = clean
    border_col = (220, 50, 50) if t in defect_tasks else (80, 180, 80)
    draw.rectangle([x, y, x+CELL_W-1, y+CELL_H+LABEL_H-1], outline=border_col, width=2)

    # Task image
    png = gt_pngs[t]
    if png:
        try:
            img = Image.open(png).convert("RGB")
            img.thumbnail((CELL_W - 6, CELL_H - 6))
            px = x + (CELL_W - img.width)  // 2
            py = y + (CELL_H - img.height) // 2
            sheet.paste(img, (px, py))
        except Exception:
            draw.text((x+10, y+CELL_H//2), "ERROR", fill=(200,0,0), font=font_id)
    else:
        draw.rectangle([x+3, y+3, x+CELL_W-4, y+CELL_H-4], fill=(255,220,220))
        draw.text((x+10, y+CELL_H//2), "NO PNG", fill=(180,0,0), font=font_id)

    # Label strip
    ly = y + CELL_H
    draw.rectangle([x, ly, x+CELL_W-1, ly+LABEL_H-1], fill=(30,30,30))
    draw.text((x+4, ly+2), f"T{t}", fill=(255,220,80), font=font_id)
    q = queries[t][:55] if queries[t] else "(no query)"
    # wrap query text to two lines
    wrapped = textwrap.wrap(q, width=30)[:2]
    for li, line in enumerate(wrapped):
        draw.text((x+4, ly+16+li*12), line, fill=(200,200,200), font=font_lbl)

sheet.save(str(OUT_SHEET))
print(f"  Contact sheet saved: {OUT_SHEET}  ({IMG_W}x{IMG_H})")

# ── Tally defects ─────────────────────────────────────────────────────────────
all_defective = set()
all_defective.update(missing_png)
all_defective.update(blank_png)
all_defective.update(missing_code)
all_defective.update(missing_query)
for t1, t2, ratio, dist in query_diff_image:
    all_defective.add(t1); all_defective.add(t2)
for t1, t2, dist, q_sim in same_image_diff_query:
    all_defective.add(t1); all_defective.add(t2)
# Near-duplicate queries without visual diff: flag both as ambiguous
for t1, t2, ratio, exact in dup_pairs:
    all_defective.add(t1); all_defective.add(t2)

n_defective = len(all_defective)
n_clean     = 75 - n_defective

# ── Write Markdown report ─────────────────────────────────────────────────────
def fmt_tasks(lst):
    return ", ".join(f"T{t}" for t in sorted(lst)) if lst else "none"

lines = []
A = lines.append

A(f"# KojoBench2 — GT Validity Audit")
A(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
A("")
A("## Summary")
A("")
A(f"| Metric | Count |")
A(f"|---|---|")
A(f"| Total tasks | 75 |")
A(f"| **Clean (no defect detected)** | **{n_clean}** |")
A(f"| Defective (any flag) | {n_defective} |")
A(f"| **Achievable NSS ceiling** | **{n_clean}/75 ({n_clean/75*100:.0f}%)** |")
A("")
A("---")
A("")

# 1. Duplicate queries
A("## 1. Duplicate / Near-Identical Queries")
A("")
if dup_pairs:
    A(f"| T1 | T2 | Similarity | Exact | Query T1 (first 80 chars) | Query T2 (first 80 chars) |")
    A(f"|---|---|---|---|---|---|")
    for t1, t2, ratio, exact in sorted(dup_pairs):
        q1 = queries[t1][:80].replace("|","\\|")
        q2 = queries[t2][:80].replace("|","\\|")
        A(f"| T{t1} | T{t2} | {ratio:.3f} | {'YES' if exact else 'no'} | {q1} | {q2} |")
else:
    A("None found.")
A("")

# 2. Collision check
A("## 2. Collision Check")
A("")
A("### 2a. Same/similar query — visually different image (query→target ambiguity)")
A("")
if query_diff_image:
    A(f"| T1 | T2 | Query sim | pHash dist | Defect class |")
    A(f"|---|---|---|---|---|")
    for t1, t2, ratio, dist in sorted(query_diff_image):
        A(f"| T{t1} | T{t2} | {ratio:.3f} | {dist} | query→target ambiguity |")
else:
    A("None found.")
A("")
A("### 2b. Visually same image — different query (duplicate target)")
A("")
A("Detection method: NSS >= 0.88 (chamfer + edge correlation on binarised shapes).")
A("")
if same_image_diff_query:
    A(f"| T1 | T2 | NSS | Query sim | Defect class |")
    A(f"|---|---|---|---|---|")
    for t1, t2, nss, q_sim in sorted(same_image_diff_query):
        A(f"| T{t1} | T{t2} | {nss:.3f} | {q_sim:.3f} | duplicate target |")
else:
    A("None found.")
A("")

# 3. Render sanity
A("## 3. Render Sanity")
A("")
A(f"| Check | Tasks |")
A(f"|---|---|")
A(f"| Missing GT PNG | {fmt_tasks(missing_png)} |")
A(f"| Blank GT PNG (< {BLANK_PIXEL_THRESH} drawn pixels) | {fmt_tasks(blank_png)} |")
A(f"| Missing GT Kojo code | {fmt_tasks(missing_code)} |")
A(f"| Missing query text | {fmt_tasks(missing_query)} |")
A("")

# 4. Full defect catalogue
A("## 4. Defect Catalogue")
A("")
A(f"| Task | Defect class | Notes |")
A(f"|---|---|---|")
for t in sorted(all_defective):
    flags = []
    if t in missing_png:      flags.append("MISSING_PNG")
    if t in blank_png:        flags.append("BLANK_PNG")
    if t in missing_code:     flags.append("MISSING_CODE")
    if t in missing_query:    flags.append("MISSING_QUERY")
    for t1, t2, ratio, exact in dup_pairs:
        if t in (t1, t2):
            other = t2 if t == t1 else t1
            label = "EXACT_DUP_QUERY" if exact else f"NEAR_DUP_QUERY(sim={ratio:.2f})"
            flags.append(f"{label} with T{other}")
    for t1, t2, ratio, dist in query_diff_image:
        if t in (t1, t2):
            other = t2 if t == t1 else t1
            flags.append(f"QUERY_TARGET_AMBIGUITY(phash_dist={dist}) with T{other}")
    for t1, t2, nss, q_sim in same_image_diff_query:
        if t in (t1, t2):
            other = t2 if t == t1 else t1
            flags.append(f"DUPLICATE_TARGET(NSS={nss:.2f}) with T{other}")
    q_preview = queries[t][:70].replace("|","\\|") if queries[t] else "(no query)"
    A(f"| T{t} | {'; '.join(flags)} | {q_preview} |")
A("")

A("## 5. Notes")
A("")
A("- Tasks 26–75: GT code was auto-generated from a Python Turtle archive; query text was LLM-described.")
A("- Known issue: T72 and T74 share identical query text but have different GT images (different archive entries).")
A(f"- Visual similarity (2b): NSS >= {NSS_SAME_THRESH} (chamfer distance + edge correlation on binarised shapes).")
A(f"- pHash used only as exclusion pre-filter (Hamming > {PHASH_EXCL_THRESH} → skip NSS). Never used to assert similarity.")
A(f"- pHash for 2a (same-query/diff-image): Hamming distance >= {PHASH_DIFF_THRESH} confirms images differ.")
A("- Near-duplicate query threshold: SequenceMatcher ratio >= 0.92.")
A(f"- Contact sheet: `gt_contact_sheet.png` — red border = flagged, green = clean.")
A("- This audit does NOT fix GT. Use contact sheet for manual triage.")

OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(f"\nMarkdown report: {OUT_MD}")

print(f"\n{'='*60}")
print(f"RESULT: {n_clean} CLEAN / {n_defective} DEFECTIVE out of 75")
print(f"Achievable NSS ceiling: {n_clean}/75 ({n_clean/75*100:.0f}%)")
print(f"{'='*60}")
