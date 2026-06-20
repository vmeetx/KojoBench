"""
colab_run.py
------------
Standalone script for running KojoBench2 tasks 11-25 on a reasoning model
via Groq's free API. Prints the full thinking trace + generated code per task.
No Kojo rendering needed — just model evaluation.

Colab setup:
    !pip install groq
    # Set GROQ_API_KEY in Colab Secrets (left sidebar → key icon)

    import os
    from google.colab import userdata
    os.environ["GROQ_API_KEY"] = userdata.get("GROQ_API_KEY")

Get a free Groq API key at: console.groq.com
Model used: deepseek-r1-distill-llama-70b (returns reasoning_content separately)
"""

import os
import re
import time
from pathlib import Path

try:
    from groq import Groq
except ImportError:
    raise ImportError("pip install groq")

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_MODEL  = "qwen-qwq-32b"
TASKS       = list(range(1, 11))           # tasks 1-10
SLEEP_S     = 10                           # seconds between calls (rate limit buffer)
MAX_RETRIES = 4                            # retries on rate-limit (429)
DATASET_DIR = Path(__file__).parent / "KojoBench2"

# ── System prompt (condensed for rate limit efficiency) ───────────────────────
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
_FENCE_RE = re.compile(r'```(?:scala|kojo)?\s*(.*?)```', re.DOTALL)

def extract_code(text: str) -> str:
    m = _FENCE_RE.search(text)
    return m.group(1).strip() if m else ""

def print_divider(task_id: int, query: str):
    print("\n" + "=" * 70)
    print(f"  TASK {task_id}")
    print(f"  {query}")
    print("=" * 70)

def print_thinking(thinking: str):
    if not thinking:
        return
    lines = thinking.strip().splitlines()
    # Show first 20 lines of thinking to keep output readable
    preview = lines[:20]
    print("\n[THINKING]")
    for line in preview:
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


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("Set GROQ_API_KEY in environment or Colab Secrets.")

    client = Groq(api_key=api_key)
    print(f"Model: {GROQ_MODEL}")
    print(f"Tasks: {TASKS}")
    print(f"Sleep between calls: {SLEEP_S}s\n")

    for task_id in TASKS:
        task_dir   = DATASET_DIR / f"Task{task_id}"
        query_file = task_dir / f"KojoQuery{task_id}.md"

        if not query_file.exists():
            print(f"\nTask {task_id}: no query file, skipping")
            continue

        query = query_file.read_text(encoding="utf-8").strip()
        print_divider(task_id, query)

        response = None
        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": query},
                    ],
                    max_tokens=6000,
                    temperature=0.0,
                )
                break  # success
            except Exception as e:
                err = str(e)
                is_rate_limit = "429" in err or "rate_limit" in err.lower() or "rate limit" in err.lower()
                wait = (2 ** attempt) * 30 if is_rate_limit else SLEEP_S * 2
                print(f"\n  {'RATE LIMITED' if is_rate_limit else 'ERROR'} (attempt {attempt+1}/{MAX_RETRIES}): {err[:80]}")
                print(f"  Waiting {wait}s before retry...")
                time.sleep(wait)

        if response is None:
            print(f"\n  Task {task_id}: all retries failed, skipping")
            continue

        msg      = response.choices[0].message
        thinking = getattr(msg, "reasoning_content", None) or ""
        content  = msg.content or ""
        code     = extract_code(content)

        print_thinking(thinking)
        print_code(code)

        # Usage summary
        u = response.usage
        print(f"\n  [tokens] prompt={u.prompt_tokens}  completion={u.completion_tokens}  total={u.total_tokens}")

        # Save full response
        task_dir.mkdir(exist_ok=True)
        full = f"<think>\n{thinking}\n</think>\n\n{content}" if thinking else content
        (task_dir / "llm_response.txt").write_text(full, encoding="utf-8")
        if code:
            (task_dir / "llm_generated_raw.py").write_text(code, encoding="utf-8")
        print(f"  Saved → {task_dir}/llm_response.txt")

        time.sleep(SLEEP_S)

    print("\n\nDone.")


if __name__ == "__main__":
    main()
