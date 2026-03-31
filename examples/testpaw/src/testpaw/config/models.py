from __future__ import annotations

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    agent_id: str
    enabled: bool = True
    model: str = "mock/mock-chat-1"


class AppConfig(BaseModel):
    app_name: str = "testpaw"
    default_agent: str = "default"
    agents: dict[str, AgentConfig] = Field(
        default_factory=lambda: {"default": AgentConfig(agent_id="default")},
    )
    enabled_channels: list[str] = Field(default_factory=lambda: ["console"])
