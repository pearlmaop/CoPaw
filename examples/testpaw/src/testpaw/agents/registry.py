from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class AgentProfile:
    agent_id: str
    name: str
    description: str = ""


class AgentRegistry:
    def __init__(self) -> None:
        self._profiles: dict[str, AgentProfile] = {
            "default": AgentProfile(agent_id="default", name="Default Agent"),
        }

    def upsert(self, agent_id: str, name: str, description: str = "") -> AgentProfile:
        profile = AgentProfile(agent_id=agent_id, name=name, description=description)
        self._profiles[agent_id] = profile
        return profile

    def list_profiles(self) -> list[dict]:
        return [asdict(p) for p in self._profiles.values()]
