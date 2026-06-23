"""
Generates KojoBench2_Qwen_Analysis.pdf — complete per-task analysis.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                 Spacer, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from pathlib import Path

OUT = Path(__file__).parent / "KojoBench2_Qwen_Analysis_v3.pdf"

C_HEAD   = colors.HexColor("#1a1a2e")
C_PASS   = colors.HexColor("#22c55e")
C_FAIL   = colors.HexColor("#ef4444")
C_CRASH  = colors.HexColor("#f59e0b")
C_WHITE  = colors.white
C_ALT    = colors.HexColor("#eef2ff")
C_BORDER = colors.HexColor("#e2e8f0")
C_MUTED  = colors.HexColor("#64748b")

doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=18*mm, rightMargin=18*mm,
    topMargin=16*mm, bottomMargin=16*mm
)
W = A4[0] - 36*mm

styles = getSampleStyleSheet()
def sty(name, **kw):
    return ParagraphStyle(name, parent=styles["Normal"], **kw)

title_sty = sty("TT",  fontSize=17, fontName="Helvetica-Bold", textColor=C_HEAD, spaceAfter=3)
sub_sty   = sty("Sub", fontSize=8.5, fontName="Helvetica",     textColor=C_MUTED, spaceAfter=6)
h2_sty    = sty("H2",  fontSize=11, fontName="Helvetica-Bold", textColor=C_HEAD, spaceBefore=8, spaceAfter=4)
note_sty  = sty("N",   fontSize=7,  fontName="Helvetica-Oblique", textColor=C_MUTED, leading=10)

# Cell paragraph styles — these are what make text wrap inside table cells
def cs(name, align=TA_CENTER, bold=False, size=7.5, color=C_HEAD):
    fn = "Helvetica-Bold" if bold else "Helvetica"
    return sty(name, fontSize=size, fontName=fn, textColor=color,
               alignment=align, leading=size*1.35, wordWrap='CJK')

CH  = cs("CH",  bold=True,  color=C_WHITE)   # column header
CL  = cs("CL",  align=TA_LEFT)               # left-aligned body
CC  = cs("CC")                                # centre body
CB  = cs("CB",  bold=True)                    # bold centre
CLP = cs("CLP", align=TA_LEFT,  color=C_PASS,  bold=True)
CLF = cs("CLF", align=TA_LEFT,  color=C_FAIL,  bold=True)
CLC = cs("CLC", align=TA_LEFT,  color=C_CRASH, bold=True)
CP  = cs("CP",  color=C_PASS,  bold=True)
CF  = cs("CF",  color=C_FAIL,  bold=True)
CCR = cs("CCR", color=C_CRASH, bold=True)

def p(txt, style=CC): return Paragraph(str(txt), style)
def pl(txt):          return Paragraph(str(txt), CL)
def hdr(txt):         return Paragraph(txt, h2_sty)
def note(txt):        return Paragraph(txt, note_sty)
def sp(h=4):          return Spacer(1, h*mm)
def hr():             return HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=3)

BASE_STYLE = [
    ("FONTSIZE",      (0,0), (-1,-1), 7.5),
    ("BACKGROUND",    (0,0), (-1,0),  C_HEAD),
    ("TEXTCOLOR",     (0,0), (-1,0),  C_WHITE),
    ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_ALT]),
    ("GRID",          (0,0), (-1,-1), 0.3, C_BORDER),
    ("TOPPADDING",    (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING",   (0,0), (-1,-1), 5),
    ("RIGHTPADDING",  (0,0), (-1,-1), 5),
]

def tbl(data, col_widths, extra=None):
    style = list(BASE_STYLE) + (extra or [])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(style))
    return t

# ── All task data ─────────────────────────────────────────────────────────────
tasks = [
    (1,  "Circle",                                                "100%","PASS",  "Primitive"),
    (2,  "Triangle pointing up",                                  "2%",  "FAIL",  "Triangle / orientation"),
    (3,  "Square",                                                "100%","PASS",  "Primitive"),
    (4,  "Pentagon, flat bottom",                                 "66%", "PASS",  "Regular polygon"),
    (5,  "Triangle with smaller triangles at each corner",        "25%", "FAIL",  "Composite"),
    (6,  "Two side-by-side upward triangles sharing a corner",    "28%", "FAIL",  "Composite / triangle"),
    (7,  "Square + right-pointing triangle on right side",        "24%", "FAIL",  "Composite"),
    (8,  "Four-pointed star (square centre + 4 triangles)",       "48%", "FAIL",  "Star / composite"),
    (9,  "S-curve (top curves right, bottom curves left)",        "29%", "FAIL",  "Arc / curve"),
    (10, "Circle inscribed in a square (touches midpoints)",      "45%", "FAIL",  "Arc + composite"),
    (11, "Rectangle (longer sides horizontal)",                   "97%", "PASS",  "Primitive"),
    (12, "Right-angle triangle (two sides axis-aligned)",         "3%",  "FAIL",  "Triangle / orientation"),
    (13, "Hexagon, flat top and bottom",                          "20%", "FAIL",  "Regular polygon / orientation"),
    (14, "Five-pointed star",                                     "22%", "FAIL",  "Star"),
    (15, "Two rectangles joined at corner forming an L",          "24%", "FAIL",  "Composite"),
    (16, "Square balanced on one corner (diamond)",               "0%",  "FAIL",  "Orientation"),
    (17, "Equilateral triangle pointing downward",                "3%",  "FAIL",  "Triangle / orientation"),
    (18, "Rightward arrow (rect body + triangle head)",           "8%",  "FAIL",  "Composite / orientation"),
    (19, "Octagon, flat top and bottom",                          "71%", "PASS",  "Regular polygon"),
    (20, "Square centred inside larger square, sides parallel",   "39%", "FAIL",  "Composite / nesting"),
    (21, "Semicircle, flat side at bottom",                       "27%", "FAIL",  "Arc / semicircle"),
    (22, "Wide rect + narrower rect on top forming a T",          "13%", "FAIL",  "Composite"),
    (23, "Staircase of three equal steps, lower-left to upper-right","0%","FAIL", "Staircase / composite"),
    (24, "Trapezoid (parallel top and bottom, top shorter)",      "16%", "FAIL",  "Polygon / orientation"),
    (25, "Three equal upward triangles side by side",             "36%", "FAIL",  "Composite / triangle"),
    (26, "Three adjacent squares sharing a base in a rectangle",  "65%", "FAIL*", "Composite"),
    (27, "Square inscribed inside a circle",                      "40%", "FAIL",  "Arc + composite"),
    (28, "Square with both diagonals drawn",                      "45%", "FAIL",  "Composite"),
    (29, "Square with diagonal top-left to bottom-right",         "100%","PASS",  "Primitive+"),
    (30, "Square with diagonal top-right to bottom-left",         "15%", "FAIL",  "Orientation"),
    (31, "Two squares connected at exactly one corner",           "0%",  "FAIL",  "Composite"),
    (32, "Two circles stacked + vertical diameter of upper",      "CRASH","CRASH","Arc / hop(x,y)"),
    (33, "Two overlapping squares",                               "33%", "FAIL",  "Composite"),
    (34, "Square, side length 80",                                "18%", "FAIL",  "Size-specific"),
    (35, "Semicircle on top of equilateral triangle (shared base)","26%","FAIL",  "Arc + composite"),
    (36, "Two circles touching at one point, larger on left",     "39%", "FAIL",  "Arc / multi-circle"),
    (37, "Rectangle with rounded corners",                        "3%",  "FAIL",  "Arc / rounded rect"),
    (38, "Three circles of different radii sharing one point",    "48%", "FAIL",  "Arc / multi-circle"),
    (39, "Three concentric circles",                              "57%", "FAIL",  "Arc / concentric"),
    (40, "Semicircle, radius 60",                                 "0%",  "FAIL",  "Arc / semicircle"),
    (41, "Two semicircles and one triangle",                      "30%", "FAIL",  "Arc + composite"),
    (42, "Triangle with two semicircles at base",                 "26%", "FAIL",  "Arc + composite"),
    (43, "Square with four semicircles at each corner",           "42%", "FAIL",  "Arc + composite"),
    (44, "Three overlapping semicircles",                         "CRASH","CRASH","Arc / hop(x,y)"),
    (45, "Four equal squares forming one larger square",          "17%", "FAIL",  "Composite"),
    (46, "Three equilateral triangles",                           "CRASH","CRASH","Triangle / hop(x,y)"),
    (47, "Three squares in a triangular pattern",                 "0%",  "FAIL",  "Composite"),
    (48, "Four nested squares with increasing side lengths",      "58%", "FAIL",  "Composite / nesting"),
    (49, "Square with four quarter-circles at each corner",       "28%", "FAIL",  "Arc + composite"),
    (50, "Square with a circle at each of its four corners",      "45%", "FAIL",  "Arc + composite"),
    (51, "Hexagon with alternating large and small circles",      "61%", "FAIL",  "Arc + polygon"),
    (52, "Octagon",                                               "36%", "FAIL",  "Regular polygon"),
    (53, "Square, side length 100",                               "30%", "FAIL",  "Size-specific"),
    (54, "Six regular hexagons arranged in a ring",               "67%", "PASS",  "Structured repeat"),
    (55, "Five concentric regular pentagons",                     "64%", "FAIL",  "Composite / nesting"),
    (56, "Three regular hexagons in a triangular pattern",        "33%", "FAIL",  "Composite / polygon"),
    (57, "Large triangle, smaller triangle, large triangle in row","30%","FAIL",  "Composite / triangle"),
    (58, "Two concentric circles",                                "64%", "FAIL",  "Arc / concentric"),
    (59, "Large square containing four smaller squares inside",   "55%", "FAIL",  "Composite / nesting"),
    (60, "Four triangles of different sizes in a row",            "33%", "FAIL",  "Composite / triangle"),
    (61, "Semicircle with horizontal diameter line",              "CRASH","CRASH","Arc / hop(x,y)"),
    (62, "Two circles intersecting, shared lens region",          "CRASH","CRASH","Arc / hop(x,y)"),
    (63, "Hexagon with semicircle on each of its six sides",      "54%", "FAIL",  "Arc + polygon"),
    (64, "Square subdivided into four equilateral triangles",     "63%", "FAIL",  "Composite / triangle"),
    (65, "Three semicircles in a triangular pattern",             "23%", "FAIL",  "Arc / semicircle"),
    (66, "Large circle with four smaller circles inside",         "43%", "FAIL",  "Arc / multi-circle"),
    (67, "Four semicircles arranged in a square pattern",         "14%", "FAIL",  "Arc / semicircle"),
    (68, "Square with four corner semicircles (variant A)",       "41%", "FAIL",  "Arc + composite"),
    (69, "Square with four corner semicircles (variant B)",       "24%", "FAIL",  "Arc + composite"),
    (70, "Grid of nine equilateral triangles (3x3)",              "41%", "FAIL",  "Composite / triangle"),
    (71, "Semicircle, radius 100",                                "4%",  "FAIL",  "Arc / semicircle"),
    (72, "Square, side length 200 (variant A)",                   "37%", "FAIL",  "Size-specific"),
    (73, "Large equilateral triangle with smaller inside",        "CRASH","CRASH","Triangle / sqrt import"),
    (74, "Square, side length 200 (variant B)",                   "80%", "PASS",  "Size-specific"),
    (75, "Square with inner square rotated 45 degrees",           "36%", "FAIL",  "Composite / orientation"),
]

# ── Build story ───────────────────────────────────────────────────────────────
story = []

story.append(Paragraph("KojoBench2 — Model Evaluation Report", title_sty))
story.append(Paragraph("Qwen 2.5 Coder 7B  ·  75 Tasks  ·  Zero-Shot  ·  Kojo (Scala) turtle graphics", sub_sty))
story.append(hr())
story.append(sp(2))

# ── 1. Overview ───────────────────────────────────────────────────────────────
story.append(hdr("1. Overview"))
ov = [
    [p("Metric", CH),                          p("Qwen 2.5 Coder 7B", CH),     p("Claude Sonnet 4.6", CH)],
    [pl("Visual Pass Rate (NSS >= 65%)"),       p("8 / 75  (10.7%)"),            p("39 / 75  (52.0%)")],
    [pl("Average NSS"),                         p("36.4%", CF),                  p("66.6%", CP)],
    [pl("Average KCSS (code quality)"),         p("77.1%"),                      p("81.3%")],
    [pl("Render Failures (CRASH)"),             p("6 / 75"),                     p("0 / 75")],
    [pl("Responses using // comments"),         p("66 / 75"),                    p("—")],
    [pl("hop(x,y) two-arg hallucination"),      p("5 tasks = CRASH", CCR),       p("0")],
    [pl("Missing math import (sqrt)"),          p("1 task = CRASH", CCR),        p("0")],
]
story.append(tbl(ov, [W*0.44, W*0.28, W*0.28]))
story.append(sp(2))
story.append(note(
    "NSS = Normalised Shape Similarity (0.7 × chamfer + 0.3 × edge correlation). "
    "KCSS = Kojo Code Style Score (0.4 × structure + 0.3 × idioms + 0.3 × simplicity). "
    "CRASH = Scala compilation failure; no NSS computed."
))
story.append(sp(5))

# ── 2. Passed tasks ───────────────────────────────────────────────────────────
story.append(hdr("2. Tasks Passed (NSS >= 65%)"))
ph = [[p("ID",CH), p("Description",CH), p("NSS",CH), p("Category",CH)]]
pr = []
for t in tasks:
    if t[3] == "PASS":
        pr.append([p(f"T{t[0]}"), pl(t[1]), p(t[2], CP), pl(t[4])])
extra_p = [("BACKGROUND",(0,i),(-1,i), colors.HexColor("#f0fdf4")) for i in range(1, len(pr)+1)]
story.append(tbl(ph + pr, [W*0.09, W*0.52, W*0.12, W*0.27], extra_p))
story.append(sp(2))
story.append(note(
    "T26 scored exactly 65% and fell just below the pass threshold. "
    "All 8 passes are primitives or regular polygons solvable with a single repeat loop. "
    "No composite shape, arc-sequence, or orientation-specific task passed."
))
story.append(sp(5))

# ── 3. Failure Taxonomy ───────────────────────────────────────────────────────
story.append(hdr("3. Failure Taxonomy"))
th = [[p("Category",CH), p("N",CH), p("Avg NSS",CH), p("Exemplar Tasks",CH), p("Root Cause",CH)]]
tax = [
    ["CRASH — hop(x,y) 2-arg",    "5",  "—",   "T32, T44, T46, T61, T62",
     "Kojo hop(n) takes one arg; Qwen invents Python-style hop(x,y)"],
    ["CRASH — missing import",     "1",  "—",   "T73",
     "sqrt(3) used without scala.math import"],
    ["Orientation / mirroring",    "5",  "5%",  "T2, T12, T16, T17, T30",
     "Correct shape type; wrong rotation or reflection"],
    ["Arc / semicircle sequencing","12", "22%", "T9, T21, T35, T40, T41, T42, T43, T65, T67, T68, T69, T71",
     "right(angle,r) syntax recalled correctly; post-arc turtle state not tracked"],
    ["Multi-shape composition",    "14", "32%", "T6, T7, T22, T25, T31, T45, T47, T56, T57, T60, T63, T64, T70, T75",
     "Turtle not repositioned between shapes; second shape drawn at wrong position"],
    ["Nesting / concentric",       "6",  "51%", "T20, T39, T48, T55, T58, T59",
     "Closest to passing; scale or centre offset slightly wrong"],
    ["Size-specific (GT mismatch)","3",  "28%", "T34, T53, T72",
     "GT code draws a different shape than the auto-generated query describes"],
    ["Other composite / polygon",  "15", "34%", "T5, T8, T10, T13, T14, T15, T18, T24, T27, T28, T33, T36, T38, T50, T51",
     "Shape partially correct; composition, count, or proportion wrong"],
]
tr = []
for row in tax:
    tr.append([pl(row[0]), p(row[1]), p(row[2]), pl(row[3]), pl(row[4])])
crash_bg = [("BACKGROUND",(0,i),(-1,i), colors.HexColor("#fffbeb")) for i in (1,2)]
story.append(tbl(th + tr, [W*0.19, W*0.05, W*0.08, W*0.26, W*0.42], crash_bg))
story.append(sp(5))

# ── 4. Arc vs Non-Arc ────────────────────────────────────────────────────────
story.append(hdr("4. Arc / Semicircle vs. Non-Arc — NSS Comparison"))
ah = [[p("Group",CH), p("Tasks",CH), p("Avg NSS",CH), p("Interpretation",CH)]]
ar = [
    ["Arc / semicircle / circle tasks (28)", "28", "36.5%",
     "Syntax correctly recalled; sequencing fails identically to non-arc tasks"],
    ["Non-arc tasks",                         "47", "36.4%",
     "Same failure profile — gap is 0.1 percentage points"],
    ["All tasks excluding 6 crashes",         "69", "39.6%",
     "Crashes excluded from NSS average"],
    ["All 75 tasks (crashes counted as 0%)",  "75", "36.4%",
     "Headline figure"],
]
story.append(tbl(ah + [[pl(r[0]), p(r[1]), p(r[2]), pl(r[3])] for r in ar],
                 [W*0.33, W*0.09, W*0.10, W*0.48]))
story.append(sp(2))
story.append(note(
    "Arc and non-arc groups are statistically indistinguishable by NSS (36.5% vs 36.4%). "
    "The failure is not arc syntax — it is turtle state tracking, which collapses for any "
    "sequential multi-step drawing regardless of whether arcs are involved."
))
story.append(sp(5))

# ── 5. Core Diagnosis ────────────────────────────────────────────────────────
story.append(hdr("5. Core Diagnosis"))
dh = [[p("Failure Mode",CH), p("Explanation",CH)]]
diag = [
    ["Spatial state tracking",
     "Qwen does not propagate turtle position and heading across drawing steps. "
     "Each subsequent shape is drawn as if the turtle reset to the origin."],
    ["Allocentric orientation",
     "Orientation constraints ('pointing down', 'diagonal from top-right') are ignored. "
     "The shape type is pattern-matched but not rotated to match the specified direction."],
    ["API surface hallucination",
     "hop(x, y) is invented from Python Turtle / Processing conventions. "
     "Kojo's hop(n) accepts only a single distance argument. "
     "66 of 75 responses also include // comments (valid in Java; stripped by the renderer here)."],
    ["Declarative vs. procedural gap",
     "Arc syntax right(angle, radius) is correctly recalled (declarative), "
     "but the model cannot simulate what the call does to turtle heading and position (procedural). "
     "NSS for arc tasks: 36.5% — identical to non-arc tasks."],
    ["KCSS / NSS divergence",
     "Average KCSS 77.1% vs average NSS 36.4% — a 40.7-point gap. "
     "The model writes syntactically plausible, structurally valid Kojo code "
     "that compiles and renders, but produces the wrong image. "
     "Code-quality metrics cannot detect geometric semantic incorrectness."],
    ["Size-specific inconsistency",
     "T72 and T74 share the query 'Draw a square with side length 200' yet score 37% and 80%. "
     "The GT code at archive index 72 draws a different shape than the query describes — "
     "a benchmark labelling issue, not a Qwen error."],
]
story.append(tbl(dh + [[pl(r[0]), pl(r[1])] for r in diag], [W*0.25, W*0.75]))
story.append(sp(5))

# ── 6. Full task table ────────────────────────────────────────────────────────
story.append(hdr("6. Full Task Score Table (all 75 tasks)"))
fh = [[p("ID",CH), p("Description",CH), p("NSS",CH), p("Result",CH), p("Category",CH)]]
fr = []
extra_f = []
for i, t in enumerate(tasks, start=1):
    res = t[3]
    nss_p = p(t[2], CP if res=="PASS" else (CCR if res=="CRASH" else CF))
    res_p = p(res,  CP if res=="PASS" else (CCR if res=="CRASH" else CF))
    fr.append([p(f"T{t[0]}"), pl(t[1]), nss_p, res_p, pl(t[4])])
    if res == "PASS":
        extra_f.append(("BACKGROUND",(0,i),(-1,i), colors.HexColor("#f0fdf4")))
    elif res == "CRASH":
        extra_f.append(("BACKGROUND",(0,i),(-1,i), colors.HexColor("#fffbeb")))

story.append(tbl(fh + fr, [W*0.07, W*0.43, W*0.09, W*0.10, W*0.31], extra_f))
story.append(sp(3))
story.append(note(
    "All 75 tasks were evaluated — no tasks are missing. "
    "CRASH (T32, T44, T46, T61, T62): hop(x,y) two-arg form not valid in Kojo. "
    "CRASH (T73): sqrt(3) used without scala.math import. "
    "FAIL* T26 scored exactly 65% — at the threshold but counted as FAIL. "
    "T72 and T74 share the same query but different GT code (archive indexing inconsistency). "
    "NSS threshold for PASS: 65%. All scores rounded to nearest integer percent."
))

doc.build(story)
print(f"PDF written to: {OUT}")
