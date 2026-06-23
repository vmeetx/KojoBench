"""
LM Studio eval: calls local Qwen model via OpenAI-compatible API.
Same system prompt + same 10 queries as Claude proxy eval.
Renders each result, scores NSS + KCSS, shows live UI window.
Requires LM Studio running at http://localhost:1234 with a model loaded.
"""
import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from models.openai_compat import OpenAICompatModel
from eval_engine import SYSTEM_PROMPT, TASKS, load_query, extract_code, render_code, score_task, show_window

OUT_DIR = Path(__file__).parent / "qwen_rendered"
OUT_DIR.mkdir(exist_ok=True)

_THINK_RE = re.compile(r'<think>.*?</think>', re.DOTALL)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1, help="Resume from this task number")
    parser.add_argument("--skip-existing", action="store_true", help="Skip tasks that already have a rendered PNG")
    args = parser.parse_args()

    try:
        model = OpenAICompatModel(provider="lmstudio", max_tokens=8192, temperature=0.0)
    except Exception as e:
        print(f"ERROR: Cannot connect to LM Studio — {e}")
        print("Start LM Studio and load a model at http://localhost:1234")
        sys.exit(1)

    print(f"[LM Studio] model={model.model}\n")
    results = []

    for t in [t for t in TASKS if t >= args.start]:
        query = load_query(t)
        print(f"  Task {t}: generating...", end=" ", flush=True)

        try:
            response = model.get_response(SYSTEM_PROMPT, query)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append(score_task(t, ""))
            continue

        # Strip think block before extracting code
        clean = _THINK_RE.sub("", response).strip()
        code  = extract_code(clean) or extract_code(response)
        print(f"got {len(code)} chars code — rendering...", end=" ", flush=True)

        rendered = render_code(t, code, OUT_DIR)
        print("ok" if rendered else "FAILED")

        # Save
        (OUT_DIR / f"task{t}_response.txt").write_text(response, encoding="utf-8")
        if code:
            (OUT_DIR / f"task{t}.kojo").write_text(code, encoding="utf-8")

        r = score_task(t, code, rendered)
        nss_str = f"NSS={r['nss']*100:.0f}%" if r["nss"] is not None else "NSS=n/a"
        print(f"    KCSS={r['kcss']*100:.0f}%  {nss_str}  lines={r['lines']}  idioms={r['idioms']}")
        results.append(r)
        time.sleep(0.5)

    avg_k = sum(r["kcss"] for r in results) / len(results)
    nss_v = [r["nss"] for r in results if r["nss"] is not None]
    avg_n = sum(nss_v) / len(nss_v) if nss_v else None
    print(f"\n  Avg KCSS: {avg_k*100:.0f}%  Avg NSS: {avg_n*100:.1f}%" if avg_n else f"\n  Avg KCSS: {avg_k*100:.0f}%")

    show_window(f"LM Studio — {model.model}", results, accent="#34d399")

if __name__ == "__main__":
    main()
