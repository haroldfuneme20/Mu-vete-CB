"""GroqProvider por HTTP directo (API compatible con OpenAI), timeout 6 s (T092)."""

from __future__ import annotations

import httpx

from agent.providers.base import ProviderError

URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant", timeout_s: float = 6.0):
        self.api_key, self.model, self.timeout_s = api_key, model, timeout_s

    def generate(self, prompt: str) -> str:
        r = httpx.post(
            URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "temperature": 0.2, "max_tokens": 400,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=self.timeout_s,
        )
        if r.status_code != 200:
            raise ProviderError(f"Groq HTTP {r.status_code}")
        try:
            return r.json()["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise ProviderError("Respuesta de Groq sin texto") from exc
