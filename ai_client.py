"""Gemini API client wrapper with guardrails and logging."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pawpal.ai")

_API_KEY = os.getenv("GEMINI_API_KEY")
_MODEL_NAME = "gemini-2.5-flash"


class AIClientError(Exception):
    """Raised when the AI client cannot produce a usable response."""


class GeminiClient:
    """Thin wrapper around google-genai with guardrails."""

    def __init__(self, api_key: str | None = None, model: str = _MODEL_NAME):
        key = api_key or _API_KEY
        if not key:
            raise AIClientError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        self.client = genai.Client(api_key=key)
        self.model_name = model

    def generate_text(self, prompt: str, temperature: float = 0.4) -> str:
        """Plain text generation. Returns the model's text output."""
        logger.info(
            "Calling Gemini (text) | model=%s | chars=%d",
            self.model_name, len(prompt),
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=temperature),
            )
            text = (response.text or "").strip()
            if not text:
                raise AIClientError("Empty response from Gemini.")
            return text
        except AIClientError:
            raise
        except Exception as exc:
            logger.exception("Gemini text call failed")
            raise AIClientError(f"Gemini call failed: {exc}") from exc

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.2,
    ) -> dict[str, Any] | list[Any]:
        """Generation constrained to valid JSON. Raises AIClientError if
        parsing fails."""
        logger.info(
            "Calling Gemini (json) | model=%s | chars=%d",
            self.model_name, len(prompt),
        )
        text = ""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )
            text = (response.text or "").strip()
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("JSON decode failed, content was: %s", text[:300])
            raise AIClientError(
                f"Model did not return valid JSON: {exc}"
            ) from exc
        except Exception as exc:
            logger.exception("Gemini json call failed")
            raise AIClientError(f"Gemini call failed: {exc}") from exc
