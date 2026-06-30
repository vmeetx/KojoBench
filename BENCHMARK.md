# KojoBench2 — Benchmark Design Notes

This document covers what we inherited from TurtleBench, what we changed and why, how the scoring metrics were designed, what the LLM actually sees during evaluation, and the steps taken to ensure clean (non-poisoned) evaluation.

---

## 1. Relationship to TurtleBench

[TurtleBench](https://github.com/sinaris76/TurtleBench) (Rismanchian et al., NAACL 2025) is a benchmark for evaluating LLMs on Python Turtle graphics generation from natural language descriptions.

**What we kept:**
- The task descriptions — 75 plain natural-language queries written at roughly grade-6 reading level (e.g. "Draw a star with 5 points", "Draw a house with a triangular roof").
- The benchmark structure: one query per task, one ground-truth image per task.

**What we replaced entirely:**
- The ground-truth code. TurtleBench GT is Python Turtle (`import turtle`, `t.forward()`, `t.circle()`, etc.). We rewrote every GT in Kojo — a Scala-based turtle graphics environment with a different API, different coordinate system, and different drawing primitives. There is no `circle()`, no `begin_fill()`, no `goto()`. The models cannot succeed by recalling Python Turtle idioms.
- The ground-truth images. Since Kojo renders differently (canvas size, stroke width, coordinate origin), we re-rendered every GT script through the Kojo headless JAR to produce new `ground_truth_kojo.png` images. Scoring is always Kojo-render vs Kojo-render.
- The scoring pipeline. TurtleBench uses pixel IoU. We do not (see §3).

**What we deliberately did not keep:**
- Python Turtle imports, `t = turtle.Turtle()` patterns, or any Python-style API in the system prompt or GT code.
- Task IDs from TurtleBench — ours are renumbered 1–75.

The net effect is that a model which memorised TurtleBench Python solutions from its training data gets no direct benefit: the target language is different, the API is different, the rendering environment is different.

---

## 2. Why not IoU

The obvious choice for image comparison in a drawing benchmark is pixel IoU (intersection-over-union of foreground pixels). We tried it and found it unreliable for three reasons specific to this setup:

**Transparent background problem.** Kojo renders to RGBA at 950×700. PIL's `.convert("RGB")` turns transparent pixels black — so the entire canvas is marked "drawn". Raw IoU of two all-black canvases is 1.0.

**Canvas size mismatch.** Our GT images are 863×836 (from the Kojo headless JAR at a given window size), model-rendered images are 950×700. Naive resize to a shared canvas places shapes at different absolute pixel positions, producing near-zero IoU for images that are visually identical shapes.

**Stroke width variance.** The same Kojo code rendered at different speeds or on different JVM versions produces slightly different stroke widths. IoU penalises this as if it were a shape error.

All three problems produce scores that bear no relationship to whether the shape is correct.

---

## 3. NSS — Normalised Shape Similarity

NSS is our replacement for IoU. It makes four changes to handle the issues above:

1. **RGBA compositing.** Before binarising, RGBA images are composited onto a white background. Transparent → white, so only ink pixels are foreground.

2. **Bounding-box crop + resize to 256×256.** Both images are cropped to their content bounding box, then resized to 256×256. This makes the score invariant to canvas size, canvas origin, and absolute position of the shape.

3. **Dilation.** A 12-pixel max-filter is applied to both binary masks before comparing. This makes the score tolerant of stroke-width differences and minor pixel-level offsets.

4. **Composite score.** `NSS = 0.7 × dilated_IoU + 0.3 × edge_correlation`. The edge correlation term is the Pearson r of 16×16 spatial edge histograms computed on the undilated masks — it adds sensitivity to structural shape features (angles, curvature) that dilated IoU can blur over.

**Match threshold.** A task is counted as YES (visually matched) if NSS ≥ 0.65. This threshold was chosen by manual inspection of borderline cases — at 0.65, near-correct shapes pass and clearly wrong shapes fail.

**Excluded tasks.** Tasks {1, 16, 50, 60} are excluded from all scored totals (71 tasks, not 75). These four tasks have rendering characteristics — very large fills, near-blank canvases, or shapes that reduce to single points — where the bounding-box crop or dilation step produces unstable NSS values unrelated to solution quality. They are still in the benchmark folder and the reports; they just do not count toward the headline score.

---

## 4. KCSS — Kojo Code Style Score

TurtleBench had no code quality metric. NSS alone is insufficient for two reasons:

- A model can produce a visually correct shape using Python Turtle commands that happen to be valid Scala identifiers but do nothing in Kojo, then accidentally get lucky. NSS would score it 100%; it should score 0%.
- A model can hard-code 200 `setPosition` calls to trace a shape pixel by pixel. The image matches; the code is not a useful solution.

KCSS penalises the first case, detects the second, and rewards use of idiomatic Kojo patterns. It has three sub-scores:

**Structure (40%)** — binary: 0 if any forbidden pattern is present, 1 otherwise. Forbidden patterns include: `object { }` or `class` wrappers, `def main(...)`, `import` statements, `new`, `extends`, and all Python Turtle command names (`goto`, `circle`, `begin_fill`, `end_fill`, `fd`, `bk`, `rt`, `lt`, `speed`, `color`, `pensize`, `hideturtle`). A single forbidden pattern zeroes this sub-score.

**Idioms (30%)** — fraction of canonical Kojo idioms present. Positive signals: `repeat(n)`, `repeatFor(...)`, arc movement `right(angle, radius)` / `left(angle, radius)`, `hop()`, `savePosHe()` / `restorePosHe()`, parameterised `def` commands.

**Simplicity (30%)** — ratio of model code length to GT code length (excluding boilerplate). A model that writes 10× more lines than the GT for the same shape scores low here, even if NSS is high.

`KCSS = 0.4 × structure + 0.3 × idioms + 0.3 × simplicity`

KCSS is computed on the raw extracted code, not the wrapped `Picture{}` version. It does not penalise code that fails to render — a structurally correct but incomplete answer can still score well on KCSS.

---

## 5. What the LLM sees

Every model — Claude, Qwen, fine-tuned adapter — receives exactly two things per task:

**System message (~1,676 tokens):**
- Role declaration: "You are a Kojo turtle graphics programmer."
- Output format requirement: produce a `<geometry>...</geometry>` section, then Kojo code inside a ` ```scala ``` ` fence. Nothing else.
- Drawing conventions: default position (0,0), heading 90° (North), prefer relative movement, stay within ~500×500 pixels.
- Full Kojo API quick reference: all movement commands, pen commands, colour system, control flow, canvas commands, state save/restore.
- Three worked examples showing correct style (triangle, square with fill, circle via arc).
- Hard prohibitions: no `import`, no classes, no `main()`, no Python Turtle commands, no unavailable commands.
- Response format template showing the expected `<geometry>` structure.

**User message (the query):**
- Plain natural-language description of the shape to draw.
- No Kojo terminology, no hints about which API calls to use, no size hints unless the shape description implies them.
- Example: `"Draw a regular hexagon with six equal sides and angles."`

The system prompt is the same for every task and every model. No task-specific information leaks through it.

**Post-processing pipeline:**
1. Strip `<think>...</think>` blocks (for models that output chain-of-thought).
2. Extract the code between ` ```scala ` and ` ``` ` fences.
3. Strip `clear()`, `cleari()`, `setSpeed(...)`, and `invisible()` lines (these conflict with the Picture wrapper).
4. Wrap in `drawCentered(Picture{ ... })` so the shape is centred on the Kojo canvas.
5. Pass to the Kojo headless JAR (WSL + Java) which renders to PNG.
6. Score the PNG against the GT image using NSS.

---

## 6. Data integrity

**During evaluation, the model never sees:**
- The ground-truth `.kojo` file for any task.
- The ground-truth PNG image for any task.
- Any output from a prior model.
- Any score or ranking hint.

The eval scripts (`eval_engine.py`, `eval_claude_proxy.py`, `eval_lmstudio.py`, `eval_baseline.py`) read only the query file for each task. Ground truth files are read only at scoring time, after the model has already produced its output.

**Claude proxy mode.** Claude's outputs in `runs/claude/` were generated via the Claude API using only the system prompt and query. They were not generated with access to the benchmark folder structure, the GT `.kojo` files, or any prior model results.

**Dataset construction.** The 75 queries were adapted from TurtleBench task descriptions. No KojoBench2 query contains the word "Kojo", any Kojo command name, or any hint about the expected API. The grade-6 framing is intentional — it tests whether the model can translate a plain description into correct Kojo code purely from the system prompt's API reference.

**SFT contamination caveat.** The LoRA adapter in `sft/adapters/qwen-1.5b-kojo-lora/` was trained on the 75 GT (query, Kojo code) pairs from this benchmark. Its eval results are therefore **not** a fair benchmark score — the training data overlaps with the test set. The SFT run exists as a pipeline validation (can the model learn the format and improve at all?) not as a reported benchmark number. Any future fair SFT evaluation would require a held-out task set not present in the training data.

**Scoring independence.** NSS and KCSS are computed from the rendered PNG and extracted code respectively. Neither depends on whether a task was in the SFT training set, nor on which model produced the output. The 4 excluded tasks ({1, 16, 50, 60}) are excluded by scorer reliability, not by any property of model performance on them.
