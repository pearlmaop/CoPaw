from __future__ import annotations


class MCPClientManager:
    def __init__(self) -> None:
        self._clients: dict[str, dict] = {}

    def register(self, name: str, config: dict) -> None:
        self._clients[name] = dict(config)

    def list_clients(self) -> dict[str, dict]:
        return dict(self._clients)

    def remove(self, name: str) -> bool:
        if name in self._clients:
            del self._clients[name]
            return True
        return False
