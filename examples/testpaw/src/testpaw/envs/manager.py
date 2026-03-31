from __future__ import annotations

import os


class EnvManager:
    def get(self, key: str, default: str = "") -> str:
        return os.environ.get(key, default)

    def set(self, key: str, value: str) -> None:
        os.environ[key] = value

    def dump(self, keys: list[str]) -> dict[str, str]:
        return {k: os.environ.get(k, "") for k in keys}
