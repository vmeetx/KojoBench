"""
Usage:
  python runs/run.py claude      -- score Claude's kojo files, open results window
  python runs/run.py qwen        -- call LM Studio Qwen, generate + score, open window
  python runs/run.py compare     -- open GT vs Claude vs Qwen side-by-side window
"""
import sys, subprocess
from pathlib import Path

cmds = {
    "claude":  "eval_claude_proxy.py",
    "qwen":    "eval_lmstudio.py",
    "compare": "compare_ui.py",
}

if len(sys.argv) < 2 or sys.argv[1] not in cmds:
    print("Usage: python runs/run.py [claude | qwen | compare]")
    sys.exit(1)

script = Path(__file__).parent / cmds[sys.argv[1]]
subprocess.run([sys.executable, str(script)])
