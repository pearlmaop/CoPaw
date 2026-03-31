from __future__ import annotations


class TunnelManager:
    def __init__(self) -> None:
        self._active = False
        self._public_url = ""

    def open(self, local_port: int) -> dict:
        self._active = True
        self._public_url = f"https://testpaw-tunnel.local/{local_port}"
        return {"active": self._active, "public_url": self._public_url}

    def close(self) -> dict:
        self._active = False
        self._public_url = ""
        return {"active": self._active, "public_url": self._public_url}

    def status(self) -> dict:
        return {"active": self._active, "public_url": self._public_url}
