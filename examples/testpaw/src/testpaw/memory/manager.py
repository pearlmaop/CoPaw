from __future__ import annotations


class MemoryManager:
    def __init__(self) -> None:
        self._messages: dict[str, list[str]] = {}

    def append(self, session_id: str, message: str) -> None:
        self._messages.setdefault(session_id, []).append(message)

    def list_messages(self, session_id: str) -> list[str]:
        return list(self._messages.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self._messages.pop(session_id, None)
