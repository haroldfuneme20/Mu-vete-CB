"""LocalProvider (stub documentado, T093).

Punto de extensión para un modelo local (p. ej. Ollama en http://localhost:11434). No se
usa en el MVP: lanza un error y el FallbackProvider responde con MockProvider.
"""

from __future__ import annotations

from agent.providers.base import ProviderError


class LocalProvider:
    name = "local"

    def generate(self, prompt: str) -> str:
        raise ProviderError("LocalProvider no está configurado en el MVP")
