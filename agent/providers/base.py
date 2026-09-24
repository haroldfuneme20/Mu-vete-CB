"""Interfaz del proveedor LLM (constitución V): el agente depende de `llm.generate(...)`."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    def generate(self, prompt: str) -> str: ...


class ProviderError(RuntimeError):
    pass
