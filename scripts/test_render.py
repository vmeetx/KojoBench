import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.kojo_renderer import render
from PIL import Image
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent   # repo root

def load(task_num, q_num=1):
    base = ROOT / "Tasks" / str(task_num)
    code = (base / "QA" / "code" / f"q{q_num}_code.txt").read_text()
    var_file = base / "variables.txt"
    if var_file.exists():
        for line in var_file.read_text().splitlines():
            line = line.strip()
            if "=" in line:
                name, val = line.split("=", 1)
                code = code.replace("setAnimationDelay(0)", f"setAnimationDelay(0)\nval {name.strip()} = {val.strip()}")
    return code

TASKS = range(1, 11)  # change to range(1, 2) for a single task, or list e.g. [1, 5, 90]


def pad_to_square(img, size=500):
    img.thumbnail((size, size))
    padded = Image.new("RGB", (size, size), (255, 255, 255))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    padded.paste(img, offset)
    return padded


for TASK in TASKS:
    gt_path = f"autotest/source/{TASK}_1.png"
    if not Path(gt_path).exists():
        print(f"Task {TASK}: no ground truth, skipping")
        continue

    render(load(TASK), "test_generated.png")

    ground_truth = pad_to_square(Image.open(gt_path).convert("RGB"))
    generated    = pad_to_square(Image.open("test_generated.png").convert("RGB"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    fig.canvas.manager.set_window_title(f"KojoBench — Task {TASK}")
    fig.patch.set_facecolor("#1e1e1e")

    for ax, img, title in [(ax1, ground_truth, "Ground Truth"), (ax2, generated, "Generated")]:
        ax.imshow(img)
        ax.set_title(title, fontsize=14, color="white", pad=10)
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.add_artist(plt.Line2D([0.5, 0.5], [0.05, 0.95],
                   transform=fig.transFigure,
                   color="#555555", linewidth=2))

    plt.tight_layout(pad=2)
    plt.show()  # blocks until you close the window, then moves to next task
