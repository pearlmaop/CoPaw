from __future__ import annotations

from typing import Protocol


class ChatProvider(Protocol):
    provider_id: str

    def model_name(self) -> str:
        ...

    def generate(self, prompt: str) -> str:
        ...

    def configure(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        ...

    def as_dict(self) -> dict:
        ...
