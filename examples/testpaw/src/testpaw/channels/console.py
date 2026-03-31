from __future__ import annotations

from testpaw.channels.base import BaseChannel


class ConsoleChannel(BaseChannel):
    name = "console"

    def send(self, user_id: str, message: str) -> str:
        return f"[{self.name}:{user_id}] {message}"
