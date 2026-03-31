from __future__ import annotations

from testpaw.channels.base import BaseChannel
from testpaw.channels.console import ConsoleChannel


class ChannelManager:
    def __init__(self, enabled_channels: list[str] | None = None) -> None:
        enabled = enabled_channels or ["console"]
        self._channels: dict[str, BaseChannel] = {}
        if "console" in enabled:
            self._channels["console"] = ConsoleChannel()

    def list_channels(self) -> list[str]:
        return sorted(self._channels.keys())

    def send(self, channel: str, user_id: str, message: str) -> str:
        if channel not in self._channels:
            raise ValueError(f"Channel not enabled: {channel}")
        return self._channels[channel].send(user_id, message)
