from __future__ import annotations

from testpaw.providers.base import ChatProvider


class MockChatProvider(ChatProvider):
    def __init__(self, provider_id: str = "mock", model: str = "mock-chat-1"):
        self.provider_id = provider_id
        self.model = model

    def model_name(self) -> str:
        return f"{self.provider_id}/{self.model}"

    def generate(self, prompt: str) -> str:
        return f"[{self.model_name()}] {prompt}"

    def configure(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        _ = base_url, api_key
        if model is not None and model.strip():
            self.model = model.strip()

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model": self.model,
            "configured": True,
        }
