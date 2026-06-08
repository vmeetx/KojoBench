"""
prompts_kojo.py — KojoBench prompt library

Mirrors the structure of TurtleBench's prompts.py exactly, but replaces every
reference to Python Turtle with Kojo (Scala) equivalents.

=== COMMAND REFERENCE EMBEDDED IN PROMPTS ===

The system prompts include a compact Kojo API reference so the model doesn't
need prior Kojo knowledge.  This is critical: Kojo is obscure enough that most
LLMs have minimal training signal for it.  Embedding the reference forces the
model to work from spec rather than memory — which is exactly the test.

=== KOJO ↔ PYTHON TURTLE MAPPING (for maintainers) ===

Python Turtle             Kojo equivalent
─────────────────────────────────────────────────────────
forward(n)                forward(n)
backward(n)               back(n)          [alias: forward(-n)]
right(angle)              right(angle)
left(angle)               left(angle)
right(angle, radius)      right(angle, radius)   ← arc; NO Python equivalent
left(angle, radius)       left(angle, radius)    ← arc
penup()                   penUp()
pendown()                 penDown()
goto(x, y)                setPosition(x, y)
setheading(angle)         setHeading(angle)
pensize(n)                setPenThickness(n)     ← NOTE: paper bans pensize
pencolor(c)               setPenColor(c)
fillcolor(c)              setFillColor(c)
begin_fill()/end_fill()   not needed; fill is automatic with setFillColor
bgcolor(c)                setBackground(c)
speed(n)                  setSpeed(slow|medium|fast|superFast)
hideturtle()              invisible()
showturtle()              visible()
for i in range(n): ...    repeat(n) { ... }
for i in range(a,b): ...  repeatFor(a to b) { i => ... }
def name(): ...           def name() { ... }
def name(x: int): ...     def name(x: Int) { ... }
color(r,g,b)              Color(r, g, b)          [0-255 each]
                          cm.hsl(hue, sat, light)  [hue 0-360, sat/light 0-1]
                          cm.rgb(r, g, b)          [0-255]
hop(n)                    hop(n)   ← forward without drawing; unique to Kojo
savePosHe() /             savePosHe() / restorePosHe()
  restorePosHe()
─────────────────────────────────────────────────────────

Origin: (0,0) is canvas centre.  North is 90°, East is 0°.  Same convention
as Python Turtle.  Kojo angles are in degrees, same as Turtle.
"""

# ── Embedded Kojo API reference (injected into system prompts) ──────────────
KOJO_API_REF = """\
--- KOJO API QUICK REFERENCE ---
The code must be written in Kojo (a Scala-based turtle graphics environment).
Do NOT use Python Turtle.  Do NOT use any import statements.  Kojo's built-ins
are always in scope.

Movement:
  forward(n)           — move forward n pixels, drawing a line if pen is down
  back(n)              — move backward n pixels
  right(angle)         — turn right by angle degrees (no movement)
  left(angle)          — turn left by angle degrees (no movement)
  right(angle, radius) — move along a right arc of given radius and angle
  left(angle, radius)  — move along a left arc of given radius and angle
  hop(n)               — move forward n pixels WITHOUT drawing; pen goes down after
  setPosition(x, y)    — teleport to (x, y)
  setHeading(angle)    — point turtle in direction `angle` (0=East, 90=North)
  lineTo(x, y)         — draw a line to (x, y) from current position

Pen / appearance:
  penUp()              — lift pen (stop drawing)
  penDown()            — lower pen (resume drawing)
  setPenColor(color)   — set line colour; e.g. setPenColor(blue), setPenColor(Color(255,0,0))
  setFillColor(color)  — set fill colour for enclosed areas
  setPenThickness(n)   — set line width in pixels
  setBackground(color) — paint canvas background

Colors:
  Named:  red, blue, green, yellow, orange, purple, pink, black, white,
          cyan, magenta, brown, gray, darkGray, lightGray, etc.
  RGB:    Color(r, g, b)          — e.g. Color(255, 128, 0)
  RGBA:   Color(r, g, b, alpha)   — alpha 0-255
  HSL:    cm.hsl(hue, sat, light) — hue 0-360, sat and light 0.0-1.0
  HSLA:   cm.hsla(h, s, l, a)    — a is 0.0-1.0
  noColor                         — transparent / no fill

Control:
  repeat(n) { ... }                      — repeat a block n times
  repeatFor(a to b) { i => ... }         — loop with counter i from a to b (inclusive)
  repeatFor(a until b) { i => ... }      — exclusive upper bound
  def name() { ... }                     — define a parameterless command
  def name(x: Int) { ... }               — define a command with an Int parameter
  def name(x: Double) { ... }            — define a command with a Double parameter
  val x = expr                           — immutable binding
  var x = expr                           — mutable variable
  x = newValue                           — reassign a var

Canvas:
  clear()    — reset canvas and turtle state (position→(0,0), heading→90°, pen down)
  cleari()   — clear() and also hide the turtle
  invisible() — hide the turtle
  visible()   — show the turtle
  setSpeed(slow|medium|fast|superFast)   — animation speed

State save/restore:
  savePosHe()    — save current position and heading
  restorePosHe() — restore to saved position and heading

Example — equilateral triangle with side 100:
  repeat(3) {
    forward(100)
    right(120)
  }

Example — square with fill:
  setFillColor(blue)
  repeat(4) {
    forward(100)
    right(90)
  }

Example — circle approximation radius 50:
  repeat(72) {
    forward(4)
    right(5)
  }

Example — arc (quarter circle, radius 100, rightward):
  right(90, 100)

IMPORTANT: Output ONLY Kojo code inside a ```scala ... ``` fence.
Do NOT wrap in a main() or object.  Write top-level statements only.
--- END KOJO API ---
"""

# ── Library loading snippet (injected into user prompts, mirrors TurtleBench) ─
# In the original, this sets up "import turtle; t = turtle.Turtle()".
# In Kojo, there is no import — the environment is always ready.
# We include a minimal preamble for consistency with the dataset format.
KOJO_PREAMBLE = "// Kojo environment — no imports needed\n"


# ══════════════════════════════════════════════════════════════════════════════
#  SYSTEM PROMPTS
#  Structure mirrors prompts.py exactly:
#    system_prompts[prompting_mode][task_type][...]
# ══════════════════════════════════════════════════════════════════════════════

system_prompts = {

    # ── Chain-of-Thought ──────────────────────────────────────────────────────
    "cot": {
        "scratch": {
            "image_only": (
                "You are a Kojo Geometrician — an expert in reasoning about images "
                "and generating code in the Kojo turtle graphics environment.\n\n"
                + KOJO_API_REF +
                "\nYou need to follow the steps below before generating the answer:\n"
                "(1) Describe the relevant information from the image needed to answer "
                "the question. List all relevant geometric artifacts from the image.\n"
                "(2) Use the information described in (1) to reason step by step about "
                "how to recreate the shape using Kojo commands.\n"
                "(3) Generate the final Kojo code inside a ```scala fence."
            ),

            "image+text": (
                "You are a Kojo Geometrician — an expert in reasoning about images "
                "and generating code in the Kojo turtle graphics environment.\n\n"
                + KOJO_API_REF +
                "\nYou need to follow the steps below before generating the answer:\n"
                "(1) Use the text description provided by the user as an additional "
                "resource to understand the image.\n"
                "(2) Use the information described in (1) to reason step by step about "
                "how to recreate the shape using Kojo commands.\n"
                "(3) Generate the final Kojo code inside a ```scala fence."
            ),

            "text_only": (
                "You are a Kojo Geometrician — an expert in generating turtle graphics "
                "code from text descriptions using the Kojo environment.\n\n"
                + KOJO_API_REF +
                "\nYou need to follow the steps below before generating the answer:\n"
                "(1) Use the text description provided by the user to reason step by "
                "step about how to recreate the shape using Kojo commands.\n"
                "(2) Generate the final Kojo code inside a ```scala fence."
            ),
        },

        "tweak": {
            "code_generation": {
                "image+text": (
                    "You are a Kojo Geometrician — an expert in reasoning about images "
                    "and generating code in the Kojo turtle graphics environment.\n\n"
                    + KOJO_API_REF +
                    "\nYou need to follow the steps below before generating the answer:\n"
                    "(1) Describe the relevant information from the image. List all "
                    "relevant geometric artifacts.\n"
                    "(2) Use the information and the user's instruction to reason step "
                    "by step about the required modification.\n"
                    "(3) Generate the final Kojo code inside a ```scala fence."
                ),
            },
            "code_edit": {
                "image+image": (
                    "You are a Kojo Geometrician — an expert in reasoning about images "
                    "and editing code in the Kojo turtle graphics environment.\n\n"
                    + KOJO_API_REF +
                    "\nYou need to follow the steps below before generating the answer:\n"
                    "(1) Describe the relevant information from both images. List all "
                    "relevant differences between them.\n"
                    "(2) Use the information described in (1) and the code provided by "
                    "the user to reason step by step about the required edit.\n"
                    "(3) Generate the final Kojo code inside a ```scala fence."
                ),
                "image+text": (
                    "You are a Kojo Geometrician — an expert in reasoning about images "
                    "and editing code in the Kojo turtle graphics environment.\n\n"
                    + KOJO_API_REF +
                    "\nYou need to follow the steps below before generating the answer:\n"
                    "(1) Describe the relevant information from the image. List all "
                    "relevant geometric artifacts.\n"
                    "(2) Use the information described in (1), the instruction, and the "
                    "provided code to reason step by step about the required edit.\n"
                    "(3) Generate the final Kojo code inside a ```scala fence."
                ),
            },
        },
    },

    # ── Basic (no CoT) ────────────────────────────────────────────────────────
    "basic": {
        "scratch": {
            "image_only": (
                "The user provides an image of an abstract geometric shape or pattern. "
                "Generate Kojo code that recreates it exactly.\n\n" + KOJO_API_REF
            ),
            "image+text": (
                "The user provides a description of an abstract geometric shape or "
                "pattern and the image illustrating it. Generate Kojo code that "
                "recreates that shape.\n\n" + KOJO_API_REF
            ),
            "text_only": (
                "The user provides a text description of an abstract geometric shape "
                "or pattern. Generate Kojo code that recreates it.\n\n" + KOJO_API_REF
            ),
        },
        "tweak": {
            "code_generation": {
                "image+text": (
                    "The user provides an image of an abstract geometric shape plus an "
                    "instruction. Generate Kojo code that follows the instruction.\n\n"
                    + KOJO_API_REF
                ),
            },
            "code_edit": {
                "image+image": (
                    "The user provides two images showing abstract geometric shapes "
                    "plus the Kojo code that generates the first image. Edit the code "
                    "so it creates the second shape.\n\n" + KOJO_API_REF
                ),
                "image+text": (
                    "The user provides an image of an abstract geometric shape plus the "
                    "Kojo code that generates it. Edit the code to follow the user's "
                    "instruction.\n\n" + KOJO_API_REF
                ),
            },
        },
    },

    # ── Few-shot ──────────────────────────────────────────────────────────────
    "few-shot": {
        "scratch": {
            "image_only": (
                "You are a Kojo Geometrician — an expert in reasoning about images "
                "and generating code in the Kojo turtle graphics environment.\n\n"
                + KOJO_API_REF +
                "\nBefore each task, you are shown 4 example images paired with their "
                "correct Kojo solutions. Use them as reference.\n\n"
                "For the final task:\n"
                "(1) Describe the relevant information from the image. List all "
                "relevant geometric artifacts.\n"
                "(2) Reason step by step about how to recreate the shape in Kojo.\n"
                "(3) Generate the final Kojo code inside a ```scala fence."
            ),
        },
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  USER PROMPTS
#  Structure mirrors prompts.py exactly.
# ══════════════════════════════════════════════════════════════════════════════

_scratch_instruct = (
    "Write Kojo code that creates the exact same shape. "
    "Output only code inside a ```scala fence."
)

user_prompts = {
    "scratch": {
        "image+text": "The image shows {description}. " + _scratch_instruct,
        "image_only": _scratch_instruct,
        "text_only":  "The desired shape is: {description}. " + _scratch_instruct,
    },
    "tweak": {
        "code_edit": {
            "image+image": (
                "This Kojo code generates Shape 1:\n"
                + KOJO_PREAMBLE
                + "\n{variables}\n{code}\n\n"
                "Edit the code so that it creates Shape 2."
            ),
            "image+text": (
                "This Kojo code generates the given shape:\n"
                + KOJO_PREAMBLE
                + "\n{variables}\n{code}\n\n"
                "Edit the code so that it {query}"
            ),
        },
        "code_generation": {
            "image+text": (
                "Write Kojo code that {query} "
                "Output only code inside a ```scala fence."
            ),
        },
    },
    "few_shot": {
        # Each few-shot example: show the code that produces the image
        "scratch": KOJO_PREAMBLE + "\n{variables}\n{code}",
    },
}

# Appended to every user prompt — mirrors TurtleBench's user_prompt_final_piece
# In the original: "Provide a complete piece of code starting with:\nimport turtle\n..."
# In Kojo: no imports; we just tell the model to start with cleari() or clear().
user_prompt_final_piece = (
    "Provide a complete piece of code. Start with the following preamble "
    "(do not repeat it in your explanation, only in the code fence):\n"
    + KOJO_PREAMBLE
    + "\n{variables}"
)
