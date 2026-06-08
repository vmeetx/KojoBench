"""
utils/kojo_preprocess.py — replaces TurtleBench's utils/code_preprocess.py

Extracts Kojo (Scala) code from a raw LLM response string.

The original TurtleBench preprocess looks for Python ```python ... ``` fences.
We generalise to handle:
  - ```scala ... ```
  - ```kojo ... ```
  - ```  ... ```  (generic fenced block)
  - Raw code with no fences (fallback)
  - Responses that mix explanation and code

Strategy (in order):
1. Look for a ```scala or ```kojo fenced block.
2. Fall back to any fenced block (```) — take the longest one.
3. If no fences, heuristically strip preamble lines that don't look like
   Kojo statements (lines not starting with known Kojo keywords/builtins).
"""

import re


# Kojo/Scala keywords and common builtins used to identify code lines
_KOJO_STARTS = (
    "clear", "cleari", "forward", "back", "right", "left", "hop",
    "penUp", "penDown", "setPenColor", "setFillColor", "setPenThickness",
    "setBackground", "setSpeed", "setAnimationDelay", "repeat", "repeatFor",
    "def ", "val ", "var ", "if ", "else", "for ", "while ", "import",
    "object ", "class ", "trait ", "//", "/*", " *", "invisible", "visible",
    "savePosHe", "restorePosHe", "setPosition", "setHeading", "lineTo",
    "beginShape", "endShape", "vertex", "write", "setPenFont", "setPenFontSize",
    "randomColor", "cm.", "Color(", "Font(",
)


def preprocess_response(response: str) -> str:
    """
    Extract Kojo code from a raw model response.

    Parameters
    ----------
    response : str  — full text returned by the LLM

    Returns
    -------
    str — the extracted code snippet (may be empty if nothing found)
    """
    if not response:
        return ""

    # 1. Named fenced block — scala or kojo
    for lang_tag in ("scala", "kojo"):
        pattern = rf"```{lang_tag}\s*\n(.*?)```"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # 2. Generic fenced block — take the longest one
    generic_blocks = re.findall(r"```(?:\w+)?\s*\n(.*?)```", response, re.DOTALL)
    if generic_blocks:
        return max(generic_blocks, key=len).strip()

    # 3. No fences — heuristic: keep lines that look like Kojo statements
    lines = response.splitlines()
    code_lines = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if any(stripped.startswith(kw) for kw in _KOJO_STARTS):
            in_code = True
        if in_code:
            code_lines.append(line)

    if code_lines:
        return "\n".join(code_lines).strip()

    # 4. Last resort — return the whole response and let the runner fail gracefully
    return response.strip()
