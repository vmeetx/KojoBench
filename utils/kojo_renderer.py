import hashlib
import os
import shutil
import subprocess
from pathlib import Path

_ROOT    = Path(__file__).parent.parent
_SCALA_HOME = os.environ.get("SCALA_HOME", "")
SCALA    = str(Path(_SCALA_HOME) / "bin" / "scala.bat") if _SCALA_HOME else "scala"
SCALAC   = str(Path(_SCALA_HOME) / "bin" / "scalac.bat") if _SCALA_HOME else "scalac"
JAR      = _ROOT / "renderer" / "kojo-lib-assembly-0.3.3.jar"
CACHE    = _ROOT / ".render_cache"
WORK_DIR = _ROOT / ".render_work"

WRAPPER_TOP = """\
package p1

object KojoHeadless {
  def main(args: Array[String]): Unit = {
    val kojo = net.kogics.kojo.lite.KojoHeadless.create(500, 500)
    val builtins = kojo.builtins

    import builtins._
    import DCanvas._
    import TurtleWorld._

"""

WRAPPER_BOT = """
    exportImageToFile("{output_png}")
  }
}
"""


def render(kojo_code: str, output_png: str) -> tuple[bool, str]:
    CACHE.mkdir(exist_ok=True)
    WORK_DIR.mkdir(exist_ok=True)

    h = hashlib.sha256(kojo_code.encode()).hexdigest()[:16]
    cached = CACHE / f"{h}.png"
    if cached.exists():
        shutil.copy(cached, output_png)
        return True, ""

    work = WORK_DIR / h
    work.mkdir(exist_ok=True)
    p1_dir = work / "p1"
    p1_dir.mkdir(exist_ok=True)

    output_abs = str(Path(output_png).resolve()).replace("\\", "/")
    indented = "\n".join("    " + line for line in kojo_code.splitlines())
    scala_src = WRAPPER_TOP + indented + WRAPPER_BOT.replace("{output_png}", output_abs)

    src_file = p1_dir / "KojoHeadless.wrapped.scala"
    src_file.write_text(scala_src, encoding="utf-8")

    jar_copy = work / JAR.name
    if not jar_copy.exists():
        shutil.copy(JAR, jar_copy)

    compile_result = subprocess.run(
        [SCALAC, "-cp", JAR.name, str(src_file)],
        capture_output=True, text=True, timeout=120,
        cwd=str(work),
    )
    if compile_result.returncode != 0:
        return False, f"compile error:\n{compile_result.stderr.strip()}"

    run_result = subprocess.run(
        [SCALA, "-cp", f".{os.pathsep}{JAR.name}", "p1.KojoHeadless"],
        capture_output=True, text=True, timeout=60,
        cwd=str(work),
    )

    stdout = run_result.stdout + "\n" + run_result.stderr
    print(f"[kojo_renderer] scala output:\n{stdout.strip()}")

    if run_result.returncode != 0:
        return False, f"runtime error:\n{run_result.stderr.strip()}"

    if not Path(output_png).exists():
        return False, f"no PNG produced. stdout:\n{stdout.strip()}"

    shutil.copy(output_png, cached)
    return True, ""


def code_to_image(kojo_code: str, task_name: str, save_path: str) -> bool:
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
