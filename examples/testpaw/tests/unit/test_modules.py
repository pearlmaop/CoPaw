from testpaw.channels.manager import ChannelManager
from testpaw.crons import CronManager
from testpaw.envs import EnvManager
from testpaw.local_models import LocalModelManager
from testpaw.mcp import MCPClientManager
from testpaw.memory import MemoryManager
from testpaw.providers.manager import ProviderManager
from testpaw.token_usage import TokenUsageTracker
from testpaw.tokenizer import estimate_tokens
from testpaw.tunnel import TunnelManager
from testpaw.approvals import ApprovalService
from testpaw.utils import short_id
from testpaw.agents import AgentRegistry
from testpaw.security.skill_scanner import SkillScanner


def test_channel_manager_console_send() -> None:
    manager = ChannelManager(["console"])
    assert manager.list_channels() == ["console"]
    out = manager.send("console", "u1", "hello")
    assert out == "[console:u1] hello"


def test_cron_manager_add_list_remove() -> None:
    manager = CronManager()
    manager.add_job("job1", 10, "ping")
    jobs = manager.list_jobs()
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == "job1"
    assert manager.remove_job("job1") is True


def test_mcp_manager_register_and_remove() -> None:
    manager = MCPClientManager()
    manager.register("search", {"url": "http://localhost"})
    assert "search" in manager.list_clients()
    assert manager.remove("search") is True


def test_memory_manager_append_and_clear() -> None:
    memory = MemoryManager()
    memory.append("s1", "u:hi")
    memory.append("s1", "a:hello")
    assert memory.list_messages("s1") == ["u:hi", "a:hello"]
    memory.clear("s1")
    assert memory.list_messages("s1") == []


def test_skill_scanner_findings() -> None:
    scanner = SkillScanner()
    bad = scanner.scan("please call os.system('ls')")
    assert bad.safe is False
    assert "os.system" in bad.findings
    ok = scanner.scan("just summarize text")
    assert ok.safe is True


def test_provider_manager_switch_and_configure() -> None:
    manager = ProviderManager()

    providers = manager.list_providers()
    ids = sorted(p["provider_id"] for p in providers)
    assert ids == ["mock", "openai-compatible"]

    manager.configure_provider(
        "openai-compatible",
        model="gpt-4.1-mini",
        base_url="https://api.openai.com/v1",
        api_key="",
    )
    manager.activate("openai-compatible")

    assert manager.get_active_model() == "openai-compatible/gpt-4.1-mini"
    reply = manager.generate("hello")
    assert "missing API key" in reply


def test_env_manager_set_get() -> None:
    env = EnvManager()
    env.set("TESTPAW_ENV_KEY", "v")
    assert env.get("TESTPAW_ENV_KEY") == "v"


def test_local_model_manager_register_remove() -> None:
    mgr = LocalModelManager()
    mgr.register("m1", "llamacpp", "/tmp/m1")
    assert len(mgr.list_models()) == 1
    assert mgr.remove("m1") is True


def test_token_usage_and_tokenizer() -> None:
    tracker = TokenUsageTracker()
    tracker.add(10, 5)
    summary = tracker.summary()
    assert summary["total_tokens"] == 15
    assert estimate_tokens("hello world") > 0


def test_tunnel_manager_flow() -> None:
    mgr = TunnelManager()
    open_state = mgr.open(8088)
    assert open_state["active"] is True
    assert "8088" in open_state["public_url"]
    close_state = mgr.close()
    assert close_state["active"] is False


def test_approval_service_flow() -> None:
    svc = ApprovalService()
    svc.request("r1", {"tool": "x"})
    assert len(svc.list_pending()) == 1
    decided = svc.decide("r1", approved=False)
    assert decided["status"] == "denied"


def test_short_id_and_agent_registry() -> None:
    sid = short_id(6)
    assert len(sid) == 6
    reg = AgentRegistry()
    reg.upsert("qa", "QA Agent")
    profiles = reg.list_profiles()
    ids = sorted(p["agent_id"] for p in profiles)
    assert ids == ["default", "qa"]
