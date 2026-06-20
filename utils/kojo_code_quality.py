"""
utils/kojo_code_quality.py

Kojo Code Style Score (KCSS): rates LLM-generated Kojo code on whether it
matches the simplicity and idioms of canonical Kojo turtle-graphics code.

Three sub-scores (each 0.0–1.0):
  structure  (40%) — no forbidden OOP / import / Python-turtle constructs
  idioms     (30%) — uses repeat, arc movement, hop and similar Kojo patterns
  simplicity (30%) — code is not disproportionately bloated vs ground truth

Final KCSS = 0.4 * structure + 0.3 * idioms + 0.3 * simplicity
"""

import re
from dataclasses import dataclass, field

# ── Forbidden patterns → structure score = 0.0 if any present ─────────────
_FORBIDDEN: list[tuple[str, str]] = [
    (r'\bobject\s+\w+\s*\{',               "Java object wrapper"),
    (r'\bclass\s+\w+',                      "class definition"),
    (r'\bdef\s+main\s*\(',                  "main() method"),
    (r'^\s*import\s+',                      "import statement"),
    (r'\bSystem\.',                         "Java System call"),
    (r'\bprintln\s*\(',                     "println call"),
    (r'\bnew\s+\w+',                        "object instantiation (new ...)"),
    (r'\bextends\s+\w+',                    "class extension"),
    (r'\bArray\[',                          "Scala Array type"),
    # Python turtle commands that do not exist in Kojo
    (r'\bgoto\s*\(',                        "Python goto()"),
    (r'\bcircle\s*\(',                      "Python circle()"),
    (r'\bbegin_fill\s*\(',                  "Python begin_fill()"),
    (r'\bend_fill\s*\(',                    "Python end_fill()"),
    (r'\bhideturtle\s*\(',                  "Python hideturtle()"),
    (r'\bshowturtle\s*\(',                  "Python showturtle()"),
    (r'\bpensize\s*\(',                     "Python pensize()"),
    (r'\bspeed\s*\(',                       "Python speed()"),
    (r'\bcolor\s*\(',                       "Python color()"),
    (r'\bfd\s*\(',                          "Python fd() alias"),
    (r'\bbk\s*\(',                          "Python bk() alias"),
    (r'\brt\s*\(',                          "Python rt() alias"),
    (r'\blt\s*\(',                          "Python lt() alias"),
]

# ── Soft warnings (don't kill the score but appear in the report) ──────────
_WARNINGS: list[tuple[str, str]] = [
    (r'\bwhile\s*\(',                       "while loop (prefer repeat)"),
    (r'\bfor\s*\(',                         "for loop (prefer repeat/repeatFor)"),
    (r'(?s)penUp\(\).*penUp\(\).*penUp\(\)', "3+ pen lifts (repositioning-heavy)"),
    (r'\bsetPosition\b[^\n]*\n[^\n]*\bsetPosition\b[^\n]*\n[^\n]*\bsetPosition\b',
                                            "3+ setPosition calls (coordinate-heavy)"),
    (r'\bsetHeading\b.*\bsetHeading\b.*\bsetHeading\b.*\bsetHeading\b',
                                            "4+ setHeading calls (consider arcs)"),
]

# ── Canonical Kojo idioms (positive signals) ───────────────────────────────
_IDIOMS: list[tuple[str, str]] = [
    (r'\brepeat\s*\(',                      "repeat loop"),
    (r'\b(?:right|left)\s*\(\s*[\d.]+\s*,\s*[\d.]', "arc movement (angle, radius)"),
    (r'\bhop\s*\(',                         "hop"),
    (r'\brepeatFor\s*\(',                   "repeatFor loop"),
    (r'\bsavePosHe\s*\(\s*\)',              "savePosHe / restorePosHe"),
    (r'\bdef\s+\w+\s*\([^)]*\)\s*\{',      "reusable def with params"),
]

# Lines that are boilerplate / wrapper and should not count toward effective length
_BOILERPLATE = re.compile(
    r'^\s*('
    r'cleari\(\)'
    r'|drawCentered\s*\('
    r'|def\s+shape\s*=\s*Picture\s*\{'
    r'|setSpeed\s*\([^)]*\)'
    r'|//[^\n]*'          # single-line comments
    r'|\}'                # closing braces alone
    r')\s*$'
)


@dataclass
class CodeQualityReport:
    score:     float
    forbidden: list[str] = field(default_factory=list)
    warnings:  list[str] = field(default_factory=list)
    idioms:    list[str] = field(default_factory=list)
    metrics:   dict      = field(default_factory=dict)

    def summary(self) -> str:
        parts = [f"KCSS {self.score * 100:.0f}%"]
        if self.forbidden:
            parts.append("FORBIDDEN: " + ", ".join(self.forbidden))
        if self.warnings:
            parts.append("WARN: " + ", ".join(self.warnings))
        if self.idioms:
            parts.append("idioms: " + ", ".join(self.idioms))
        return " | ".join(parts)

    def one_line(self) -> str:
        status = "✗" if self.forbidden else ("△" if self.warnings else "✓")
        return f"{status} KCSS={self.score*100:.0f}%  lines={self.metrics.get('llm_lines','?')}  bloat={self.metrics.get('bloat_ratio','?')}x"


def _effective_lines(code: str) -> int:
    """Non-blank, non-boilerplate lines — the actual drawing work."""
    return sum(
        1 for line in code.splitlines()
        if line.strip() and not _BOILERPLATE.match(line)
    )


def analyze(llm_code: str, gt_code: str | None = None) -> CodeQualityReport:
    """
    Analyse LLM-generated Kojo drawing code for style quality.

    Parameters
    ----------
    llm_code : the drawing commands as extracted from the LLM response
               (what's inside the ```scala fence, before wrapping)
    gt_code  : ground-truth KojoTask{N}.kojo content; used for the bloat ratio.
               If omitted, a fixed 10-line baseline is used.
    """
    report = CodeQualityReport(score=0.0)

    # ── 1. Structure score ─────────────────────────────────────────────────
    found_forbidden = [
        label
        for pattern, label in _FORBIDDEN
        if re.search(pattern, llm_code, re.MULTILINE | re.IGNORECASE)
    ]
    report.forbidden = found_forbidden
    structure_score = 0.0 if found_forbidden else 1.0

    # ── 2. Idiom score ─────────────────────────────────────────────────────
    found_idioms = [
        label
        for pattern, label in _IDIOMS
        if re.search(pattern, llm_code)
    ]
    report.idioms = found_idioms
    # 2+ distinct idioms = full idiom score
    idiom_score = min(len(found_idioms) / 2.0, 1.0)

    # ── 3. Simplicity / bloat score ────────────────────────────────────────
    llm_lines = _effective_lines(llm_code)
    if gt_code:
        gt_lines = max(_effective_lines(gt_code), 1)
        bloat    = llm_lines / gt_lines
    else:
        gt_lines = None
        bloat    = llm_lines / 10.0   # 10-line canonical baseline

    if   bloat <= 1.5: simplicity_score = 1.0
    elif bloat <= 2.5: simplicity_score = 0.8
    elif bloat <= 4.0: simplicity_score = 0.5
    elif bloat <= 6.0: simplicity_score = 0.2
    else:              simplicity_score = 0.0

    # ── 4. Soft warnings ──────────────────────────────────────────────────
    report.warnings = [
        label
        for pattern, label in _WARNINGS
        if re.search(pattern, llm_code, re.DOTALL)
    ]

    # ── Metrics ────────────────────────────────────────────────────────────
    report.metrics = {
        "llm_lines":        llm_lines,
        "gt_lines":         gt_lines,
        "bloat_ratio":      round(bloat, 2),
        "structure_score":  structure_score,
        "idiom_score":      round(idiom_score, 2),
        "simplicity_score": simplicity_score,
    }

    # ── Final KCSS ─────────────────────────────────────────────────────────
    report.score = (
        0.4 * structure_score +
        0.3 * idiom_score     +
        0.3 * simplicity_score
    )

    return report
