from __future__ import annotations


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    def get(self, session_id: str) -> dict:
        return dict(self._sessions.get(session_id, {}))

    def put(self, session_id: str, state: dict) -> None:
        self._sessions[session_id] = dict(state)

    def list_session_ids(self) -> list[str]:
        return sorted(self._sessions.keys())
