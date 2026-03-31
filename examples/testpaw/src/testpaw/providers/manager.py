from __future__ import annotations

import json
from pathlib import Path

from testpaw.providers.base import ChatProvider
from testpaw.providers.mock_provider import MockChatProvider
from testpaw.providers.openai_compatible import OpenAICompatibleProvider


class ProviderManager:
    """Provider manager with pluggable provider instances."""

    def __init__(self, state_path: str | None = None) -> None:
        self._providers: dict[str, ChatProvider] = {
            "mock": MockChatProvider(),
            "openai-compatible": OpenAICompatibleProvider(),
        }
        self._active_provider_id = "mock"
        self._state_path = Path(state_path).expanduser() if state_path else None
        self._load_state()

    def list_providers(self) -> list[dict]:
        out = []
        for provider_id, provider in self._providers.items():
            item = provider.as_dict()
            item["active"] = provider_id == self._active_provider_id
            out.append(item)
        return out

    def activate(self, provider_id: str) -> None:
        if provider_id not in self._providers:
            raise ValueError(f"Provider not found: {provider_id}")
        self._active_provider_id = provider_id
        self._save_state()

    def configure_provider(
        self,
        provider_id: str,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        if provider_id not in self._providers:
            raise ValueError(f"Provider not found: {provider_id}")
        self._providers[provider_id].configure(
            model=model,
            base_url=base_url,
            api_key=api_key,
        )
        self._save_state()

    def get_active_provider(self) -> ChatProvider:
        return self._providers[self._active_provider_id]

    def get_active_model(self) -> str:
        return self.get_active_provider().model_name()

    def generate(self, prompt: str) -> str:
        return self.get_active_provider().generate(prompt)

    def _save_state(self) -> None:
        if self._state_path is None:
            return
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "active_provider": self._active_provider_id,
            "providers": {
                pid: provider.as_dict()
                for pid, provider in self._providers.items()
            },
        }
        with open(self._state_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def _load_state(self) -> None:
        if self._state_path is None or not self._state_path.exists():
            return
        try:
            with open(self._state_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            active = str(data.get("active_provider", "")).strip()
            if active in self._providers:
                self._active_provider_id = active

            providers = data.get("providers", {})
            if isinstance(providers, dict):
                for pid, conf in providers.items():
                    if pid not in self._providers or not isinstance(conf, dict):
                        continue
                    self._providers[pid].configure(
                        model=conf.get("model"),
                        base_url=conf.get("base_url"),
                        api_key=conf.get("api_key"),
                    )
        except Exception:
            # Keep startup resilient even if state file is corrupted.
            return
