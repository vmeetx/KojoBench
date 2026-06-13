"""
utils/kojo_renderer.py
Renders Kojo code to PNG by calling run-kojo-headless.sh.
Works from both Windows (via WSL subprocess) and directly inside WSL.
"""

import hashlib
import os
import shutil
import subprocess
import uuid
from pathlib import Path

_ROOT             = Path(__file__).parent.parent
KOJO_HEADLESS_DIR = _ROOT / "kojo-headless"
CACHE             = _ROOT / ".render_cache"

# Detect if we're already inside WSL or on Windows
_RUNNING_IN_WSL = os.path.exists("/proc/version")

def _to_wsl_path(p: Path) -> str:
    """Convert a Windows absolute path to its WSL /mnt/X/... equivalent."""
    s = str(p.resolve())
    if len(s) >= 2 and s[1] == ":":
        return "/mnt/" + s[0].lower() + "/" + s[3:].replace("\\", "/")
    return s.replace("\\", "/")

# When in WSL, KOJO_HEADLESS_DIR is already a valid Linux path via /mnt/
WSL_WORK_DIR = str(KOJO_HEADLESS_DIR) if _RUNNING_IN_WSL else _to_wsl_path(KOJO_HEADLESS_DIR)


def render(kojo_code: str, output_png: str) -> tuple[bool, str]:
    """
    Render kojo_code and write PNG to output_png.
    Returns (True, "") on success or (False, error_message) on failure.
    Results are cached by SHA-256 of the code.
    """
    h = hashlib.sha256(kojo_code.encode()).hexdigest()[:16]
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"{h}.png"
    if cached.exists():
        shutil.copy(cached, output_png)
        return True, ""

    kojo_filename = f"_render_{uuid.uuid4().hex[:8]}.kojo"
    kojo_file     = KOJO_HEADLESS_DIR / kojo_filename
    kojo_file.write_text(kojo_code, encoding="utf-8")

    produced_png = KOJO_HEADLESS_DIR / kojo_filename.replace(".kojo", ".png")

    try:
        if _RUNNING_IN_WSL:
            # Already in WSL — run the script directly
            cmd = ["bash", "-c",
                   f"cd {WSL_WORK_DIR} && rm -rf p1/ && ./run-kojo-headless.sh {kojo_filename}"]
        else:
            # On Windows — call via wsl
            cmd = ["wsl", "bash", "-c",
                   f"cd {WSL_WORK_DIR} && rm -rf p1/ && ./run-kojo-headless.sh {kojo_filename}"]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )

        stdout = result.stdout + "\n" + result.stderr
        print(f"[kojo_renderer] output:\n{stdout.strip()}")

        if result.returncode != 0:
            return False, f"shell error:\n{result.stderr.strip()}"

        if not produced_png.exists():
            return False, f"no PNG produced.\n{stdout.strip()}"

        shutil.copy(produced_png, output_png)
        CACHE.mkdir(parents=True, exist_ok=True)
        shutil.copy(produced_png, cached)
        return True, ""

    finally:
        if kojo_file.exists():
            kojo_file.unlink()
        if produced_png.exists():
            produced_png.unlink()


def code_to_image(kojo_code: str, task_name: str, save_path: str) -> bool:
    """Wrapper used by eval_kojo.py / calculate_score_kojo.py."""
    if not kojo_code.strip():
        print(f"[kojo_renderer] {task_name}: empty code, skipping")
        return False

    dest_dir = Path(save_path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_png = str(dest_dir / f"{task_name}.png")

    ok, err = render(kojo_code, dest_png)
    if ok:
        print(f"[kojo_renderer] {task_name}: rendered OK -> {dest_png}")
    else:
        print(f"[kojo_renderer] {task_name}: FAILED — {err}")
    return ok