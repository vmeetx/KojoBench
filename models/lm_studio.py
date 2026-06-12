"""
LM Studio model for KojoBench.

LM Studio runs a local OpenAI-compatible server. Point this at it with:

  LM_STUDIO_BASE_URL  — base URL of the server  (default: http://localhost:1234/v1)
  LM_STUDIO_API_KEY   — any non-empty string     (default: lm-studio)
  LM_STUDIO_MODEL     — model identifier to request  (default: first model from /v1/models)

Either export them in your shell or add a .env file in the repo root (gitignored):

  LM_STUDIO_BASE_URL=http://localhost:1234/v1
  LM_STUDIO_API_KEY=lm-studio
  LM_STUDIO_MODEL=qwen2.5-coder-7b-instruct
"""

import os
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
    raise ImportError("openai package required: pip install openai")

_DEFAULT_BASE_URL = "http://localhost:1234/v1"
_DEFAULT_API_KEY  = "lm-studio"

BASE_URL = os.environ.get("LM_STUDIO_BASE_URL", _DEFAULT_BASE_URL)
API_KEY  = os.environ.get("LM_STUDIO_API_KEY",  _DEFAULT_API_KEY)
MODEL    = os.environ.get("LM_STUDIO_MODEL",     "")


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _media_type(image_path: str) -> str:
    suffix = Path(image_path).suffix.lower()
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png",  ".webp": "image/webp"}.get(suffix, "image/png")


class LMStudioModel:
    """
    OpenAI-compatible wrapper for LM Studio's local server.

    Interface matches the original HFModel so eval_kojo.py works unchanged:

        model.get_response(system_message, user_message,
                           base_image=None, result_image=None,
                           few_shot=False)
        → str
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        api_key:  str = API_KEY,
        model:    str = MODEL,
    ):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        if model:
            self.model = model
        else:
            # Auto-detect: use the first loaded model
            models = self.client.models.list().data
            if not models:
                raise RuntimeError(
                    "LM Studio has no model loaded. Load a model in the LM Studio UI first."
                )
            self.model = models[0].id
            print(f"[lm_studio] Using model: {self.model}")

    def get_response(
        self,
        system_message: str,
        user_message: str,
        base_image: str | None = None,
        result_image: str | None = None,
        few_shot: bool = False,
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
            max_tokens=2048,
            temperature=0.0,
        )
        return response.choices[0].message.content or ""
