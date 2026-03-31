from __future__ import annotations

import json
from urllib import error

from testpaw.providers.manager import ProviderManager
from testpaw.providers.openai_compatible import OpenAICompatibleProvider


def test_provider_manager_persistence(tmp_path) -> None:
    state_file = tmp_path / "providers.json"

    manager = ProviderManager(state_path=str(state_file))
    manager.configure_provider(
        "openai-compatible",
        model="gpt-4.1-mini",
        base_url="https://api.openai.com/v1",
        api_key="sk-demo",
    )
    manager.activate("openai-compatible")

    assert state_file.exists()
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved["active_provider"] == "openai-compatible"

    reloaded = ProviderManager(state_path=str(state_file))
    assert reloaded.get_active_model() == "openai-compatible/gpt-4.1-mini"


def test_openai_provider_retry_then_success(monkeypatch) -> None:
    provider = OpenAICompatibleProvider(api_key="sk-demo", max_retries=2)

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            payload = {
                "choices": [{"message": {"content": "ok reply"}}],
            }
            return json.dumps(payload).encode("utf-8")

    calls = {"n": 0}

    def fake_urlopen(req, timeout=30):
        _ = req, timeout
        calls["n"] += 1
        if calls["n"] == 1:
            raise error.URLError("temporary network error")
        return _Resp()

    out = provider.generate("hello", urlopen_fn=fake_urlopen)
    assert out == "ok reply"
    assert calls["n"] == 2


def test_openai_provider_no_key_returns_structured_error() -> None:
    provider = OpenAICompatibleProvider(api_key="")
    out = provider.generate("hello")
    assert "[openai-compatible/error][not-configured]" in out
