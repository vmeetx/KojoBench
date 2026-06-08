#!/usr/bin/env python3
"""
convert_to_kojo.py

Rewrites Tasks/*/QA/code/q*_code.txt from Python Turtle to Kojo Level 1 syntax.
Always reads from *.py_orig backups when they exist so re-runs are idempotent.

Run from anywhere:
    python convert_to_kojo.py
"""

import re
from pathlib import Path

ROOT      = Path(__file__).parent
TASKS_DIR = ROOT / "Tasks"

INT_PARAM_NAMES = {"sides", "n", "count", "level", "depth", "times", "num", "steps"}

# setHeading(0) = East, matching Python turtle's default heading
HEADER = "clear()\nsetSpeed(fast)\nsetHeading(0)\n"

# ── Patterns for lines to drop entirely ───────────────────────────────────────

SKIP_RES = [re.compile(p) for p in [
    r"^\s*(from|import)\s+",
    r"^\s*(t\s*=\s*)?(turtle\.(Turtle|Screen|done|mainloop|bye)\b|Turtle\s*\()",
    r"^\s*t\.(done|mainloop|bye)\(\)",
    r"^\s*(screen|wn)\s*=",
    r"^\s*print\s*\(",
    r"^\s*t\.(begin_fill|end_fill)\(\)",
    r"^\s*if\s+__name__\s*==\s*[\"']__main__[\"']",
]]


def should_skip(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("#"):
        return True
    return any(p.match(line) for p in SKIP_RES)


# ── Argument parsing helpers ───────────────────────────────────────────────────

def extract_call_args(line: str, func: str) -> str | None:
    """Return the raw args string inside func(...), or None if not found."""
    m = re.search(re.escape(func) + r"\(", line)
    if not m:
        return None
    start = m.end()
    depth = 1
    i = start
    while i < len(line) and depth:
        if line[i] == "(":
            depth += 1
        elif line[i] == ")":
            depth -= 1
        i += 1
    return line[start : i - 1]


def split_top_comma(s: str) -> list[str]:
    """Split s at top-level commas."""
    parts, cur, depth = [], [], 0
    for c in s:
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(c)
    parts.append("".join(cur).strip())
    return parts


def is_simple(expr: str) -> bool:
    """True when expr is a plain identifier or number (no operators)."""
    return bool(re.match(r"^[\w.]+$", expr.strip()))


# ── Expression-level conversions ───────────────────────────────────────────────

def convert_expr(expr: str) -> str:
    """Applies all expression-level Python → Kojo substitutions."""

    # math
    expr = re.sub(r"\bmath\.pi\b", "math.Pi", expr)
    expr = re.sub(r"(?<!math\.)\bpi\b", "math.Pi", expr)
    expr = re.sub(r"(?<!math\.)\bsqrt\(", "math.sqrt(", expr)
    expr = re.sub(r"(?<!math\.)\batan\(", "math.atan(", expr)
    expr = re.sub(r"(?<!math\.)\batan2\(", "math.atan2(", expr)
    expr = re.sub(r"(?<!math\.)\bcos\(", "math.cos(", expr)
    expr = re.sub(r"(?<!math\.)\bsin\(", "math.sin(", expr)
    expr = re.sub(r"\bmath\.radians\(", "math.toRadians(", expr)

    # ** → math.pow
    expr = re.sub(
        r"(\w+(?:\.\w+)*|\([^)]+\))\s*\*\*\s*(\w+(?:\.\w+)*|\([^)]+\))",
        lambda m: f"math.pow({m.group(1)}, {m.group(2)})",
        expr,
    )

    # array indexing arr[i] → arr(i)
    expr = re.sub(r"(\w+)\[([^\]]+)\]", r"\1(\2)", expr)

    # color strings → bare words
    expr = re.sub(r'"(red|blue|green|yellow|orange|purple|magenta|cyan|'
                  r'black|white|gray|darkGray|brown|pink)"', r"\1", expr)

    return expr


# ── Single-line turtle command conversions ────────────────────────────────────

def convert_turtle_call(content: str) -> str | None:
    """
    Convert a single turtle command line (already stripped of t. prefix).
    Returns the Kojo equivalent, or None if the line should be dropped.
    """
    # Commands to delete
    if re.match(r"(begin_fill|end_fill|done|mainloop|bye|tracer|update|"
                r"speed|colormode|setup|title|exitonclick)\s*\(", content):
        return None

    # circle(r, extent) → left(extent, r)   positive extent = counterclockwise
    # circle(r, -extent)→ right(extent, r)  negative extent = clockwise
    # circle(r)         → left(360, r)
    if re.match(r"circle\s*\(", content):
        raw = extract_call_args(content, "circle")
        parts = split_top_comma(raw)
        r_expr = convert_expr(parts[0])
        if len(parts) >= 2:
            ext_raw = parts[1].strip()
            # Check for a literal negative number e.g. -180, -90
            neg = re.match(r"^-(\d+(?:\.\d+)?)$", ext_raw)
            if neg:
                return f"right({neg.group(1)}, {r_expr})"
            else:
                ext = convert_expr(ext_raw)
                return f"left({ext}, {r_expr})"
        else:
            return f"left(360, {r_expr})"

    # forward / backward / back
    if m := re.match(r"(forward|fd)\s*\((.+)\)$", content):
        return f"forward({convert_expr(m.group(2))})"
    if m := re.match(r"(backward|back|bk)\s*\((.+)\)$", content):
        return f"back({convert_expr(m.group(2))})"

    # right / left
    if m := re.match(r"right\s*\((.+)\)$", content):
        return f"right({convert_expr(m.group(1))})"
    if m := re.match(r"left\s*\((.+)\)$", content):
        return f"left({convert_expr(m.group(1))})"

    # penup/pendown handled by hop-collapse pass; these are fallbacks
    if re.match(r"(penup|pu|up)\s*\(\)$", content):
        return "penUp()"
    if re.match(r"(pendown|pd|down)\s*\(\)$", content):
        return "penDown()"

    # goto / setpos / setposition
    if m := re.match(r"(goto|setpos|setposition)\s*\((.+)\)$", content):
        args = split_top_comma(convert_expr(m.group(2)))
        return f"setPosition({', '.join(args)})"

    # setheading
    if m := re.match(r"setheading\s*\((.+)\)$", content):
        return f"setHeading({convert_expr(m.group(1))})"

    # home
    if re.match(r"home\s*\(\)$", content):
        return "setPosition(0, 0)"

    # pencolor / color
    if m := re.match(r"(pencolor|color)\s*\((.+)\)$", content):
        return f"setPenColor({convert_expr(m.group(2))})"

    # fillcolor
    if m := re.match(r"fillcolor\s*\((.+)\)$", content):
        return f"setFillColor({convert_expr(m.group(1))})"

    # width / pensize
    if m := re.match(r"(width|pensize)\s*\((.+)\)$", content):
        return f"setPenThickness({convert_expr(m.group(2))})"

    # hideturtle / showturtle
    if re.match(r"hideturtle\s*\(\)$", content):
        return "invisible()"
    if re.match(r"showturtle\s*\(\)$", content):
        return "visible()"

    # bgcolor (screen method)
    if m := re.match(r"(bgcolor|screen\.bgcolor|wn\.bgcolor)\s*\((.+)\)$", content):
        return f"setBackground({convert_expr(m.group(2))})"

    # speed — map any value to fast
    if re.match(r"speed\s*\(", content):
        return "setSpeed(fast)"

    return None  # not a recognised turtle call — fall through to general conversion


# ── Hop collapsing ─────────────────────────────────────────────────────────────

_PENUP_RE   = re.compile(r"^\s*t\.(penup|pu|up)\s*\(\)\s*$")
_FORWARD_RE = re.compile(r"^\s*t\.(forward|fd)\s*\((.+)\)\s*$")
_PENDOWN_RE = re.compile(r"^\s*t\.(pendown|pd|down)\s*\(\)\s*$")


def collapse_hops(lines: list[str]) -> list[str]:
    """
    Replace sequential  t.penup() / t.forward(n) / t.pendown()
    with a single       hop(n)
    at the same indentation level.
    """
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _PENUP_RE.match(line):
            indent = len(line) - len(line.lstrip())
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and _FORWARD_RE.match(lines[j]):
                fwd_indent = len(lines[j]) - len(lines[j].lstrip())
                if fwd_indent == indent:
                    fm = _FORWARD_RE.match(lines[j])
                    dist = convert_expr(fm.group(2).strip())
                    k = j + 1
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    if k < len(lines) and _PENDOWN_RE.match(lines[k]):
                        pd_indent = len(lines[k]) - len(lines[k].lstrip())
                        if pd_indent == indent:
                            out.append(" " * indent + f"hop({dist})")
                            i = k + 1
                            continue
        out.append(line)
        i += 1
    return out


# ── Block structure converter ──────────────────────────────────────────────────

def get_indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def convert_params(params_str: str) -> str:
    if not params_str.strip():
        return ""
    params = [p.strip() for p in params_str.split(",") if p.strip()]
    typed = []
    for p in params:
        ptype = "Int" if p in INT_PARAM_NAMES else "Double"
        typed.append(f"{p}: {ptype}")
    return ", ".join(typed)


def is_literal_int(s: str) -> bool:
    return bool(re.match(r"^\d+$", s.strip()))


def range_to_kojo(var: str, range_args: str, body_lines: list[str]) -> str:
    args = [a.strip() for a in split_top_comma(range_args)]
    uses_var = var != "_" and any(
        re.search(r"\b" + re.escape(var) + r"\b", bl) for bl in body_lines
    )
    if not uses_var:
        if len(args) == 1:
            n = convert_expr(args[0])
            sfx = "" if is_literal_int(n.strip()) else ".toInt"
            return f"repeat({n}{sfx}) {{"
        else:
            n = f"({convert_expr(args[1])} - {convert_expr(args[0])})"
            return f"repeat({n}.toInt) {{"
    else:
        if len(args) == 1:
            end = convert_expr(args[0])
            eu = end if is_literal_int(end) else f"{end}.toInt"
            return f"repeatFor(0 until {eu}) {{ {var} =>"
        else:
            start = convert_expr(args[0])
            end   = convert_expr(args[1])
            return f"repeatFor({start} until {end}) {{ {var} =>"


def convert_code(python_code: str) -> str:
    raw = python_code.rstrip("\n").split("\n")

    # ── Pass 1: hop collapsing ────────────────────────────────────────────────
    raw = collapse_hops(raw)

    result  = [HEADER.rstrip()]  # prepend clear() + setSpeed(fast) + setHeading(0)
    stack   = [0]
    after_block = False

    # Track declared names: first assignment → var, subsequent → bare reassignment
    declared_vars: set[str] = set()

    i = 0
    while i < len(raw):
        line = raw[i]

        # Skip blank lines that sit just before a dedent (cosmetic)
        if not line.strip():
            j = i + 1
            while j < len(raw) and not raw[j].strip():
                j += 1
            if j < len(raw) and get_indent(raw[j]) < stack[-1]:
                i += 1
                continue
            result.append("")
            i += 1
            continue

        if should_skip(line):
            i += 1
            continue

        curr    = get_indent(line)
        content = line.strip()

        # Push body indent when previous line opened a block
        if after_block:
            if curr > stack[-1]:
                stack.append(curr)
            after_block = False

        # Collect body lines for loop-var lookahead
        body: list[str] = []
        j = i + 1
        while j < len(raw):
            nl = raw[j]
            if not nl.strip():
                j += 1
                continue
            if get_indent(nl) > curr:
                body.append(nl.strip())
                j += 1
            else:
                break

        # ── else ────────────────────────────────────────────────────────────
        if content == "else:":
            closes: list[int] = []
            while len(stack) > 1 and curr < stack[-1]:
                stack.pop()
                closes.append(stack[-1])
            for ci in closes[:-1]:
                result.append(" " * ci + "}")
            result.append(" " * curr + "} else {")
            after_block = True
            i += 1
            continue

        # ── elif ─────────────────────────────────────────────────────────────
        if m := re.match(r"elif\s+(.+):", content):
            closes = []
            while len(stack) > 1 and curr < stack[-1]:
                stack.pop()
                closes.append(stack[-1])
            for ci in closes[:-1]:
                result.append(" " * ci + "}")
            cond = convert_expr(m.group(1).strip())
            result.append(" " * curr + f"}} else if ({cond}) {{")
            after_block = True
            i += 1
            continue

        # ── Normal dedent close ───────────────────────────────────────────────
        while len(stack) > 1 and curr < stack[-1]:
            stack.pop()
            result.append(" " * stack[-1] + "}")

        # ── for loop ─────────────────────────────────────────────────────────
        if m := re.match(r"for\s+(\w+)\s+in\s+range\(([^)]+)\)\s*:", content):
            result.append(" " * curr + range_to_kojo(m.group(1), m.group(2), body))
            after_block = True
            i += 1
            continue

        # ── def ──────────────────────────────────────────────────────────────
        if m := re.match(r"def\s+(\w+)\(([^)]*)\)\s*:", content):
            result.append(" " * curr + f"def {m.group(1)}({convert_params(m.group(2))}) {{")
            after_block = True
            i += 1
            continue

        # ── if ───────────────────────────────────────────────────────────────
        if m := re.match(r"if\s+(.+):", content):
            cond = convert_expr(m.group(1).strip())
            result.append(" " * curr + f"if ({cond}) {{")
            after_block = True
            i += 1
            continue

        # ── turtle call (t.xxx or bare after stripping) ───────────────────────
        bare = re.sub(r"^t\.", "", content)
        kojo_line = convert_turtle_call(bare)
        if kojo_line is None and bare != content:
            kojo_line = convert_expr(bare)
        if kojo_line is not None and bare != content:
            result.append(" " * curr + kojo_line)
            i += 1
            continue

        # ── variable assignment  x = expr ────────────────────────────────────
        if m := re.match(r"^([A-Za-z_]\w*)\s*=(?!=)\s*(.+)", content):
            lhs = m.group(1)
            rhs = convert_expr(m.group(2).rstrip())
            if lhs in declared_vars:
                result.append(" " * curr + f"{lhs} = {rhs}")
            else:
                declared_vars.add(lhs)
                result.append(" " * curr + f"var {lhs} = {rhs}")
            i += 1
            continue

        # ── bare function call (no t. prefix) ────────────────────────────────
        kojo_line = convert_turtle_call(content)
        if kojo_line is not None:
            if kojo_line:  # not dropped
                result.append(" " * curr + kojo_line)
        else:
            result.append(" " * curr + convert_expr(content))
        i += 1

    # Close any remaining blocks
    while len(stack) > 1:
        stack.pop()
        result.append(" " * stack[-1] + "}")

    return "\n".join(result)


# ── File processing ────────────────────────────────────────────────────────────

def process_task(task_dir: Path) -> int:
    code_dir = task_dir / "QA" / "code"
    if not code_dir.exists():
        return 0
    count = 0
    for txt_file in sorted(code_dir.glob("q*_code.txt")):
        orig = txt_file.with_suffix(".py_orig")
        source = orig if orig.exists() else txt_file
        python_code = source.read_text(encoding="utf-8")

        if not orig.exists():
            orig.write_text(python_code, encoding="utf-8")

        converted = convert_code(python_code)
        txt_file.write_text(converted, encoding="utf-8")
        count += 1
    return count


def main():
    if not TASKS_DIR.exists():
        print(f"ERROR: {TASKS_DIR}/ not found.")
        return
    task_dirs = sorted(
        [d for d in TASKS_DIR.iterdir() if d.is_dir()],
        key=lambda d: int(d.name) if d.name.isdigit() else d.name,
    )
    total = sum(process_task(td) for td in task_dirs)
    print(f"Converted {total} files across {len(task_dirs)} tasks.")


if __name__ == "__main__":
    main()
