from __future__ import annotations

from testpaw.config.models import AgentConfig, AppConfig


class ConfigService:
    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or AppConfig()

    def get(self) -> AppConfig:
        return self._config

    def list_agents(self) -> list[AgentConfig]:
        return list(self._config.agents.values())

    def upsert_agent(self, agent_id: str, *, enabled: bool = True) -> AgentConfig:
        agent = AgentConfig(agent_id=agent_id, enabled=enabled)
        self._config.agents[agent_id] = agent
        return agent

    def set_channels(self, channels: list[str]) -> None:
        self._config.enabled_channels = channels
