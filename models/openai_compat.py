"""
models/openai_compat.py

Single OpenAI-compatible client that works with any provider that copies
the OpenAI Chat Completions API format — LM Studio, Groq, Together, Fireworks,
OpenRouter, Mistral, etc.

Configure via environment variables or pass directly:

    base_url  — e.g. http://localhost:1234/v1  (LM Studio)
                     https://api.groq.com/openai/v1  (Groq)
    api_key   — dummy string for local servers; real key for cloud providers
    model     — model ID as the provider names it

Environment variables (all optional, fall back to defaults):
    MODEL_BASE_URL   — provider base URL
    MODEL_API_KEY    — API key
    MODEL_NAME       — model identifier
"""

import os
import re
import base64
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("pip install openai")

# ── Presets: common providers ─────────────────────────────────────────────────
PROVIDERS = {
    "lmstudio":   {"base_url": "http://localhost:1234/v1",          "api_key": "lm-studio"},
    "groq":       {"base_url": "https://api.groq.com/openai/v1",    "api_key": os.environ.get("GROQ_API_KEY", "")},
    "together":   {"base_url": "https://api.together.xyz/v1",       "api_key": os.environ.get("TOGETHER_API_KEY", "")},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",      "api_key": os.environ.get("OPENROUTER_API_KEY", "")},
    "fireworks":  {"base_url": "https://api.fireworks.ai/inference/v1", "api_key": os.environ.get("FIREWORKS_API_KEY", "")},
}

_THINK_TAG_RE = re.compile(r'<think>(.*?)</think>', re.DOTALL)


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _media_type(path: str) -> str:
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png",  ".webp": "image/webp"}.get(
        Path(path).suffix.lower(), "image/png")


class OpenAICompatModel:
    """
    Drop-in replacement for LMStudioModel and HFApiModel.
    Same get_response() interface; works with any OpenAI-compatible provider.

    Usage:
        # LM Studio (local)
        model = OpenAICompatModel(provider="lmstudio")

        # Groq
        model = OpenAICompatModel(provider="groq", model="qwen/qwen3-32b")

        # Anything else
        model = OpenAICompatModel(
            base_url="https://api.example.com/v1",
            api_key="sk-...",
            model="some-model",
        )
    """

    def __init__(
        self,
        provider: str | None = None,
        base_url: str | None = None,
        api_key:  str | None = None,
        model:    str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ):
        # Resolve base_url and api_key from preset or env
        if provider and provider in PROVIDERS:
            preset = PROVIDERS[provider]
            base_url = base_url or preset["base_url"]
            api_key  = api_key  or preset["api_key"]

        base_url = base_url or os.environ.get("MODEL_BASE_URL", "http://localhost:1234/v1")
        api_key  = api_key  or os.environ.get("MODEL_API_KEY",  "lm-studio")
        model    = model    or os.environ.get("MODEL_NAME",      "")

        self.client      = OpenAI(base_url=base_url, api_key=api_key)
        self.max_tokens  = max_tokens
        self.temperature = temperature

        if model:
            self.model = model
        else:
            # Auto-detect first loaded model (LM Studio behaviour)
            models = self.client.models.list().data
            if not models:
                raise RuntimeError("No model loaded / returned by provider.")
            self.model = models[0].id

        print(f"[openai_compat] {base_url}  model={self.model}")

    def get_response(
        self,
        system_message: str,
        user_message:   str,
        base_image:     str | None = None,
        result_image:   str | None = None,
        few_shot:       bool       = False,
    ) -> str:
        user_content = [{"type": "text", "text": user_message}]

        for img_path in [base_image, result_image]:
            if img_path and Path(img_path).exists():
                b64 = _encode_image(img_path)
                mt  = _media_type(img_path)
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mt};base64,{b64}"},
                })

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user",   "content": user_content},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        msg     = response.choices[0].message
        content = msg.content or ""

        # Extract thinking — two styles:
        # 1. Qwen3 / some models: <think>...</think> tags inside content
        think_match = _THINK_TAG_RE.search(content)
        if think_match:
            thinking = think_match.group(1).strip()
            content  = content[think_match.end():].strip()
            return f"<think>\n{thinking}\n</think>\n\n{content}"

        # 2. DeepSeek R1 style: separate reasoning_content field
        reasoning = getattr(msg, "reasoning_content", None) or ""
        if reasoning:
            return f"<think>\n{reasoning}\n</think>\n\n{content}"

        return content
