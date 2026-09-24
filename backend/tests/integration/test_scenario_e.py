"""T105: Escenario E — proveedor externo con clave inválida → Mock sin interrupción."""

from __future__ import annotations

from backend.tests.conftest import mock_client_for
from backend.tests.integration.test_scenario_a import A


def test_invalid_key_falls_back_to_mock(mock_db, tmp_path, monkeypatch):
    import agent.providers.gemini as gem

    def fail(*_a, **_k):
        raise gem.ProviderError("HTTP 400 (clave inválida simulada)")

    monkeypatch.setattr(gem.GeminiProvider, "generate", fail)
    client, core = mock_client_for(mock_db, tmp_path, llm_provider="gemini",
                                   gemini_api_key="invalida")
    with client:
        r = client.post("/api/recommendations", json=A)
        assert r.status_code == 200
        d = r.json()
        assert d["explanation_provider"] == "mock"
        assert d["explanation"]
        assert client.get("/api/health").json()["llm_provider"] == "gemini"
