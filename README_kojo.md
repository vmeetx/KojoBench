# KojoBench

A benchmark for evaluating LLMs on Kojo turtle graphics code generation.
Direct port of [TurtleBench](https://github.com/sinaris76/TurtleBench) from
Python Turtle to **Kojo** (a Scala-based turtle graphics environment used in CS
education).

---

## What this is

TurtleBench tests whether LMMs can look at a geometric image and generate code
that reproduces it.  The original uses Python's `turtle` library.

KojoBench replaces every Python Turtle call with its Kojo equivalent, adds an
embedded API reference in the system prompt (because LLMs have minimal Kojo
training signal), and uses the Kojo online renderer instead of a local Python
sandbox.

This makes the benchmark harder in an interesting way: the model cannot rely on
memorised Python Turtle syntax and must reason from the spec.

---

## File map

```
kojobench/
├── eval_kojo.py            ← main entry point (mirrors eval.py)
├── calculate_score_kojo.py ← rescore saved responses (mirrors calculate_score.py)
├── crawl_tasks.py          ← rebuild dataset.jsonl from Tasks/
├── prompts_kojo.py         ← all prompts with Kojo API reference embedded
├── requirements.txt
│
├── models/
│   └── hf_model.py         ← ★ CONFIGURE THIS — your HF token + model URL
│
├── utils/
│   ├── kojo_runner.py      ← renders Kojo code → PNG via kojo.in API
│   ├── kojo_preprocess.py  ← extracts Kojo code from raw LLM response
│   └── shape_similarity.py ← pixel IoU evaluation (unchanged logic)
│
├── Tasks/                  ← your task data (same structure as TurtleBench)
├── autotest/source/        ← ground-truth PNGs named {id}_{q}.png
└── reports/report.csv      ← auto-created results file
```

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your model

Open `models/hf_model.py` and set:

```python
HF_TOKEN   = "hf_YOUR_TOKEN_HERE"
HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
```

To use a **different model**, change only `HF_API_URL`.  Examples:

| Model | URL |
|---|---|
| Llama 3.1 8B Instruct | `https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct` |
| Qwen2-VL 7B (multimodal) | `https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct` |
| InternVL2-8B (multimodal) | `https://api-inference.huggingface.co/models/OpenGVLab/InternVL2-8B` |
| Your dedicated endpoint | `https://<name>.endpoints.huggingface.cloud` |

For **Together AI / Replicate / OpenAI**: subclass `HFModel` in `models/` and
implement `get_response()` with the same signature.  `eval_kojo.py` only calls
that method.

### 3. Add tasks

Use the same directory structure as TurtleBench:

```
Tasks/
  1/
    description.txt     (optional)
    variables.txt       (e.g. "val radius = 100")
    image/1.png
    result_image/
      q1_image.png
      q2_image.png      (tweak tasks)
    QA/
      code/
        q1_code.txt     (reference Kojo code)
        q2_code.txt
      text/
        q1.txt          ("create the exact same shape.")
        q2.txt          ("make the radius twice as large.")
  2/
    ...
```

Put ground-truth images in `autotest/source/` named `{id}_{q}.png`
(e.g. `1_1.png`, `1_2.png`).

Then rebuild the dataset index:

```bash
python crawl_tasks.py
```

### 4. Run evaluation

```bash
# Simplest: scratch tasks, image only, CoT
python eval_kojo.py

# All options
python eval_kojo.py \
  --task_type   scratch \          # scratch | tweak
  --task_mode   code_generation \  # code_generation | code_edit
  --modalities  image_only \       # image_only | text_only | image+text | image+image
  --prompting_mode cot \           # cot | basic | few-shot
  --save_responses                 # keep raw LLM responses on disk
```

Results are written to `reports/report.csv`.

### 5. Rescore after interruption

```bash
python calculate_score_kojo.py .responses/<run_name>
```

---

## Python Turtle → Kojo command map

| Python Turtle | Kojo |
|---|---|
| `forward(n)` | `forward(n)` |
| `backward(n)` | `back(n)` |
| `right(a)` | `right(a)` |
| `left(a)` | `left(a)` |
| `— (no equivalent)` | `right(a, radius)` — arc |
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
| `for i in range(a,b):` | `repeatFor(a to b) { i => ... }` |
| `def name(): ...` | `def name() { ... }` |
| `— (no equivalent)` | `hop(n)` — forward without drawing |
| `— (no equivalent)` | `savePosHe()` / `restorePosHe()` |

Key differences:
- **No imports** — Kojo builtins are always in scope
- **`repeat(n) { ... }`** is cleaner than Python's `for` loop for turtle patterns
- **Arc drawing** — `right(angle, radius)` and `left(angle, radius)` have no
  direct Python Turtle equivalent (Python requires `circle()`)
- **`hop(n)`** — moves without drawing, putting pen back down after; more
  ergonomic than `penup/forward/pendown`
- **Origin and headings** identical to Python Turtle: (0,0) = centre, 0° = East,
  90° = North

---

## Evaluation metric

Identical to TurtleBench: **pixel-level IoU** between the ground-truth PNG and
the model-rendered PNG, with a **0.95 threshold** for a task to count as solved.

Both images are resized to 500×500, binarised by luminance threshold (< 240 =
drawn pixel), then:

```
IoU = |drawn in both| / |drawn in either|
```

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
        # Call your API here
        ...
        return response_text
```

Then in `eval_kojo.py`, replace:
```python
from models.hf_model import HFModel
model = HFModel()
```
with:
```python
from models.my_model import MyModel
model = MyModel()
```

---

## Notes on the Kojo online renderer

`utils/kojo_runner.py` sends code to `https://kojo.in/api/run`.  The renderer:
- Wraps user code in `cleari(); setSpeed(superFast); ... invisible()`
- Returns a base64 PNG
- Has a 60 s timeout with 3 retries

If the Kojo API changes, update `KOJO_API_URL` in `kojo_runner.py` only.

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
