"""GeminiProvider por HTTP directo (sin SDK), timeout 6 s (T091)."""

from __future__ import annotations

import httpx

from agent.providers.base import ProviderError

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", timeout_s: float = 6.0):
        self.api_key, self.model, self.timeout_s = api_key, model, timeout_s

    def generate(self, prompt: str) -> str:
        r = httpx.post(
            URL.format(model=self.model),
            params={"key": self.api_key},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.2, "maxOutputTokens": 400}},
            timeout=self.timeout_s,
        )
        if r.status_code != 200:
            raise ProviderError(f"Gemini HTTP {r.status_code}")
        try:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as exc:
            raise ProviderError("Respuesta de Gemini sin texto") from exc
