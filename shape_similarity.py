"""
utils/shape_similarity.py

Pixel-level IoU between a ground-truth image and a model-generated image.
This is a direct port of the logic from TurtleBench's utils/shape_similarity.py
(not published in the repo but described in the paper).

The metric:
  IoU = |pixels_drawn_in_both| / |pixels_drawn_in_either|

  where "drawn" means non-white (or non-background) pixels.

A task is considered "solved" if IoU >= ACCURACY_THRESHOLD (paper uses 0.95).

Both images are:
  - Resized to a common size (CANVAS_SIZE × CANVAS_SIZE) if needed
  - Converted to binary masks (background vs. drawn)

The background colour in Kojo defaults to white (255, 255, 255).
We binarise by thresholding: pixel is "drawn" if its luminance < 240.
"""

import os
import numpy as np
from PIL import Image

# ── Configurable constants ────────────────────────────────────────────────────
ACCURACY_THRESHOLD = 0.95   # IoU threshold to count a task as solved (paper §4)
CANVAS_SIZE        = 500    # Both images are resized to this before comparison
BACKGROUND_LUMA    = 240    # Pixels with luminance >= this are treated as bg


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_and_binarise(path: str) -> np.ndarray:
    """
    Load an image from disk, resize to CANVAS_SIZE, and return a boolean mask
    where True == "drawn pixel" (non-background).
    """
    img = Image.open(path).convert("RGB").resize(
        (CANVAS_SIZE, CANVAS_SIZE), Image.LANCZOS
    )
    arr = np.array(img, dtype=np.float32)
    # Luminance approximation: 0.299R + 0.587G + 0.114B
    luma = arr[:, :, 0] * 0.299 + arr[:, :, 1] * 0.587 + arr[:, :, 2] * 0.114
    return luma < BACKGROUND_LUMA   # True where something is drawn


def pixel_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Binary pixel-level IoU between two boolean arrays."""
    intersection = np.logical_and(mask_a, mask_b).sum()
    union        = np.logical_or(mask_a, mask_b).sum()
    if union == 0:
        # Both images are completely blank — treat as a match
        return 1.0
    return float(intersection) / float(union)


# ── Public interface ──────────────────────────────────────────────────────────

def calculate_accuracy(
    task_name: str,
    source_path: str,
    response_path: str,
) -> bool:
    """
    Compare the model-rendered image against the ground-truth image.

    Parameters
    ----------
    task_name     : e.g. "3_1"  (task id _ question number)
    source_path   : directory containing ground-truth PNGs  (named <task_name>.png)
    response_path : directory containing model-rendered PNGs (named <task_name>.png)

    Returns
    -------
    True if IoU >= ACCURACY_THRESHOLD, False otherwise.
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
        mask_gt   = _load_and_binarise(gt_path)
        mask_pred = _load_and_binarise(pred_path)
        iou = pixel_iou(mask_gt, mask_pred)
        solved = iou >= ACCURACY_THRESHOLD
        print(
            f"[shape_similarity] {task_name}: IoU={iou:.4f} "
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
    Returns the raw IoU float (0.0–1.0) rather than a boolean.
    Useful for analysis / partial credit scoring.
    """
    gt_path   = os.path.join(source_path,   task_name + ".png")
    pred_path = os.path.join(response_path, task_name + ".png")

    if not os.path.exists(gt_path) or not os.path.exists(pred_path):
        return 0.0
    try:
        return pixel_iou(
            _load_and_binarise(gt_path),
            _load_and_binarise(pred_path),
        )
    except Exception:
        return 0.0
