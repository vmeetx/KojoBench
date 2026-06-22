"""
colab_run.py
------------
Run KojoBench2 tasks against any OpenAI-compatible reasoning model API.
Prints thinking trace + generated code per task. No Kojo rendering needed.

Colab setup:
    !pip install openai
    import os
    os.environ["GROQ_API_KEY"] = "your-key-here"

    # Then run:  !python colab_run.py

Provider presets (set the matching env var):
    Groq        →  GROQ_API_KEY       (default, model: qwen/qwen3-32b)
    Together    →  TOGETHER_API_KEY
    OpenRouter  →  OPENROUTER_API_KEY
    LM Studio   →  (no key needed, runs locally)

Override any value:
    MODEL_BASE_URL / MODEL_API_KEY / MODEL_NAME
"""

import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from models.openai_compat import OpenAICompatModel, PROVIDERS

# ── Config ────────────────────────────────────────────────────────────────────
PROVIDER   = os.environ.get("PROVIDER", "groq")
MODEL_NAME = os.environ.get("MODEL_NAME", "qwen/qwen3-32b")
TASKS      = list(range(1, 11))    # tasks 1-10
SLEEP_S    = 10                    # seconds between calls
MAX_RETRIES = 4

DATASET_DIR = Path(__file__).parent / "benchmark"

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a Kojo turtle graphics programmer.
Write Kojo code that draws exactly what the user describes.

First produce a short <geometry> section describing your approach.
Then output the drawing commands inside a ```scala ... ``` fence.

Rules:
- Kojo starts at (0,0) heading North (90°). 0°=East, 90°=North, 180°=West, 270°=South.
- right(angle) turns CLOCKWISE. left(angle) turns counter-clockwise.
- right(angle, radius) / left(angle, radius) — arc movement.
- repeat(n) { ... } — loop. hop(n) — move without drawing.
- Do NOT use: import, class, object, def main, goto, circle, begin_fill, pensize.
- Do NOT wrap in object/class. Write top-level drawing commands only.
- Start code with: clear()\nsetSpeed(fast)

Examples:
  // circle radius 50:
  right(360, 50)

  // equilateral triangle side 100:
  repeat(3) { forward(100); right(120) }

  // square:
  repeat(4) { forward(100); right(90) }

  // hexagon:
  repeat(6) { forward(80); right(60) }
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
_FENCE_RE   = re.compile(r'```(?:scala|kojo)?\s*(.*?)```', re.DOTALL)
_THINK_RE   = re.compile(r'<think>(.*?)</think>', re.DOTALL)

def extract_code(text: str) -> str:
    m = _FENCE_RE.search(text)
    return m.group(1).strip() if m else ""

def split_thinking(text: str) -> tuple[str, str]:
    """Return (thinking, rest) splitting on <think>...</think>."""
    m = _THINK_RE.search(text)
    if m:
        return m.group(1).strip(), text[m.end():].strip()
    return "", text

def print_divider(task_id: int, query: str):
    print("\n" + "=" * 70)
    print(f"  TASK {task_id}")
    print(f"  {query}")
    print("=" * 70)

def print_thinking(thinking: str):
    if not thinking:
        return
    lines = thinking.strip().splitlines()
    print("\n[THINKING]")
    for line in lines[:20]:
        print(f"  {line}")
    if len(lines) > 20:
        print(f"  ... ({len(lines) - 20} more lines)")

def print_code(code: str):
    if not code:
        print("\n[CODE]  (none extracted)")
        return
    print("\n[CODE]")
    for line in code.splitlines():
        print(f"  {line}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    model = OpenAICompatModel(
        provider=PROVIDER,
        model=MODEL_NAME,
        max_tokens=2048,
        temperature=0.0,
    )
    print(f"Tasks: {TASKS}  sleep: {SLEEP_S}s\n")

    for task_id in TASKS:
        task_dir   = DATASET_DIR / f"Task{task_id}"
        query_file = task_dir / f"KojoQuery{task_id}.md"

        if not query_file.exists():
            print(f"\nTask {task_id}: no query file, skipping")
            continue

        query = query_file.read_text(encoding="utf-8").strip()
        print_divider(task_id, query)

        raw_response = None
        for attempt in range(MAX_RETRIES):
            try:
                raw_response = model.get_response(SYSTEM_PROMPT, query)
                break
            except Exception as e:
                err = str(e)
                is_rate_limit = "429" in err or "rate_limit" in err.lower() or "rate limit" in err.lower()
                wait = (2 ** attempt) * 30 if is_rate_limit else SLEEP_S * 2
                print(f"\n  {'RATE LIMITED' if is_rate_limit else 'ERROR'} (attempt {attempt+1}/{MAX_RETRIES}): {err[:120]}")
                print(f"  Waiting {wait}s...")
                time.sleep(wait)

        if raw_response is None:
            print(f"\n  Task {task_id}: all retries failed, skipping")
            continue

        thinking, content = split_thinking(raw_response)
        code = extract_code(content) or extract_code(raw_response)

        print_thinking(thinking)
        print_code(code)

        task_dir.mkdir(exist_ok=True)
        (task_dir / "llm_response.txt").write_text(raw_response, encoding="utf-8")
        if code:
            (task_dir / "llm_generated.kojo").write_text(code, encoding="utf-8")
        print(f"\n  Saved → {task_dir}/llm_response.txt")

        time.sleep(SLEEP_S)

    print("\n\nDone.")


if __name__ == "__main__":
    main()
