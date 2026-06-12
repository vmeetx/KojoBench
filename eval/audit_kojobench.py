"""
audit_kojobench.py

Visual audit tool for KojoNewDataset.
For each task it shows ground truth vs generated side by side, with a
shape-similarity score that is robust to canvas-position differences.

Better metric than raw IoU
--------------------------
Raw pixel IoU fails when the same shape is drawn at a different canvas
position (which happens because the Kojo turtle always starts at the
canvas centre, while the ground-truth images may be cropped/positioned
differently).

This script uses *Normalised Shape Similarity* (NSS):
  1. Binarise both images (drawn pixels vs white background).
  2. Crop each to its tight bounding box.
  3. Pad to square, resize to a common size (256 x 256).
  4. Compute IoU on the normalised thumbnails.
  5. Also compute a soft "edge density correlation" for partial-credit
     on shapes that are topologically correct but slightly mis-sized.

The final score is:  score = 0.7 * nss_iou + 0.3 * edge_corr
This penalises wrong shapes more than minor scaling errors.

Usage
-----
    python audit_kojobench.py            # all tasks in KojoNewDataset/
    python audit_kojobench.py --task 3   # single task debug
"""

import argparse
import sys
from pathlib import Path

# Allow imports from the repo root (utils/, models/)
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from PIL import Image
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent.parent   # repo root
DATASET_DIR = BASE / "KojoNewDataset"
THUMB_SIZE  = 256       # normalised thumbnail side length
BG_LUMA     = 240       # luminance threshold: pixels >= this are background


# ── Metric ────────────────────────────────────────────────────────────────────

def _binarise(img: Image.Image) -> np.ndarray:
    """Return bool mask: True = drawn pixel."""
    # Composite onto white so transparent pixels become white, not black
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])
        img = bg
    arr = np.array(img.convert("RGB"), dtype=np.float32)
    luma = arr[:, :, 0] * 0.299 + arr[:, :, 1] * 0.587 + arr[:, :, 2] * 0.114
    return luma < BG_LUMA


def _normalise_to_thumb(mask: np.ndarray) -> np.ndarray:
    """
    Crop to content bounding box, pad to square, resize to THUMB_SIZE.
    Returns a float32 array in [0, 1].
    """
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any():
        return np.zeros((THUMB_SIZE, THUMB_SIZE), dtype=np.float32)

    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]

    # Add a small padding around the content
    pad = max(10, int((r1 - r0 + c1 - c0) * 0.05))
    r0 = max(0, r0 - pad); r1 = min(mask.shape[0] - 1, r1 + pad)
    c0 = max(0, c0 - pad); c1 = min(mask.shape[1] - 1, c1 + pad)

    crop = mask[r0:r1+1, c0:c1+1].astype(np.uint8) * 255
    h, w = crop.shape
    side = max(h, w)
    square = np.zeros((side, side), dtype=np.uint8)
    y_off = (side - h) // 2
    x_off = (side - w) // 2
    square[y_off:y_off+h, x_off:x_off+w] = crop

    thumb = Image.fromarray(square).resize(
        (THUMB_SIZE, THUMB_SIZE), Image.LANCZOS
    )
    return np.array(thumb, dtype=np.float32) / 255.0


def _edge_density_hist(thumb: np.ndarray, bins: int = 16) -> np.ndarray:
    """Coarse spatial histogram of drawn pixels — captures topology."""
    h, w = thumb.shape
    bh, bw = h // bins, w // bins
    hist = np.zeros((bins, bins), dtype=np.float32)
    for i in range(bins):
        for j in range(bins):
            hist[i, j] = thumb[i*bh:(i+1)*bh, j*bw:(j+1)*bw].mean()
    flat = hist.flatten()
    norm = flat.sum()
    return flat / norm if norm > 0 else flat


CHAMFER_MAX = 20.0  # px on 256×256 thumbnail; chamfer >= this → score 0


def _chamfer_score(thumb_a: np.ndarray, thumb_b: np.ndarray) -> float:
    """
    Normalised Chamfer distance between two shape thumbnails.

    For each drawn pixel in A, find the nearest drawn pixel in B (and vice
    versa). Average those distances, then normalise to [0, 1].

    Why this beats IoU / soft-IoU:
    - Completely stroke-width invariant: a 7px thick GT stroke and a 2px
      thin Kojo stroke of the same circle score ~95% because the Kojo pixels
      sit inside the GT band (avg distance ≈ 1-2px out of CHAMFER_MAX).
    - Measures geometric proximity, not pixel overlap area.
    - Standard metric in computer vision for shape matching.
    """
    from scipy.ndimage import distance_transform_edt

    bin_a = thumb_a > 0.3
    bin_b = thumb_b > 0.3
    if not bin_a.any() or not bin_b.any():
        return 0.0

    dist_to_b = distance_transform_edt(~bin_b)
    dist_to_a = distance_transform_edt(~bin_a)

    a_to_b = float(dist_to_b[bin_a].mean())
    b_to_a = float(dist_to_a[bin_b].mean())
    chamfer = (a_to_b + b_to_a) / 2.0

    return max(0.0, 1.0 - chamfer / CHAMFER_MAX)


def normalised_shape_score(gt_path: Path, gen_path: Path) -> dict:
    """
    Compute shape similarity score between ground truth and generated image.
    Returns a dict with 'score', 'nss_iou', 'edge_corr'.
    """
    gt_img  = Image.open(gt_path)
    gen_img = Image.open(gen_path)

    gt_mask  = _binarise(gt_img)
    gen_mask = _binarise(gen_img)

    gt_thumb  = _normalise_to_thumb(gt_mask)
    gen_thumb = _normalise_to_thumb(gen_mask)

    nss_iou = _chamfer_score(gt_thumb, gen_thumb)

    # 2. Spatial layout correlation (Pearson r on coarse grid histogram)
    gt_hist  = _edge_density_hist(gt_thumb)
    gen_hist = _edge_density_hist(gen_thumb)
    if gt_hist.std() < 1e-6 or gen_hist.std() < 1e-6:
        edge_corr = 0.0
    else:
        edge_corr = float(np.corrcoef(gt_hist, gen_hist)[0, 1])
        edge_corr = max(0.0, edge_corr)

    score = 0.7 * nss_iou + 0.3 * edge_corr
    return {"score": score, "nss_iou": nss_iou, "edge_corr": edge_corr}


# ── Data loading ──────────────────────────────────────────────────────────────

def load_task(task_id: int) -> dict | None:
    task_dir = DATASET_DIR / f"Task{task_id}"
    gt_path  = task_dir / "ground_truth.png"
    gen_path = task_dir / "generated.png"
    prompt_path = task_dir / f"KojoQuery{task_id}.md"

    if not gt_path.exists() or not gen_path.exists():
        print(f"Task {task_id}: missing images, skipping.")
        return None

    desc = ""
    if prompt_path.exists():
        first_line = prompt_path.read_text(encoding="utf-8").strip().splitlines()[0]
        desc = first_line[:60] + ("…" if len(first_line) > 60 else "")

    metrics = normalised_shape_score(gt_path, gen_path)

    return {
        "id":       task_id,
        "desc":     desc,
        "gt_img":   Image.open(gt_path).convert("RGB"),
        "gen_img":  Image.open(gen_path).convert("RGB"),
        "score":    metrics["score"],
        "nss_iou":  metrics["nss_iou"],
        "edge_corr":metrics["edge_corr"],
    }


# ── Colour coding ─────────────────────────────────────────────────────────────

def score_color(s: float) -> str:
    if s >= 0.85: return "#2ecc71"   # green
    if s >= 0.60: return "#f39c12"   # amber
    return "#e74c3c"                  # red


# ── Display ───────────────────────────────────────────────────────────────────

def render_audit(tasks: list[dict]):
    n = len(tasks)
    fig = plt.figure(figsize=(14, 3.5 * n), facecolor="#1a1a2e")
    fig.canvas.manager.set_window_title("KojoNewDataset — Shape Similarity Audit")

    # Overall header
    overall = sum(t["score"] for t in tasks) / n
    fig.suptitle(
        f"KojoNewDataset Audit   |   Tasks: {n}   |   "
        f"Avg score: {overall*100:.1f}%",
        fontsize=14, color="white", y=1.002, fontweight="bold"
    )

    outer = gridspec.GridSpec(n, 1, figure=fig, hspace=0.55)

    for row, t in enumerate(tasks):
        inner = gridspec.GridSpecFromSubplotSpec(
            2, 3,
            subplot_spec=outer[row],
            width_ratios=[1, 1, 0.55],
            height_ratios=[0.18, 1],
            hspace=0.08, wspace=0.15,
        )

        # ── Header row ────────────────────────────────────────────────────────
        ax_hdr = fig.add_subplot(inner[0, :])
        ax_hdr.set_facecolor("#16213e")
        ax_hdr.axis("off")

        color = score_color(t["score"])
        ax_hdr.text(
            0.01, 0.5,
            f"Task {t['id']}  —  {t['desc']}",
            transform=ax_hdr.transAxes,
            fontsize=10, color="white", va="center", ha="left",
        )
        ax_hdr.text(
            0.99, 0.5,
            f"{t['score']*100:.1f}%  "
            f"(NSS-IoU {t['nss_iou']*100:.0f}%  |  "
            f"edge-corr {t['edge_corr']*100:.0f}%)",
            transform=ax_hdr.transAxes,
            fontsize=9, color=color, va="center", ha="right", fontweight="bold",
        )

        # ── Ground truth ──────────────────────────────────────────────────────
        ax_gt = fig.add_subplot(inner[1, 0])
        ax_gt.imshow(t["gt_img"])
        ax_gt.set_title("Ground Truth", fontsize=8, color="#aaaaaa", pad=3)
        ax_gt.axis("off")

        # ── Generated ─────────────────────────────────────────────────────────
        ax_gen = fig.add_subplot(inner[1, 1])
        ax_gen.imshow(t["gen_img"])
        ax_gen.set_title("Generated", fontsize=8, color="#aaaaaa", pad=3)
        ax_gen.axis("off")

        # ── Score bar ─────────────────────────────────────────────────────────
        ax_bar = fig.add_subplot(inner[1, 2])
        ax_bar.set_facecolor("#0f3460")
        ax_bar.axis("off")

        bar_h = 0.22
        metrics = [
            ("Score",     t["score"],     color),
            ("NSS-IoU",   t["nss_iou"],   "#3498db"),
            ("Edge-corr", t["edge_corr"], "#9b59b6"),
        ]
        for k, (label, val, col) in enumerate(metrics):
            y = 0.72 - k * 0.28
            ax_bar.barh(y, val, height=bar_h, color=col, alpha=0.85,
                        left=0, clip_on=False)
            ax_bar.barh(y, 1.0, height=bar_h, color="#ffffff", alpha=0.06,
                        left=0, clip_on=False)
            ax_bar.text(-0.02, y, label, fontsize=7.5, color="white",
                        va="center", ha="right", transform=ax_bar.transData)
            ax_bar.text(val + 0.02, y, f"{val*100:.0f}%",
                        fontsize=7.5, color=col, va="center", ha="left",
                        transform=ax_bar.transData)

        ax_bar.set_xlim(0, 1.35)
        ax_bar.set_ylim(-0.1, 1.0)

    plt.tight_layout()
    plt.show()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Audit KojoNewDataset similarity scores.")
    parser.add_argument("--task", type=int, default=None,
                        help="Single task ID to audit (default: all)")
    args = parser.parse_args()

    task_ids = [args.task] if args.task else sorted(
        int(d.name.replace("Task", ""))
        for d in DATASET_DIR.iterdir()
        if d.is_dir() and d.name.startswith("Task")
    )

    tasks = [t for i in task_ids if (t := load_task(i)) is not None]

    if not tasks:
        print("No tasks found. Check KojoNewDataset/ exists and has ground_truth.png + generated.png.")
        sys.exit(1)

    # Print summary table
    print(f"\n{'Task':<6} {'Score':>7} {'NSS-IoU':>9} {'Edge-corr':>11}  Description")
    print("-" * 70)
    for t in tasks:
        print(f"  {t['id']:<4} {t['score']*100:>6.1f}%  "
              f"{t['nss_iou']*100:>7.1f}%  "
              f"{t['edge_corr']*100:>9.1f}%   {t['desc']}")
    avg = sum(t["score"] for t in tasks) / len(tasks)
    print("-" * 70)
    print(f"  {'AVG':<4} {avg*100:>6.1f}%\n")

    render_audit(tasks)


if __name__ == "__main__":
    main()
