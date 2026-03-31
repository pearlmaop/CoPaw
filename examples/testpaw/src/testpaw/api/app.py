from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
import tempfile

from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse, StreamingResponse
from starlette.staticfiles import StaticFiles

from testpaw.agents import AgentRegistry
from testpaw.approvals import ApprovalService
from testpaw.app.multi_agent_manager import MultiAgentManager
from testpaw.config import ConfigService
from testpaw.crons import CronManager
from testpaw.envs import EnvManager
from testpaw.local_models import LocalModelManager
from testpaw.token_usage import TokenUsageTracker
from testpaw.tokenizer import estimate_tokens
from testpaw.tunnel import TunnelManager
from testpaw.runtime.workspace import Workspace
from testpaw.security.skill_scanner import SkillScanner
from testpaw.skills import SkillManager


class ChatRequest(BaseModel):
    text: str = Field(default="")
    user_id: str = Field(default="local-user")
    session_id: str = Field(default="default-session")
    channel: str = Field(default="console")
    agent_id: str = Field(default="default")


class ChatResponse(BaseModel):
    answer: str
    trace: list[str]
    dispatch: str


class CronRequest(BaseModel):
    job_id: str
    every_seconds: int
    message: str


class MCPRegisterRequest(BaseModel):
    name: str
    config: dict = Field(default_factory=dict)


class ProviderActivateRequest(BaseModel):
    provider_id: str


class ProviderConfigRequest(BaseModel):
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None


class ApprovalRequest(BaseModel):
    request_id: str
    payload: dict = Field(default_factory=dict)


class ApprovalDecisionRequest(BaseModel):
    approved: bool


class LocalModelRequest(BaseModel):
    model_id: str
    backend: str
    path: str = ""


class EnvSetRequest(BaseModel):
    key: str
    value: str


class TunnelOpenRequest(BaseModel):
    local_port: int


class SkillToggleRequest(BaseModel):
    enabled: bool


class SkillRunRequest(BaseModel):
    text: str = Field(default="")


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_dir = os.environ.get("TESTPAW_DATA_DIR")
    if not data_dir:
        data_dir = tempfile.mkdtemp(prefix="testpaw-")
    manager = MultiAgentManager(data_dir=data_dir)
    config = ConfigService()
    cron = CronManager()
    scanner = SkillScanner()
    approvals = ApprovalService()
    envs = EnvManager()
    local_models = LocalModelManager()
    tunnel = TunnelManager()
    token_usage = TokenUsageTracker()
    agent_registry = AgentRegistry()
    skills = SkillManager()

    default_ws = await manager.get_agent(config.get().default_agent)

    app.state.multi_agent_manager = manager
    app.state.config_service = config
    app.state.cron_manager = cron
    app.state.skill_scanner = scanner
    app.state.approval_service = approvals
    app.state.env_manager = envs
    app.state.local_model_manager = local_models
    app.state.tunnel_manager = tunnel
    app.state.token_usage = token_usage
    app.state.agent_registry = agent_registry
    app.state.skill_manager = skills
    app.state.default_workspace = default_ws
    try:
        yield
    finally:
        await manager.stop_all()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    console_dir = Path(__file__).resolve().parent / "console"
    app.mount("/assets", StaticFiles(directory=str(console_dir)), name="assets")

    @app.get("/")
    async def home() -> HTMLResponse:
        return HTMLResponse((console_dir / "index.html").read_text(encoding="utf-8"))

    @app.get("/health")
    async def health() -> dict:
        manager: MultiAgentManager = app.state.multi_agent_manager
        return {
            "ok": True,
            "loaded_agents": manager.list_loaded_agents(),
        }

    @app.post("/chat", response_model=ChatResponse)
    async def chat(payload: ChatRequest) -> ChatResponse:
        manager: MultiAgentManager = app.state.multi_agent_manager
        workspace: Workspace = await manager.get_agent(payload.agent_id)
        result = await workspace.chat(
            session_id=payload.session_id,
            user_id=payload.user_id,
            text=payload.text,
            channel=payload.channel,
        )
        token_usage: TokenUsageTracker = app.state.token_usage
        token_usage.add(
            input_tokens=estimate_tokens(payload.text),
            output_tokens=estimate_tokens(str(result.get("answer", ""))),
        )
        return ChatResponse(
            answer=str(result.get("answer", "")),
            trace=list(result.get("trace", [])),
            dispatch=str(result.get("dispatch", "")),
        )

    @app.post("/chat/stream")
    async def chat_stream(payload: ChatRequest):
        manager: MultiAgentManager = app.state.multi_agent_manager
        workspace: Workspace = await manager.get_agent(payload.agent_id)
        result = await workspace.chat(
            session_id=payload.session_id,
            user_id=payload.user_id,
            text=payload.text,
            channel=payload.channel,
        )
        answer = str(result.get("answer", ""))
        words = answer.split() if answer else [""]

        async def _event_stream():
            for index, token in enumerate(words):
                yield f"data: {index}:{token}\n\n"
            yield "event: done\ndata: done\n\n"

        return StreamingResponse(
            _event_stream(),
            media_type="text/event-stream",
        )

    @app.get("/agents")
    async def list_agents() -> dict:
        cfg: ConfigService = app.state.config_service
        manager: MultiAgentManager = app.state.multi_agent_manager
        registry: AgentRegistry = app.state.agent_registry
        return {
            "configured": [a.model_dump() for a in cfg.list_agents()],
            "loaded": manager.list_loaded_agents(),
            "profiles": registry.list_profiles(),
        }

    @app.post("/agents/{agent_id}")
    async def upsert_agent(agent_id: str) -> dict:
        cfg: ConfigService = app.state.config_service
        manager: MultiAgentManager = app.state.multi_agent_manager
        cfg.upsert_agent(agent_id)
        registry: AgentRegistry = app.state.agent_registry
        registry.upsert(agent_id, name=f"Agent {agent_id}")
        await manager.get_agent(agent_id)
        return {"created": True, "agent_id": agent_id}

    @app.get("/config")
    async def get_config() -> dict:
        cfg: ConfigService = app.state.config_service
        return cfg.get().model_dump()

    @app.post("/config/channels")
    async def set_channels(payload: list[str]) -> dict:
        cfg: ConfigService = app.state.config_service
        cfg.set_channels(payload)
        return {"channels": payload}

    @app.post("/cron/jobs")
    async def add_cron_job(payload: CronRequest) -> dict:
        cron: CronManager = app.state.cron_manager
        job = cron.add_job(
            payload.job_id,
            payload.every_seconds,
            payload.message,
        )
        return {"job": job.__dict__}

    @app.get("/cron/jobs")
    async def list_cron_jobs() -> dict:
        cron: CronManager = app.state.cron_manager
        return {"jobs": cron.list_jobs()}

    @app.delete("/cron/jobs/{job_id}")
    async def delete_cron_job(job_id: str) -> dict:
        cron: CronManager = app.state.cron_manager
        return {"removed": cron.remove_job(job_id)}

    @app.post("/mcp/register")
    async def register_mcp(payload: MCPRegisterRequest) -> dict:
        ws: Workspace = app.state.default_workspace
        ws.mcp_manager.register(payload.name, payload.config)
        return {"clients": ws.mcp_manager.list_clients()}

    @app.get("/mcp/clients")
    async def list_mcp_clients() -> dict:
        ws: Workspace = app.state.default_workspace
        return {"clients": ws.mcp_manager.list_clients()}

    @app.get("/memory/{session_id}")
    async def list_memory(session_id: str) -> dict:
        ws: Workspace = app.state.default_workspace
        return {"messages": ws.memory_manager.list_messages(session_id)}

    @app.post("/skills/scan")
    async def scan_skill(payload: dict) -> dict:
        scanner: SkillScanner = app.state.skill_scanner
        text = str(payload.get("text", ""))
        result = scanner.scan(text)
        return {"safe": result.safe, "findings": result.findings}

    @app.get("/skills")
    async def list_skills() -> dict:
        mgr: SkillManager = app.state.skill_manager
        return {"skills": mgr.list_skills()}

    @app.post("/skills/{skill_id}/enable")
    async def set_skill_enabled(skill_id: str, payload: SkillToggleRequest) -> dict:
        mgr: SkillManager = app.state.skill_manager
        try:
            skill = mgr.set_enabled(skill_id, payload.enabled)
            return {"ok": True, "skill": skill}
        except ValueError:
            return {"ok": False, "error": "skill not found"}

    @app.post("/skills/{skill_id}/run")
    async def run_skill(skill_id: str, payload: SkillRunRequest) -> dict:
        mgr: SkillManager = app.state.skill_manager
        try:
            return mgr.run(skill_id, payload.text)
        except ValueError:
            return {"ok": False, "error": "skill not found"}

    @app.post("/approvals/request")
    async def create_approval(payload: ApprovalRequest) -> dict:
        svc: ApprovalService = app.state.approval_service
        return {"approval": svc.request(payload.request_id, payload.payload)}

    @app.post("/approvals/{request_id}/decision")
    async def decide_approval(
        request_id: str,
        payload: ApprovalDecisionRequest,
    ) -> dict:
        svc: ApprovalService = app.state.approval_service
        return {"approval": svc.decide(request_id, payload.approved)}

    @app.get("/approvals/pending")
    async def list_pending_approvals() -> dict:
        svc: ApprovalService = app.state.approval_service
        return {"pending": svc.list_pending()}

    @app.post("/envs/set")
    async def set_env(payload: EnvSetRequest) -> dict:
        env: EnvManager = app.state.env_manager
        env.set(payload.key, payload.value)
        return {"ok": True, "key": payload.key}

    @app.get("/envs/get/{key}")
    async def get_env(key: str) -> dict:
        env: EnvManager = app.state.env_manager
        return {"key": key, "value": env.get(key)}

    @app.post("/local-models")
    async def register_local_model(payload: LocalModelRequest) -> dict:
        mgr: LocalModelManager = app.state.local_model_manager
        model = mgr.register(payload.model_id, payload.backend, payload.path)
        return {"model": model}

    @app.get("/local-models")
    async def list_local_models() -> dict:
        mgr: LocalModelManager = app.state.local_model_manager
        return {"models": mgr.list_models()}

    @app.delete("/local-models/{model_id}")
    async def remove_local_model(model_id: str) -> dict:
        mgr: LocalModelManager = app.state.local_model_manager
        return {"removed": mgr.remove(model_id)}

    @app.get("/token-usage")
    async def get_token_usage() -> dict:
        tracker: TokenUsageTracker = app.state.token_usage
        return tracker.summary()

    @app.post("/token-usage/reset")
    async def reset_token_usage() -> dict:
        tracker: TokenUsageTracker = app.state.token_usage
        tracker.reset()
        return tracker.summary()

    @app.post("/tokenizer/count")
    async def count_tokens(payload: dict) -> dict:
        text = str(payload.get("text", ""))
        return {"tokens": estimate_tokens(text)}

    @app.post("/tunnel/open")
    async def open_tunnel(payload: TunnelOpenRequest) -> dict:
        mgr: TunnelManager = app.state.tunnel_manager
        return mgr.open(payload.local_port)

    @app.post("/tunnel/close")
    async def close_tunnel() -> dict:
        mgr: TunnelManager = app.state.tunnel_manager
        return mgr.close()

    @app.get("/tunnel/status")
    async def tunnel_status() -> dict:
        mgr: TunnelManager = app.state.tunnel_manager
        return mgr.status()

    @app.get("/providers")
    async def list_providers() -> dict:
        ws: Workspace = app.state.default_workspace
        return {"providers": ws.provider_manager.list_providers()}

    @app.post("/providers/activate")
    async def activate_provider(payload: ProviderActivateRequest) -> dict:
        ws: Workspace = app.state.default_workspace
        ws.provider_manager.activate(payload.provider_id)
        return {
            "active_model": ws.provider_manager.get_active_model(),
        }

    @app.post("/providers/{provider_id}/config")
    async def configure_provider(
        provider_id: str,
        payload: ProviderConfigRequest,
    ) -> dict:
        ws: Workspace = app.state.default_workspace
        ws.provider_manager.configure_provider(
            provider_id,
            model=payload.model,
            base_url=payload.base_url,
            api_key=payload.api_key,
        )
        return {"providers": ws.provider_manager.list_providers()}

    @app.post("/auth/login")
    async def auth_login(payload: dict) -> dict:
        username = str(payload.get("username", ""))
        return {"ok": bool(username), "username": username}

    @app.post("/auth/logout")
    async def auth_logout() -> dict:
        return {"ok": True}

    @app.get("/workspace/info")
    async def workspace_info() -> dict:
        ws: Workspace = app.state.default_workspace
        return {
            "agent_id": ws.agent_id,
            "sessions": ws.session_store.list_session_ids(),
        }

    @app.get("/messages")
    async def list_messages(session_id: str = "default-session") -> dict:
        ws: Workspace = app.state.default_workspace
        return {"messages": ws.memory_manager.list_messages(session_id)}

    @app.get("/files")
    async def list_files() -> dict:
        return {"files": []}

    @app.get("/console/push-messages")
    async def console_push_messages() -> dict:
        return {"messages": []}

    @app.post("/tools/execute")
    async def execute_tool(payload: dict) -> dict:
        ws: Workspace = app.state.default_workspace
        name = str(payload.get("name", ""))
        args = payload.get("args", {})
        if not isinstance(args, dict):
            args = {}
        if not ws.tools.has(name):
            return {"ok": False, "error": "tool not found"}
        return {"ok": True, "result": ws.tools.run(name, args)}

    @app.post("/daemon/restart")
    async def daemon_restart() -> dict:
        return {"ok": True, "action": "restart"}

    @app.get("/chats")
    async def list_chats() -> dict:
        ws: Workspace = app.state.default_workspace
        return {"sessions": ws.session_store.list_session_ids()}

    return app


app = create_app()
