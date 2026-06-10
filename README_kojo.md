# KojoBench

Benchmark and dataset for evaluating LLMs on generating [Kojo](https://kogics.net/kojo) turtle-graphics code from natural language descriptions, with automated rendering and visual accuracy scoring.

Based on [TurtleBench](https://github.com/sinaris76/TurtleBench) — every Python Turtle task has been ported to Kojo (a Scala-based turtle graphics environment used in CS education). This makes the benchmark harder in an interesting way: models cannot rely on memorised Python syntax and must reason from a Kojo-specific reference.

---

## File map

Every file in one line.

```
KojoBench/
│
├── README_kojo.md                ← this file
├── requirements.txt              ← Python dependencies
├── .gitignore
│
├── eval/                         ← evaluation pipeline (run from repo root)
│   ├── eval_kojo.py              ← main entry point: run LLM eval on all tasks
│   ├── calculate_score_kojo.py   ← re-score saved responses after an interruption
│   ├── audit_tasks.py            ← render all reference Kojo code, report IoU failures
│   └── audit_kojobench.py        ← visual audit for KojoNewDataset with NSS scoring
│
├── scripts/                      ← one-off utility scripts
│   ├── build_new_dataset.py      ← generate KojoNewDataset/ from Tasks 1-10
│   ├── convert_to_kojo.py        ← convert Python Turtle reference code → Kojo
│   ├── crawl_tasks.py            ← rebuild dataset.jsonl by crawling Tasks/
│   └── test_render.py            ← visual smoke test: ground truth vs generated side-by-side
│
├── models/                       ← LLM wrappers (one per provider)
│   └── hf_model.py               ← HuggingFace Inference API wrapper (text + multimodal)
│
├── utils/                        ← shared library imported by eval and scripts
│   ├── kojo_renderer.py          ← renders Kojo code → PNG via WSL + local JAR (with cache)
│   ├── kojo_preprocess.py        ← strips markdown/boilerplate from raw LLM responses
│   ├── shape_similarity.py       ← pixel IoU metric used by the original pipeline
│   └── prompts_kojo.py           ← system + user prompts with embedded Kojo syntax reference
│
├── kojo-headless/                ← Kojo headless runner
│   ├── kojo-lib-assembly-0.3.3.jar   ← Kojo runtime JAR (Scala)
│   └── run-kojo-headless.sh      ← shell script: compiles + runs a .kojo file → PNG
│
├── Tasks/                        ← raw task data (130+ tasks, TurtleBench format)
│   └── {N}/
│       ├── description.txt       ← natural language description of the shape
│       ├── variables.txt         ← e.g. "radius = 100"
│       ├── image/{N}.png         ← ground truth shape image
│       ├── result_image/         ← variant images (q1–q4)
│       └── QA/code/
│           ├── q1_code.txt       ← reference Kojo code for question 1
│           └── q1_code.py_orig   ← original Python Turtle code (backup)
│
├── KojoNewDataset/               ← formatted dataset for training / evaluation
│   └── Task{N}/                  ← Tasks 1-10, each containing:
│       ├── KojoQuery{N}.md       ← student-style natural language prompt
│       ├── KojoTask{N}.kojo      ← reference Kojo solution
│       ├── TurtleTask{N}.py      ← equivalent Python Turtle solution
│       ├── ground_truth.png      ← canonical shape image
│       └── generated.png         ← image rendered from KojoTask{N}.kojo
│
├── autotest/source/              ← ground-truth PNGs for the main eval pipeline
│   └── {id}_{q}.png              ← e.g. 1_1.png, 3_2.png
│
└── .render_cache/                ← SHA-256 keyed PNG cache (auto-managed, gitignored)
```

---

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up the renderer

The renderer runs headlessly via WSL — no internet needed at render time.

**Install WSL with Java and Scala 2.13:**
```bash
sudo apt install default-jdk
# Install Scala 2.13 and add its bin/ to PATH
```

**Verify the JAR and script are in place:**
```
kojo-headless/kojo-lib-assembly-0.3.3.jar
kojo-headless/run-kojo-headless.sh
```

**Smoke test** (renders task 1 and shows ground truth vs generated):
```bash
python scripts/test_render.py
```

### 3. Configure your model

Set credentials as environment variables — never hardcode them:

```bash
export HF_TOKEN=hf_...
export HF_API_URL=https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct
```

Or add a `.env` file in the repo root (already gitignored):
```
HF_TOKEN=hf_...
HF_API_URL=https://...
```

**Supported model URLs:**

| Model | HF_API_URL |
|---|---|
| Llama 3.1 8B Instruct | `https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct` |
| Qwen2-VL 7B (multimodal) | `https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct` |
| InternVL2-8B (multimodal) | `https://api-inference.huggingface.co/models/OpenGVLab/InternVL2-8B` |
| Dedicated endpoint | `https://<name>.endpoints.huggingface.cloud` |

For other providers (Together AI, Replicate, OpenAI): subclass `HFModel` in `models/` and implement `get_response()` with the same signature — `eval_kojo.py` only calls that method.

---

## Workflows

### Run an LLM evaluation

```bash
# All defaults (scratch tasks, image only, CoT)
python eval/eval_kojo.py

# Full options
python eval/eval_kojo.py \
  --task_type      scratch \         # scratch | tweak
  --task_mode      code_generation \ # code_generation | code_edit
  --modalities     image_only \      # image_only | text_only | image+text | image+image
  --prompting_mode cot \             # cot | basic | few-shot
  --save_responses                   # save raw LLM responses to .responses/
```

Results are written to `reports/report.csv`.

### Re-score after interruption

```bash
python eval/calculate_score_kojo.py .responses/<run_name>
```

### Audit reference Kojo code (main task set)

Renders every reference code file, reports IoU against ground truth, auto-retries conversion on failures:

```bash
python eval/audit_tasks.py
python eval/audit_tasks.py --task 5   # single task
```

### Visual audit of KojoNewDataset

Opens a window showing ground truth vs generated for all 10 tasks with NSS scores:

```bash
python eval/audit_kojobench.py
python eval/audit_kojobench.py --task 3   # single task
```

### Rebuild KojoNewDataset from scratch

Regenerates all files in `KojoNewDataset/` (converts code, renders images):

```bash
python scripts/build_new_dataset.py
```

### Convert Python Turtle reference code → Kojo

Safe to re-run — backs up originals as `*.py_orig`:

```bash
python scripts/convert_to_kojo.py
```

### Rebuild dataset index

```bash
python scripts/crawl_tasks.py
```

---

## Evaluation metrics

### NSS — Normalised Shape Similarity (KojoNewDataset)

Used by `eval/audit_kojobench.py`. Fixes the main weakness of raw IoU (position sensitivity):

1. Both images are binarised (drawn vs. white background), including correct RGBA handling.
2. Each is cropped to its content bounding box and resized to a 256×256 thumbnail — removing canvas-position differences.
3. Both thumbnails are dilated uniformly (MaxFilter 9px) so that thick hand-drawn strokes and thin computer-drawn strokes overlap meaningfully.
4. **NSS-IoU**: IoU on the dilated thumbnails.
5. **Edge-corr**: Pearson correlation of a 16×16 spatial histogram of drawn pixels — captures whether the layout of the shape matches.

```
Final score = 0.7 × NSS-IoU + 0.3 × Edge-corr
```

### Pixel IoU (main pipeline)

Used by `eval/eval_kojo.py` and `eval/audit_tasks.py`. Identical to TurtleBench:

```
IoU = |drawn in both| / |drawn in either|
```

Both images resized to 500×500, luminance threshold < 240 = drawn pixel. Task solved if IoU ≥ 0.95.

---

## Python Turtle → Kojo command map

| Python Turtle | Kojo |
|---|---|
| `forward(n)` | `forward(n)` |
| `backward(n)` | `back(n)` |
| `right(a)` | `right(a)` |
| `left(a)` | `left(a)` |
| `t.circle(r)` | `left(360, r)` — full circle arc |
| `t.circle(r, a)` | `left(a, r)` — partial arc |
| `penup()` | `penUp()` |
| `pendown()` | `penDown()` |
| `goto(x, y)` | `setPosition(x, y)` |
| `setheading(a)` | `setHeading(a)` |
| `pensize(n)` | `setPenThickness(n)` |
| `pencolor(c)` | `setPenColor(c)` |
| `fillcolor(c)` | `setFillColor(c)` |
| `bgcolor(c)` | `setBackground(c)` |
| `speed(n)` | `setSpeed(slow\|medium\|fast\|superFast)` |
| `hideturtle()` | `invisible()` |
| `for i in range(n):` | `repeat(n) { ... }` |
| `for i in range(a, b):` | `repeatFor(a to b) { i => ... }` |
| `def f(): ...` | `def f() { ... }` |
| *(no equivalent)* | `hop(n)` — move without drawing |
| *(no equivalent)* | `savePosHe()` / `restorePosHe()` |

**Key differences:**
- No imports — Kojo builtins are always in scope.
- `setHeading(0)` is required at the start; Kojo's default heading is 90° (North), not 0° (East).
- `repeat(n) { ... }` replaces Python's `for` loop for turtle patterns.
- Arc drawing: `right(angle, radius)` / `left(angle, radius)` — more explicit than Python's `circle()`.
- `hop(n)` moves without drawing (pen auto-restores after).

---

## Adding a new model

Create `models/my_model.py`:

```python
class MyModel:
    def get_response(
        self,
        system_message: str,
        user_message: str,
        base_image: str | None = None,
        result_image: str | None = None,
        few_shot: bool = False,
    ) -> str:
        ...
        return response_text
```

Then in `eval/eval_kojo.py` swap:
```python
from models.hf_model import HFModel
model = HFModel()
```
for:
```python
from models.my_model import MyModel
model = MyModel()
```

---

## Citation

If you use this benchmark, please also cite the original TurtleBench paper:

```bibtex
@inproceedings{rismanchian2025turtlebench,
  title     = {TurtleBench: A Visual Programming Benchmark in Turtle Geometry},
  author    = {Rismanchian, Sina and Razeghi, Yasaman and Singh, Sameer and Doroudi, Shayan},
  booktitle = {NAACL},
  year      = {2025}
}
```
