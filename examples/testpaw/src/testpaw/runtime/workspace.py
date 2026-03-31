from __future__ import annotations

from dataclasses import dataclass

from testpaw.channels.manager import ChannelManager
from testpaw.mcp.manager import MCPClientManager
from testpaw.memory.manager import MemoryManager
from testpaw.providers.manager import ProviderManager
from testpaw.runtime.graph import AgentGraphBuilder
from testpaw.runtime.session_store import SessionStore
from testpaw.runtime.tools import build_default_tool_registry
from testpaw.security.skill_scanner import SkillScanner
from testpaw.security.tool_guard import ToolGuardEngine


@dataclass
class Workspace:
    agent_id: str
    provider_state_path: str | None = None

    def __post_init__(self) -> None:
        self.provider_manager = ProviderManager(
            state_path=self.provider_state_path,
        )
        self.tool_guard = ToolGuardEngine()
        self.skill_scanner = SkillScanner()
        self.tools = build_default_tool_registry()
        self.session_store = SessionStore()
        self.memory_manager = MemoryManager()
        self.mcp_manager = MCPClientManager()
        self.channel_manager = ChannelManager(["console"])
        self.graph = None
        self.started = False

    async def start(self) -> None:
        builder = AgentGraphBuilder(
            tool_guard=self.tool_guard,
            tools=self.tools,
            model_reply=self.provider_manager.generate,
        )
        self.graph = builder.compile()
        self.started = True

    async def stop(self) -> None:
        self.started = False
        self.graph = None

    async def invoke(self, text: str) -> dict:
        if not self.started or self.graph is None:
            raise RuntimeError("Workspace is not started")

        scan_result = self.skill_scanner.scan(text)
        if not scan_result.safe:
            return {
                "response": (
                    "Request blocked by skill scanner: "
                    + ", ".join(scan_result.findings)
                ),
                "trace": ["skill_scanner"],
            }

        final_state = self.graph.invoke(
            {
                "input_text": text,
                "trace": [],
            },
        )
        return dict(final_state)

    async def chat(
        self,
        *,
        session_id: str,
        user_id: str,
        text: str,
        channel: str = "console",
    ) -> dict:
        final_state = await self.invoke(text)
        response = str(final_state.get("response", ""))
        self.memory_manager.append(session_id, f"user:{text}")
        self.memory_manager.append(session_id, f"assistant:{response}")
        self.session_store.put(
            session_id,
            {
                "agent_id": self.agent_id,
                "user_id": user_id,
                "last_input": text,
                "last_response": response,
                "trace": list(final_state.get("trace", [])),
            },
        )
        dispatch = self.channel_manager.send(channel, user_id, response)
        return {
            "answer": response,
            "trace": list(final_state.get("trace", [])),
            "dispatch": dispatch,
        }

    async def handle_user_message(self, text: str) -> str:
        result = await self.chat(session_id="default", user_id="local", text=text)
        return result["answer"]
