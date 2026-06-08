"""
HuggingFace Inference API model for KojoBench.

=== HOW TO CONFIGURE ===

1. Set HF_TOKEN to your HuggingFace token (read token is enough for public endpoints).
2. Set HF_API_URL to the Inference API endpoint for your chosen model.

   Standard HF Inference API format:
     https://api-inference.huggingface.co/models/<org>/<model-name>

   Examples:
     Llama 3.1 8B Instruct:
       https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct
     Qwen2-VL 7B (multimodal):
       https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct
     InternVL2 (multimodal):
       https://api-inference.huggingface.co/models/OpenGVLab/InternVL2-8B
     Dedicated Inference Endpoint (your own):
       https://<endpoint-name>.endpoints.huggingface.cloud

   To use a different model later: change ONLY HF_API_URL.
   To use a different provider (Replicate, Together, etc.): subclass BaseModel and
   implement get_response() the same way — eval_kojo.py depends only on that interface.

=== MULTIMODAL vs TEXT-ONLY ===

The HF Inference API supports two payload shapes depending on the model:
  - Text-only:      {"inputs": "<prompt>"}
  - Multimodal:     {"inputs": {"text": "...", "image": "<base64>"}}  (model-dependent)

We use the Messages API (chat completions) format where available, which is more
consistent across models. Set USE_MESSAGES_API = True (default) for instruction-tuned
models. Set False for raw text completion models.
"""

import os
import base64
import requests
from pathlib import Path

# ============================================================
#  CONFIGURE THESE TWO LINES
# ============================================================
HF_TOKEN  = "hf_YOUR_TOKEN_HERE"       # ← paste your token
HF_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.1-8B-Instruct"
# ============================================================

USE_MESSAGES_API = True   # True for instruction-tuned models; False for raw completion


def _encode_image(image_path: str) -> str:
    """Return base64-encoded image string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _image_media_type(image_path: str) -> str:
    suffix = Path(image_path).suffix.lower()
    return {"jpg": "image/jpeg", ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", ".png": "image/png",
            ".webp": "image/webp"}.get(suffix, "image/png")


class HFModel:
    """
    Generic wrapper for HuggingFace Inference API (text + multimodal).

    Implements the same interface as the original TurtleBench model classes
    so eval_kojo.py can use it transparently:

        model.get_response(system_message, user_message,
                           base_image=None, result_image=None,
                           few_shot=False)
        → str  (raw text response)
    """

    def __init__(self, token: str = HF_TOKEN, api_url: str = HF_API_URL):
        if token == "hf_YOUR_TOKEN_HERE":
            raise ValueError(
                "Set HF_TOKEN in models/hf_model.py before running evaluation."
            )
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.api_url = api_url

    # ------------------------------------------------------------------
    # Public interface (mirrors original GPT/Gemini model classes)
    # ------------------------------------------------------------------

    def get_response(
        self,
        system_message: str,
        user_message: str,
        base_image: str | None = None,
        result_image: str | None = None,
        few_shot: bool = False,
    ) -> str:
        """
        Call the HF Inference API and return the raw text response.

        base_image / result_image: paths to PNG files on disk (optional).
        When images are provided, they are base64-encoded and attached as
        multimodal content blocks (OpenAI-compatible format used by many
        HF models). Text-only models will ignore image content blocks
        gracefully if USE_MESSAGES_API is False — in that case images
        are silently dropped and only the text prompt is sent.
        """
        if USE_MESSAGES_API:
            return self._call_messages_api(
                system_message, user_message, base_image, result_image
            )
        else:
            return self._call_text_api(system_message, user_message)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_messages_api(
        self,
        system_message: str,
        user_message: str,
        base_image: str | None,
        result_image: str | None,
    ) -> str:
        """
        Use the /v1/chat/completions compatible endpoint.
        Most modern instruction-tuned models on HF support this.
        Endpoint format: <base_url>/v1/chat/completions
        """
        # Build the URL — if already ends with /v1/chat/completions keep it,
        # otherwise append it for standard HF hosted models.
        url = self.api_url
        if not url.endswith("/v1/chat/completions"):
            url = url.rstrip("/") + "/v1/chat/completions"

        # Build user content — text first, then optional images
        user_content = []
        user_content.append({"type": "text", "text": user_message})

        if base_image and Path(base_image).exists():
            b64 = _encode_image(base_image)
            mt  = _image_media_type(base_image)
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mt};base64,{b64}"},
            })

        if result_image and Path(result_image).exists():
            b64 = _encode_image(result_image)
            mt  = _image_media_type(result_image)
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mt};base64,{b64}"},
            })

        payload = {
            "model":    self.api_url.rstrip("/").split("/")[-1],  # model name hint
            "messages": [
                {"role": "system",  "content": system_message},
                {"role": "user",    "content": user_content},
            ],
            "max_tokens": 2048,
            "temperature": 0.0,
        }

        resp = requests.post(url, headers=self.headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # Handle both HF Messages API format and raw inference API format
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        if "generated_text" in data:
            return data["generated_text"]
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        raise ValueError(f"Unexpected API response format: {list(data.keys())}")

    def _call_text_api(self, system_message: str, user_message: str) -> str:
        """
        Fall back to raw text completion endpoint.
        Images are not supported in this mode.
        """
        prompt = f"{system_message}\n\n{user_message}"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 2048}}
        resp = requests.post(
            self.api_url, headers=self.headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        if "generated_text" in data:
            return data["generated_text"]
        raise ValueError(f"Unexpected API response format: {list(data.keys())}")
