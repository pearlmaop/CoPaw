from __future__ import annotations

from pathlib import Path

from testpaw.runtime.workspace import Workspace


class MultiAgentManager:
    def __init__(self, data_dir: str | None = None) -> None:
        self._agents: dict[str, Workspace] = {}
        self._data_dir = Path(data_dir).expanduser() if data_dir else None

    async def get_agent(self, agent_id: str) -> Workspace:
        if agent_id in self._agents:
            return self._agents[agent_id]
        state_path = None
        if self._data_dir is not None:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            state_path = str(self._data_dir / f"providers.{agent_id}.json")

        ws = Workspace(agent_id=agent_id, provider_state_path=state_path)
        await ws.start()
        self._agents[agent_id] = ws
        return ws

    def list_loaded_agents(self) -> list[str]:
        return sorted(self._agents.keys())

    async def stop_all(self) -> None:
        for ws in self._agents.values():
            await ws.stop()
        self._agents.clear()
