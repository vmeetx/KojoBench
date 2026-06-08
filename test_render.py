from pathlib import Path
from utils.kojo_renderer import render
from PIL import Image
import matplotlib.pyplot as plt

def load(task_num, q_num=1):
    base = Path(__file__).parent / "Tasks" / str(task_num)
    code = (base / "QA" / "code" / f"q{q_num}_code.txt").read_text()
    var_file = base / "variables.txt"
    if var_file.exists():
        for line in var_file.read_text().splitlines():
            line = line.strip()
            if "=" in line:
                name, val = line.split("=", 1)
                code = code.replace("setSpeed(fast)", f"setSpeed(fast)\nval {name.strip()} = {val.strip()}")
    return code

TASK = 1

code = load(TASK)
render(code, "test_generated.png")

def pad_to_square(img, size=500):
    img.thumbnail((size, size))
    padded = Image.new("RGB", (size, size), (255, 255, 255))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    padded.paste(img, offset)
    return padded

ground_truth = pad_to_square(Image.open(f"autotest/source/{TASK}_1.png").convert("RGB"))
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

# Divider line in the middle
fig.add_artist(plt.Line2D([0.5, 0.5], [0.05, 0.95],
               transform=fig.transFigure,
               color="#555555", linewidth=2))

plt.tight_layout(pad=2)
plt.show()
