# KojoBench2

Benchmark for evaluating LLMs on generating [Kojo](https://kogics.net/kojo) turtle-graphics code from natural language descriptions. 75 tasks, automated rendering via WSL, visual accuracy scoring (NSS + KCSS).

Based on [TurtleBench](https://github.com/sinaris76/TurtleBench) — ported from Python Turtle to Kojo (Scala), making it harder since models can't rely on memorised Python syntax.

---

## Results (open in browser after cloning)

| Report | What it shows | File |
|---|---|---|
| **Claude vs GT** | Claude Sonnet 4.6 output vs ground truth, task by task | [`runs/report_claude.html`](runs/report_claude.html) |
| **Qwen vs GT** | Qwen 2.5 Coder 7B output vs ground truth, task by task | [`runs/report_qwen.html`](runs/report_qwen.html) |
| **GT Accuracy Audit** | How faithful our Kojo ground truth is vs original Python images | [`runs/report_gt_audit.html`](runs/report_gt_audit.html) |

Each card: ground truth image on the left, model output on the right, **YES** / **NO** match at a glance.

---

## Just want to see the results?

No setup needed. Clone and open in your browser:

```bash
git clone https://github.com/vmeetx2/KojoBench
```

Then open one of these files directly in your browser:

- `runs/report_claude.html` — Claude Sonnet 4.6 vs Ground Truth
- `runs/report_qwen.html` — Qwen (LM Studio) vs Ground Truth

Each card shows the ground truth shape next to the model's output, with a green **YES** / red **NO** for whether they match (NSS ≥ 65%).

---

## Run it yourself

### 1. Clone and install Python deps

```bash
git clone https://github.com/vmeetx2/KojoBench
cd KojoBench
pip install -r requirements.txt
```

### 2. Set up the Kojo renderer (WSL required — Windows only as-is)

The renderer compiles and runs Kojo code headlessly via WSL.

**Install WSL** if you don't have it:
```bash
wsl --install
```

**Inside WSL**, install Java:
```bash
sudo apt update && sudo apt install -y default-jdk
```

**Install Scala 2.13** inside WSL:
```bash
curl -fL https://github.com/coursier/launchers/raw/master/cs-x86_64-pc-linux.gz | gzip -d > cs
chmod +x cs && ./cs setup
cs install scala:2.13.12 scalac:2.13.12
```
Make sure `scalac` is on your WSL PATH (`which scalac` should return a path).

**Make the runner script executable:**
```bash
wsl chmod +x kojo-headless/run-kojo-headless.sh
```

**Smoke test** — renders task 1 and checks it works:
```bash
python -c "from utils.kojo_renderer import render; ok,err = render('clear(); setSpeed(fast)\nrepeat(4){forward(100);right(90)}', '/tmp/test.png'); print('OK' if ok else err)"
```

### 3. Run Claude (no API key needed — proxy mode)

Claude's outputs are already pre-generated in `runs/claude/`. This just renders and scores them:

```bash
python runs/run.py claude
python runs/make_report.py
```

Then open `runs/report_claude.html`.

### 4. Run Qwen (needs LM Studio)

1. Download [LM Studio](https://lmstudio.ai/)
2. Download and load a Qwen model (e.g. `qwen2.5-coder-7b-instruct`)
3. Start the local server in LM Studio (default: `http://localhost:1234`)
4. Run:

```bash
python runs/run.py qwen
python runs/make_report_qwen.py
```

Then open `runs/report_qwen.html`.

### 5. Run any other LLM

Add a provider to `models/openai_compat.py` or set these env vars and point to any OpenAI-compatible API:

```bash
# .env file (gitignored)
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
```

---

## Benchmark structure

```
benchmark/
└── Task{N}/                   # 75 tasks
    ├── KojoQuery{N}.md        # natural language prompt given to the LLM
    ├── KojoTask{N}.kojo       # ground truth Kojo code
    └── ground_truth_kojo.png  # rendered ground truth image

runs/
├── claude/task{N}.kojo        # Claude's generated code (pre-filled, proxy mode)
├── claude_rendered/           # Claude's rendered PNGs
├── qwen_rendered/             # Qwen's rendered PNGs
├── report_claude.html         # visual comparison report (self-contained)
├── report_qwen.html           # visual comparison report (self-contained)
├── run.py                     # entry point: python runs/run.py [claude|qwen|compare]
├── make_report.py             # generate Claude HTML report
└── make_report_qwen.py        # generate Qwen HTML report
```

---

## Scores

| Model | Avg NSS | YES (≥65%) / 75 |
|---|---|---|
| Claude Sonnet 4.6 (proxy) | 53.6% | 35 / 75 |
| Qwen 2.5 Coder 7B (LM Studio) | — | — |

**NSS** (Normalised Shape Similarity) = `0.7 × shape_overlap + 0.3 × edge_correlation`  
**KCSS** (Kojo Code Style Score) = `0.4 × structure + 0.3 × idioms + 0.3 × simplicity`

---

## Citation

```bibtex
@inproceedings{rismanchian2025turtlebench,
  title     = {TurtleBench: A Visual Programming Benchmark in Turtle Geometry},
  author    = {Rismanchian, Sina and Razeghi, Yasaman and Singh, Sameer and Doroudi, Shayan},
  booktitle = {NAACL},
  year      = {2025}
}
```
