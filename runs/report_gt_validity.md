# KojoBench2 — GT Validity Audit
Generated: 2026-06-23 23:18

## Summary

| Metric | Count |
|---|---|
| Total tasks | 75 |
| **Clean (no defect detected)** | **67** |
| Defective (any flag) | 8 |
| **Achievable NSS ceiling** | **67/75 (89%)** |

---

## 1. Duplicate / Near-Identical Queries

None found.

## 2. Collision Check

### 2a. Same/similar query — visually different image (query→target ambiguity)

None found.

### 2b. Visually same image — different query (duplicate target)

Detection method: NSS >= 0.88 (chamfer + edge correlation on binarised shapes).

| T1 | T2 | NSS | Query sim | Defect class |
|---|---|---|---|---|
| T1 | T10 | 0.908 | 0.224 | duplicate target |
| T16 | T52 | 0.880 | 0.243 | duplicate target |
| T49 | T50 | 0.909 | 0.579 | duplicate target |
| T60 | T73 | 0.888 | 0.457 | duplicate target |

## 3. Render Sanity

| Check | Tasks |
|---|---|
| Missing GT PNG | none |
| Blank GT PNG (< 50 drawn pixels) | none |
| Missing GT Kojo code | none |
| Missing query text | none |

## 4. Defect Catalogue

| Task | Defect class | Notes |
|---|---|---|
| T1 | DUPLICATE_TARGET(NSS=0.91) with T10 | Draw a circle. |
| T10 | DUPLICATE_TARGET(NSS=0.91) with T1 | Draw a circle inside a square. The circle touches the middle of each s |
| T16 | DUPLICATE_TARGET(NSS=0.88) with T52 | Draw a square balanced on one of its four corners. All four sides are  |
| T49 | DUPLICATE_TARGET(NSS=0.91) with T50 | Draw four equal circles arranged in a clover pattern so that all four  |
| T50 | DUPLICATE_TARGET(NSS=0.91) with T49 | Draw four equal circles arranged in a clover or four-leaf pattern so t |
| T52 | DUPLICATE_TARGET(NSS=0.88) with T16 | Draw two squares of equal size overlapping at their centers, with one  |
| T60 | DUPLICATE_TARGET(NSS=0.89) with T73 | Draw four concentric equilateral triangles of increasing sizes all sha |
| T73 | DUPLICATE_TARGET(NSS=0.89) with T60 | Draw a large equilateral triangle with a smaller one inside it. |

## 5. Notes

- Tasks 26–75: GT code was auto-generated from a Python Turtle archive; query text was LLM-described.
- Known issue: T72 and T74 share identical query text but have different GT images (different archive entries).
- Visual similarity (2b): NSS >= 0.88 (chamfer distance + edge correlation on binarised shapes).
- pHash used only as exclusion pre-filter (Hamming > 22 → skip NSS). Never used to assert similarity.
- pHash for 2a (same-query/diff-image): Hamming distance >= 18 confirms images differ.
- Near-duplicate query threshold: SequenceMatcher ratio >= 0.92.
- Contact sheet: `gt_contact_sheet.png` — red border = flagged, green = clean.
- This audit does NOT fix GT. Use contact sheet for manual triage.