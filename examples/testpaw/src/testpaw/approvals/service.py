from __future__ import annotations

import time


class ApprovalService:
    def __init__(self) -> None:
        self._pending: dict[str, dict] = {}

    def request(self, request_id: str, payload: dict) -> dict:
        item = {
            "request_id": request_id,
            "payload": payload,
            "status": "pending",
            "created_at": time.time(),
        }
        self._pending[request_id] = item
        return dict(item)

    def decide(self, request_id: str, approved: bool) -> dict:
        if request_id not in self._pending:
            raise ValueError("request not found")
        self._pending[request_id]["status"] = "approved" if approved else "denied"
        return dict(self._pending[request_id])

    def list_pending(self) -> list[dict]:
        return [dict(v) for v in self._pending.values() if v["status"] == "pending"]
