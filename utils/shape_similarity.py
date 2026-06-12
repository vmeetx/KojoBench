"""
utils/shape_similarity.py

NSS (Normalised Shape Similarity) between a ground-truth image and a model-generated image.

Replaces the original raw pixel-IoU which gave near-zero scores for visually matching
images because:
  1. Kojo renders as RGBA 950×700; GT images are RGB 863×836.
     PIL's .convert("RGB") turns transparent pixels black → entire canvas marked "drawn".
  2. Different canvas sizes mean shapes sit at different absolute pixel positions
     after naive resize to 500×500.
  3. GT images (hand-drawn or Python turtle) have different stroke widths than Kojo renders.

NSS fix:
  1. RGBA → composite onto white before binarising (fixes transparent-bg bug).
  2. Crop to content bounding box + resize to 256×256 (position/scale invariant).
  3. MaxFilter dilation (DILATE_PX) on both masks (stroke-width invariant).
  4. Final score = 0.7 × NSS-IoU  +  0.3 × edge-corr (Pearson r of 16×16 spatial histogram).

A task is considered "solved" if score >= NSS_THRESHOLD.
"""

import os
import numpy as np
from PIL import Image, ImageFilter

# ── Configurable constants ────────────────────────────────────────────────────
NSS_THRESHOLD  = 0.55   # NSS score to count a task as solved (cross-renderer realistic)
THUMB_SIZE     = 256    # Both bounding-box crops are resized to this
CHAMFER_MAX    = 20.0   # px on 256×256 thumbnail; chamfer >= this → score 0
GRID           = 16     # Spatial histogram grid for edge-corr
BG_LUMA        = 240    # Pixels with luminance >= this are treated as background

# Keep for backwards compat (used nowhere that checks the value directly)
ACCURACY_THRESHOLD = NSS_THRESHOLD
CANVAS_SIZE        = 500


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _to_rgb(img: Image.Image) -> Image.Image:
    """Convert any image mode to RGB, compositing RGBA onto white."""
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        alpha = img.convert("RGBA").split()[3]
        bg.paste(img.convert("RGBA"), mask=alpha)
        return bg
    return img.convert("RGB")


def _binarise(img: Image.Image) -> np.ndarray:
    """Return boolean mask where True == drawn pixel (non-background)."""
    arr  = np.array(_to_rgb(img), dtype=np.float32)
    luma = arr[:, :, 0] * 0.299 + arr[:, :, 1] * 0.587 + arr[:, :, 2] * 0.114
    return luma < BG_LUMA


def _bbox_crop_resize(mask: np.ndarray) -> np.ndarray:
    """
    Crop to content bounding box, resize to THUMB_SIZE × THUMB_SIZE.
    If the mask is blank, return a blank thumbnail (avoids zero-division).
    """
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any():
        return np.zeros((THUMB_SIZE, THUMB_SIZE), dtype=np.float32)
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    crop = mask[r0:r1+1, c0:c1+1].astype(np.uint8) * 255
    img  = Image.fromarray(crop).resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
    return np.array(img, dtype=np.float32) / 255.0


def _chamfer_score(thumb_a: np.ndarray, thumb_b: np.ndarray) -> float:
    """Normalised Chamfer distance — stroke-width invariant shape comparison."""
    from scipy.ndimage import distance_transform_edt
    bin_a = thumb_a > 0.3
    bin_b = thumb_b > 0.3
    if not bin_a.any() or not bin_b.any():
        return 0.0
    dist_to_b = distance_transform_edt(~bin_b)
    dist_to_a = distance_transform_edt(~bin_a)
    chamfer = (dist_to_b[bin_a].mean() + dist_to_a[bin_b].mean()) / 2.0
    return max(0.0, 1.0 - chamfer / CHAMFER_MAX)


def _edge_corr(a: np.ndarray, b: np.ndarray) -> float:
    """
    Pearson correlation of GRID×GRID spatial histograms of drawn pixels.
    Captures whether the layout of shapes matches, even if pixel-level IoU isn't perfect.
    """
    h, w = a.shape
    gh, gw = h // GRID, w // GRID
    def hist(m):
        return np.array([
            m[i*gh:(i+1)*gh, j*gw:(j+1)*gw].mean()
            for i in range(GRID) for j in range(GRID)
        ])
    ha, hb = hist(a), hist(b)
    denom = ha.std() * hb.std()
    if denom < 1e-8:
        return 0.0
    return float(np.corrcoef(ha, hb)[0, 1])


def nss_score(path_a: str, path_b: str) -> float:
    """
    Chamfer-based shape similarity between two image files.
    Returns a float in [0, 1] — higher is more similar.
    """
    try:
        img_a = Image.open(path_a)
        img_b = Image.open(path_b)
        thumb_a = _bbox_crop_resize(_binarise(img_a))
        thumb_b = _bbox_crop_resize(_binarise(img_b))
    except Exception:
        return 0.0

    chamfer = _chamfer_score(thumb_a, thumb_b)
    ec      = max(0.0, _edge_corr(thumb_a, thumb_b))

    return 0.7 * chamfer + 0.3 * ec


# ── Public interface (same signatures as before) ──────────────────────────────

def pixel_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Raw binary pixel-level IoU. Kept for internal use."""
    intersection = np.logical_and(mask_a, mask_b).sum()
    union        = np.logical_or(mask_a, mask_b).sum()
    return float(intersection / union) if union > 0 else 1.0


def calculate_accuracy(
    task_name: str,
    source_path: str,
    response_path: str,
) -> bool:
    """
    Compare model-rendered image against ground-truth using NSS.

    Returns True if NSS score >= NSS_THRESHOLD.
    """
    gt_path   = os.path.join(source_path,   task_name + ".png")
    pred_path = os.path.join(response_path, task_name + ".png")

    if not os.path.exists(gt_path):
        print(f"[shape_similarity] Ground-truth not found: {gt_path}")
        return False
    if not os.path.exists(pred_path):
        print(f"[shape_similarity] Prediction not found: {pred_path}")
        return False

    try:
        score  = nss_score(gt_path, pred_path)
        solved = score >= NSS_THRESHOLD
        print(
            f"[shape_similarity] {task_name}: NSS={score:.4f} "
            f"({'✓' if solved else '✗'})"
        )
        return solved
    except Exception as e:
        print(f"[shape_similarity] Error evaluating {task_name}: {e}")
        return False


def compute_iou_score(
    task_name: str,
    source_path: str,
    response_path: str,
) -> float:
    """
    Returns the NSS score (0.0–1.0) for a task.
    Named 'iou_score' for API compatibility — now returns NSS, which is more meaningful.
    """
    gt_path   = os.path.join(source_path,   task_name + ".png")
    pred_path = os.path.join(response_path, task_name + ".png")

    if not os.path.exists(gt_path) or not os.path.exists(pred_path):
        return 0.0
    return nss_score(gt_path, pred_path)
