from __future__ import annotations


class LocalModelManager:
    def __init__(self) -> None:
        self._models: dict[str, dict] = {}

    def register(self, model_id: str, backend: str, path: str = "") -> dict:
        info = {"model_id": model_id, "backend": backend, "path": path}
        self._models[model_id] = info
        return info

    def list_models(self) -> list[dict]:
        return list(self._models.values())

    def remove(self, model_id: str) -> bool:
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False
