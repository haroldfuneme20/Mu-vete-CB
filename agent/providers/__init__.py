"""Fábrica de proveedores (T029b, T094): LLM_PROVIDER=mock|gemini|groq|local."""

from __future__ import annotations

from agent.providers.base import LLMProvider
from agent.providers.fallback import FallbackProvider
from agent.providers.mock import MockProvider


def build_provider(name: str, gemini_key: str | None = None,
                   groq_key: str | None = None) -> FallbackProvider:
    name = (name or "mock").lower()
    primary: LLMProvider | None = None
    if name == "gemini" and gemini_key:
        from agent.providers.gemini import GeminiProvider

        primary = GeminiProvider(gemini_key)
    elif name == "groq" and groq_key:
        from agent.providers.groq import GroqProvider

        primary = GroqProvider(groq_key)
    elif name == "local":
        from agent.providers.local import LocalProvider

        primary = LocalProvider()
    elif name in ("gemini", "groq"):
        # clave ausente → sin principal: MockProvider (FR-031)
        primary = _MissingKey(name)
    return FallbackProvider(primary, MockProvider())


class _MissingKey:
    def __init__(self, name: str):
        self.name = name

    def generate(self, prompt: str) -> str:
        raise RuntimeError(f"falta la clave de API para {self.name}")


__all__ = ["build_provider", "FallbackProvider", "MockProvider", "LLMProvider"]
