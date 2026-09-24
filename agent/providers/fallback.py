"""FallbackProvider (T029b): cualquier fallo del proveedor principal cae en MockProvider."""

from __future__ import annotations

import concurrent.futures
import logging
from collections.abc import Callable

from agent.providers.base import LLMProvider
from agent.providers.mock import MockProvider

log = logging.getLogger("muevete.llm")
TIMEOUT_S = 6.0
_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm")


class FallbackProvider:
    def __init__(self, primary: LLMProvider | None, fallback: LLMProvider | None = None,
                 timeout_s: float = TIMEOUT_S):
        self.primary = primary
        self.fallback = fallback or MockProvider()
        self.timeout_s = timeout_s
        self.last_provider = self.fallback.name
        self.last_reason: str | None = None

    @property
    def name(self) -> str:
        return self.primary.name if self.primary else self.fallback.name

    def generate(self, prompt: str) -> str:
        return self.generate_checked(prompt, None)[0]

    def generate_checked(self, prompt: str,
                         check: Callable[[str], bool] | None) -> tuple[str, str]:
        """Devuelve (texto, proveedor efectivo). `check` valida la salida del principal."""
        if self.primary is not None:
            try:
                fut = _POOL.submit(self.primary.generate, prompt)
                out = fut.result(timeout=self.timeout_s)
                if out and (check is None or check(out)):
                    self.last_provider, self.last_reason = self.primary.name, None
                    return out, self.primary.name
                reason = "salida inválida"
            except concurrent.futures.TimeoutError:
                reason = f"timeout > {self.timeout_s:.0f} s"
            except Exception as exc:  # noqa: BLE001 - cualquier fallo cae en Mock
                reason = f"{type(exc).__name__}: {exc}"
            log.warning("Proveedor %s falló (%s); se usa %s", self.primary.name, reason,
                        self.fallback.name)
            self.last_reason = reason
        out = self.fallback.generate(prompt)
        self.last_provider = self.fallback.name
        return out, self.fallback.name
