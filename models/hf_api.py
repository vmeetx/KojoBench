"""
models/hf_api.py

HuggingFace Inference API model for KojoBench.
Uses the serverless HF Inference API — no local GPU needed.

Set HF_TOKEN in your environment (.env or Colab secret):
  HF_TOKEN=hf_...

Default model: Qwen/Qwen3-32B (reasoning, enable_thinking=True)
Override with: HF_MODEL=deepseek-ai/DeepSeek-R1-Distill-Qwen-32B

Usage:
  from models.hf_api import HFApiModel
  model = HFApiModel()
  response = model.get_response(system_message, user_message)
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from huggingface_hub import InferenceClient
except ImportError:
    raise ImportError("huggingface_hub required: pip install huggingface_hub")

_DEFAULT_MODEL = "Qwen/Qwen3-32B"

HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_MODEL = os.environ.get("HF_MODEL", _DEFAULT_MODEL)

# Models that use enable_thinking instead of returning reasoning_content
_THINKING_FLAG_MODELS = {"Qwen/Qwen3-32B", "Qwen/Qwen3-8B", "Qwen/Qwen3-14B"}


class HFApiModel:
    """
    Wraps the HF Inference API with the same interface as LMStudioModel
    so eval_kojobench2.py works unchanged.

        model.get_response(system_message, user_message) -> str
    """

    def __init__(self, model: str = HF_MODEL, token: str = HF_TOKEN):
        if not token:
            raise ValueError(
                "HF_TOKEN is required. Set it in .env or as a Colab secret."
            )
        self.model  = model
        self.client = InferenceClient(api_key=token)
        print(f"[hf_api] model: {self.model}")

    def get_response(
        self,
        system_message: str,
        user_message:   str,
        base_image:     str | None = None,
        result_image:   str | None = None,
        few_shot:       bool       = False,
    ) -> str:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user",   "content": user_message},
        ]

        # Qwen3 uses enable_thinking; R1-Distill returns reasoning_content
        use_thinking_flag = self.model in _THINKING_FLAG_MODELS
        extra = {"enable_thinking": True} if use_thinking_flag else {}

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=8192,
            temperature=0.0 if not use_thinking_flag else None,
            extra_body=extra if extra else None,
        )

        msg = response.choices[0].message

        # Capture reasoning trace if available (R1-Distill style)
        reasoning = getattr(msg, "reasoning_content", None) or ""
        content   = msg.content or ""

        if reasoning:
            return f"<think>\n{reasoning}\n</think>\n\n{content}"
        return content
