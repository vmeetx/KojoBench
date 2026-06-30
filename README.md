# KojoBench2

Benchmark for evaluating LLMs on generating [Kojo](https://kogics.net/kojo) turtle-graphics code from natural language descriptions. 71 scored tasks, automated headless rendering via WSL/Java, and two complementary scoring metrics (visual shape similarity + code quality).

Based on [TurtleBench](https://github.com/sinaris76/TurtleBench) — ported from Python Turtle to Kojo (Scala), which makes it harder: models can't rely on memorised Python turtle syntax, and the API differs enough that rote translation fails.

For full design rationale — what we kept from TurtleBench, why we replaced IoU, how NSS and KCSS work, what the LLM sees, and data integrity guarantees — see [BENCHMARK.md](BENCHMARK.md).

---

## Scores

| Model | Variant | Avg NSS | YES (≥65%) / 71 | Avg KCSS |
|---|---|---|---|---|
| Claude Sonnet 4.6 | API (proxy) | **71.1%** | **49 / 71** | 81.2% |
| Qwen 2.5 Coder 7B | LM Studio, 4-bit | 20.6% | 6 / 71 | 77.6% |
| Qwen 2.5 Coder 1.5B | HF direct, 4-bit NF4 | 22.1%* | 4 / 30* | ~70% |
| Qwen 2.5 Coder 1.5B + LoRA | SFT on GT (3 epochs) | — | sanity only† | — |

\* Partial run (30/71 tasks with renderable output scored).  
† LoRA adapter produces correct `<geometry>` + ` ```scala ` format on Task 1. Full eval pending.

**NSS** (Normalised Shape Similarity) = `ar_penalty × (0.7 × chamfer_score + 0.3 × edge_correlation)`  
**KCSS** (Kojo Code Style Score) = `0.4 × structure + 0.3 × idioms + 0.3 × simplicity`  
4 tasks excluded as scorer blind spots: {1, 16, 50, 60}.

---

## Reports (open in browser after cloning)

| Report | Contents |
|---|---|
| [`runs/reports/report_claude.html`](runs/reports/report_claude.html) | Claude Sonnet 4.6 vs GT, all 71 tasks |
| [`runs/reports/report_qwen.html`](runs/reports/report_qwen.html) | Qwen 2.5 Coder 7B vs GT, all 71 tasks |
| [`sft/reports/training_report.html`](sft/reports/training_report.html) | LoRA SFT run — loss curves, metrics table, sanity check |

Each eval card: ground truth image on the left, model output on the right, green **YES** / red **NO** based on NSS ≥ 65%.

---

## Just want to see the results?

Clone and open the HTML files directly in your browser — no server needed, everything is self-contained:

```bash
git clone https://github.com/vmeetx2/KojoBench
```

---

## Repo structure

```
KojoBench/
├── benchmark/
│   └── Task{N}/                   # 75 tasks (71 scored, 4 excluded)
│       ├── KojoQuery{N}.md        # natural language prompt
│       ├── KojoTask{N}.kojo       # ground truth Kojo code
│       └── ground_truth_kojo.png  # rendered GT image
│
├── eval/
│   └── eval_kojobench2.py         # system prompt + eval entry point (Java deps)
│
├── runs/                          # benchmark eval pipeline
│   ├── eval_engine.py             # shared scoring harness (NSS, KCSS, renderer)
│   ├── eval_claude_proxy.py       # score pre-generated Claude outputs
│   ├── eval_lmstudio.py           # call Qwen via LM Studio API + score
│   ├── compare_ui.py              # side-by-side GT / Claude / Qwen window
│   ├── make_report.py             # generate Claude HTML report
│   ├── make_report_qwen.py        # generate Qwen HTML report
│   ├── run.py                     # entry point: python runs/run.py [claude|qwen|compare]
│   ├── claude/                    # Claude's .kojo responses (pre-filled)
│   ├── claude_rendered/           # Claude's rendered PNGs
│   ├── qwen/                      # Qwen's .kojo responses
│   ├── qwen_rendered/             # Qwen's rendered PNGs
│   └── reports/                   # all HTML/PDF output
│       ├── report_claude.html
│       └── report_qwen.html
│
├── sft/                           # fine-tuning pipeline
│   ├── train_lora.py              # LoRA SFT: data -> training -> adapter save -> sanity check
│   ├── eval_baseline.py           # base model eval (HF direct, --model flag)
│   ├── adapters/
│   │   └── qwen-1.5b-kojo-lora/  # saved LoRA adapter (Qwen 1.5B, 3 epochs)
│   ├── data/
│   │   └── dataset.jsonl          # exported training data
│   ├── logs/                      # training CSV logs
│   ├── notebooks/
│   │   └── kojo_sft.ipynb
│   ├── reports/
│   │   └── training_report.html   # loss curves, perplexity, sanity check output
│   └── results/
│       └── qwen-1.5b-base/        # 1.5B baseline rendered outputs
│
├── utils/
│   ├── kojo_renderer.py           # headless Kojo renderer (calls kojo-headless JAR)
│   ├── shape_similarity.py        # NSS scorer
│   ├── kojo_code_quality.py       # KCSS scorer
│   └── kojo_preprocess.py
│
├── models/
│   └── openai_compat.py           # OpenAI-compatible client (Claude, Groq, LM Studio)
│
├── kojo-headless/                 # Scala/Java renderer (prebuilt JAR + WSL runner)
│   └── kojo-lib-assembly-0.3.3.jar
│
└── scripts/                       # dataset construction and audit scripts
```

---

## Run it yourself

### Prerequisites

**Python deps:**
```bash
pip install -r requirements.txt
```

**Kojo renderer** (required for all eval — renders Kojo code to PNG):

WSL must be installed. Inside WSL:
```bash
sudo apt update && sudo apt install -y default-jdk
# Install Scala 2.13
curl -fL https://github.com/coursier/launchers/raw/master/cs-x86_64-pc-linux.gz | gzip -d > cs
chmod +x cs && ./cs setup
cs install scala:2.13.12 scalac:2.13.12
wsl chmod +x kojo-headless/run-kojo-headless.sh
```

Smoke test:
```bash
python -c "from utils.kojo_renderer import render; ok,e = render('repeat(4){forward(100);right(90)}', '/tmp/t.png'); print('OK' if ok else e)"
```

---

### Score Claude (no API key needed)

Claude's outputs are pre-generated in `runs/claude/`. This just renders and scores them:

```bash
python runs/run.py claude
python runs/make_report.py
# open runs/reports/report_claude.html
```

---

### Score Qwen via LM Studio

1. Download [LM Studio](https://lmstudio.ai/), load `qwen2.5-coder-7b-instruct`
2. Start the local server (default `http://localhost:1234`)

```bash
python runs/run.py qwen
python runs/make_report_qwen.py
# open runs/reports/report_qwen.html
```

---

### Run any HF model directly (no LM Studio)

Requires a CUDA GPU. Loads the model in 4-bit NF4 and runs inference directly:

```bash
# 1.5B — fits on 6GB VRAM
python sft/eval_baseline.py --no-window

# Any other HF model
python sft/eval_baseline.py --model Qwen/Qwen2.5-Coder-7B-Instruct --no-window

# Resume a paused run
python sft/eval_baseline.py --start 54 --skip-existing --no-window
```

Results land in `sft/results/<model-slug>/`.

---

### LoRA Fine-tuning (SFT)

Trains a LoRA adapter on the 75 KojoBench2 ground-truth examples. Uses 4-bit NF4 + gradient checkpointing — fits on 6GB VRAM.

```bash
pip install -r sft/requirements.txt
python sft/train_lora.py
```

What it does:
- Splits data 80/20 (60 train / 15 val) with seed 42
- Trains for up to 5 epochs with early stopping (patience=2)
- Logs train loss, val loss, and perplexity after every epoch
- Saves best checkpoint by val loss to `sft/adapters/<model>/`

**PoC results** (Qwen 2.5 Coder 1.5B, RTX 3050 6GB, 23 min):

| Epoch | Train loss | Train PPL | Val loss | Val PPL |
|---|---|---|---|---|
| 1 | ~0.35 | ~1.42 | — | — |
| 2 | ~0.21 | ~1.23 | — | — |
| 3 | 0.15 | 1.16 | — | — |

Final train loss 0.29, token accuracy 94.9%. Adapter produces correct `<geometry>` + ` ```scala ` format on Task 1 inference.

> **Note:** This is a pipeline validation run, not a fair generalisation test. The adapter is trained on the benchmark's own ground truth — a proper evaluation would require a held-out task set.

---

### API keys

Required for Claude proxy mode. Store in `.env` (gitignored):

```bash
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...          # optional, for Groq-hosted models
```

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
