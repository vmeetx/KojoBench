"""
Builds benchmark/Task26 through Task75.
For each task:
  1. Reads archive/Tasks/N/QA/code/q1_code.txt  (Kojo code)
  2. Inlines variables from variables.txt
  3. Wraps in cleari() + Picture{} + drawCentered() format
  4. Generates KojoQuery{N}.md:
       - from description.txt if it exists
       - otherwise calls LM Studio to describe what the code draws
  5. Renders ground_truth_kojo.png via kojo-headless
  6. Writes all files to benchmark/Task{N}/
"""
import re, sys, time
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

from utils.kojo_renderer import render

ARCHIVE   = BASE / "archive" / "Tasks"
BENCHMARK = BASE / "benchmark"
START, END = 26, 75

# ---------- code preparation ------------------------------------------------

_HEADER_RE = re.compile(
    r'^\s*(clear\(\)|cleari\(\)|setSpeed\([^)]*\)|setPenColor\([^)]*\)|invisible\(\))\s*$',
    re.MULTILINE
)

def load_vars(task_dir: Path) -> dict:
    vf = task_dir / "variables.txt"
    if not vf.exists():
        return {}
    out = {}
    for line in vf.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out

def inline_vars(code: str, variables: dict) -> str:
    """Replace bare variable names used as values with their literal."""
    # Insert val bindings at the top instead of string-replacing (safer)
    if not variables:
        return code
    bindings = []
    for k, v in variables.items():
        # Convert list syntax  [a, b, c] -> Array(a, b, c)
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1]
            bindings.append(f"val {k} = Array({inner})")
        else:
            bindings.append(f"val {k} = {v}")
    return "\n".join(bindings) + "\n" + code

def fix_negative_turns(code: str) -> str:
    """Some tasks use right(-angle) which is equivalent to left(angle)."""
    def replace(m):
        angle_expr = m.group(1).strip()
        # Try to evaluate simple negatives: right(-90) -> left(90)
        if angle_expr.startswith("-"):
            return f"left({angle_expr[1:]})"
        return m.group(0)
    return re.sub(r'right\((-[^,)]+)\)', replace, code)

def wrap_for_benchmark(raw_code: str, variables: dict) -> str:
    code = inline_vars(raw_code, variables)
    code = fix_negative_turns(code)
    # Strip canvas-level commands (invalid inside Picture{})
    inner = _HEADER_RE.sub("", code).strip()
    lines = inner.splitlines()
    indented = "\n".join("    " + l for l in lines)
    return f"cleari()\n\ndef shape = Picture {{\n{indented}\n}}\n\ndrawCentered(shape)\n"

# ---------- query generation ------------------------------------------------

_LM_SYSTEM = (
    "You are given Kojo turtle graphics code. "
    "Describe in ONE short sentence (max 20 words) what shape or drawing this code produces. "
    "Start with 'Draw a' or 'Draw'. "
    "Be specific about the shape, count, and arrangement. "
    "No code, no technical terms, no explanation — just the description."
)

def generate_query_from_code(code: str, variables: dict, task_id: int) -> str:
    try:
        from models.openai_compat import OpenAICompatModel
        model = OpenAICompatModel(provider="lmstudio", max_tokens=60, temperature=0.0)
        var_hint = ", ".join(f"{k}={v}" for k, v in variables.items())
        user_msg = f"Variables: {var_hint}\n\nKojo code:\n```\n{code[:800]}\n```"
        response = model.get_response(_LM_SYSTEM, user_msg)
        # Extract first sentence
        first = response.strip().split("\n")[0].strip()
        if first and len(first) > 5:
            return first
    except Exception as e:
        print(f"    [LM Studio] task {task_id} query gen failed: {e}")
    # Fallback: use variable names as hint
    if variables:
        shape_hint = list(variables.keys())[0].replace("_", " ").replace("side", "").strip()
        return f"Draw a shape with {shape_hint}."
    return f"Draw a geometric shape (task {task_id})."

def make_query_grade6(raw_desc: str) -> str:
    """Simplify a technical description into grade-6 plain English."""
    # Just capitalise and add "Draw a" prefix if needed
    s = raw_desc.strip().rstrip(".")
    if not s.lower().startswith("draw"):
        s = "Draw " + s[0].lower() + s[1:]
    return s + "."

# ---------- main loop -------------------------------------------------------

def build_task(task_id: int, force: bool = False) -> bool:
    src     = ARCHIVE / str(task_id)
    dest    = BENCHMARK / f"Task{task_id}"
    code_f  = src / "QA" / "code" / "q1_code.txt"
    desc_f  = src / "description.txt"
    gt_png  = dest / "ground_truth_kojo.png"
    kojo_f  = dest / f"KojoTask{task_id}.kojo"
    query_f = dest / f"KojoQuery{task_id}.md"

    if not code_f.exists():
        print(f"  Task {task_id}: SKIP — no q1_code.txt")
        return False

    dest.mkdir(parents=True, exist_ok=True)

    raw_code  = code_f.read_text(encoding="utf-8")
    variables = load_vars(src)

    # 1. Wrap code
    kojo_code = wrap_for_benchmark(raw_code, variables)
    kojo_f.write_text(kojo_code, encoding="utf-8")

    # 2. Query
    if not query_f.exists() or force:
        if desc_f.exists():
            raw_desc = desc_f.read_text(encoding="utf-8").strip()
            query    = make_query_grade6(raw_desc)
        else:
            print(f"  Task {task_id}: generating query via LM Studio...", end=" ", flush=True)
            query = generate_query_from_code(raw_code, variables, task_id)
            print(f"'{query[:60]}'")
        query_f.write_text(query, encoding="utf-8")
    else:
        query = query_f.read_text(encoding="utf-8").strip()

    # 3. Render
    if not gt_png.exists() or force:
        ok, err = render(kojo_code, str(gt_png))
        status = "ok" if ok else f"FAILED: {err[:80]}"
    else:
        ok, status = True, "cached"

    print(f"  Task {task_id}: render={status}  query='{query[:55]}'")
    return ok

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", type=int,
                        default=list(range(START, END + 1)))
    parser.add_argument("--force", action="store_true",
                        help="Re-render and re-generate even if files exist")
    args = parser.parse_args()

    ok_count = 0
    for t in args.tasks:
        try:
            ok = build_task(t, force=args.force)
            if ok:
                ok_count += 1
        except Exception as e:
            print(f"  Task {t}: ERROR — {e}")
        time.sleep(0.2)

    print(f"\nDone: {ok_count}/{len(args.tasks)} tasks built successfully.")
    print(f"Benchmark now has Tasks 1-{max(args.tasks)}.")

if __name__ == "__main__":
    main()
