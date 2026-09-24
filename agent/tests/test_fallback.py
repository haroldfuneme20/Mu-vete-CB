"""T103: cualquier fallo del proveedor principal cae en MockProvider."""

from __future__ import annotations

import time

from agent.providers import build_provider
from agent.providers.fallback import FallbackProvider

PARSE = "### TAREA: PARSE\n### CONSULTA\nde Paraíso a Portal Tunal"


class Boom:
    name = "boom"

    def generate(self, prompt):
        raise RuntimeError("caído")


class Slow:
    name = "slow"

    def generate(self, prompt):
        time.sleep(0.5)
        return '{"on_topic": true}'


class Garbage:
    name = "garbage"

    def generate(self, prompt):
        return "no es json"


def test_exception_falls_back():
    fb = FallbackProvider(Boom())
    text, used = fb.generate_checked(PARSE, None)
    assert used == "mock" and '"on_topic": true' in text


def test_timeout_falls_back():
    fb = FallbackProvider(Slow(), timeout_s=0.1)
    assert fb.generate_checked(PARSE, None)[1] == "mock"
    assert "timeout" in fb.last_reason


def test_invalid_output_falls_back():
    fb = FallbackProvider(Garbage())
    assert fb.generate_checked(PARSE, lambda s: s.startswith("{"))[1] == "mock"


def test_missing_key_uses_mock():
    fb = build_provider("gemini", gemini_key=None)
    assert fb.generate_checked(PARSE, None)[1] == "mock"


def test_default_is_mock():
    fb = build_provider("mock")
    assert fb.primary is None and fb.generate_checked(PARSE, None)[1] == "mock"
