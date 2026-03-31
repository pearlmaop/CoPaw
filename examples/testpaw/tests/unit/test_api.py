from fastapi.testclient import TestClient

from testpaw.api.app import create_app


def test_health_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert "default" in body["loaded_agents"]


def test_chat_tool_path() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/chat", json={"text": "/calc 3+4"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == "Result: 7"
        assert body["trace"] == ["normalize", "guard", "plan", "run_tool"]
        assert body["dispatch"].startswith("[console:")


def test_chat_model_path() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.post("/chat", json={"text": "hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert "mock/mock-chat-1" in body["answer"]
        assert body["trace"] == ["normalize", "guard", "plan", "model_reply"]
        assert body["dispatch"].startswith("[console:")


def test_module_endpoints() -> None:
    app = create_app()
    with TestClient(app) as client:
        agents = client.get("/agents")
        assert agents.status_code == 200
        assert "configured" in agents.json()

        add_agent = client.post("/agents/qa")
        assert add_agent.status_code == 200

        cfg = client.get("/config")
        assert cfg.status_code == 200
        assert cfg.json()["app_name"] == "testpaw"

        set_channels = client.post("/config/channels", json=["console"])
        assert set_channels.status_code == 200

        add_job = client.post(
            "/cron/jobs",
            json={"job_id": "j1", "every_seconds": 5, "message": "ping"},
        )
        assert add_job.status_code == 200

        list_jobs = client.get("/cron/jobs")
        assert list_jobs.status_code == 200
        assert len(list_jobs.json()["jobs"]) == 1

        mcp = client.post("/mcp/register", json={"name": "demo", "config": {"url": "x"}})
        assert mcp.status_code == 200
        assert "demo" in mcp.json()["clients"]

        scan = client.post("/skills/scan", json={"text": "safe text"})
        assert scan.status_code == 200
        assert scan.json()["safe"] is True

        providers = client.get("/providers")
        assert providers.status_code == 200
        assert len(providers.json()["providers"]) == 2

        cfg_provider = client.post(
            "/providers/openai-compatible/config",
            json={"model": "gpt-4.1-mini", "api_key": ""},
        )
        assert cfg_provider.status_code == 200

        activate_provider = client.post(
            "/providers/activate",
            json={"provider_id": "openai-compatible"},
        )
        assert activate_provider.status_code == 200
        assert (
            activate_provider.json()["active_model"]
            == "openai-compatible/gpt-4.1-mini"
        )

        approval = client.post(
            "/approvals/request",
            json={"request_id": "r1", "payload": {"tool": "run"}},
        )
        assert approval.status_code == 200

        pending = client.get("/approvals/pending")
        assert pending.status_code == 200
        assert len(pending.json()["pending"]) == 1

        decision = client.post(
            "/approvals/r1/decision",
            json={"approved": True},
        )
        assert decision.status_code == 200
        assert decision.json()["approval"]["status"] == "approved"

        env_set = client.post("/envs/set", json={"key": "TP_TEST", "value": "1"})
        assert env_set.status_code == 200
        env_get = client.get("/envs/get/TP_TEST")
        assert env_get.status_code == 200
        assert env_get.json()["value"] == "1"

        local_model = client.post(
            "/local-models",
            json={"model_id": "llm-a", "backend": "llamacpp", "path": "/tmp/m"},
        )
        assert local_model.status_code == 200
        local_models = client.get("/local-models")
        assert local_models.status_code == 200
        assert len(local_models.json()["models"]) == 1

        token_usage = client.get("/token-usage")
        assert token_usage.status_code == 200
        assert token_usage.json()["total_tokens"] >= 0

        token_count = client.post("/tokenizer/count", json={"text": "hello tokenizer"})
        assert token_count.status_code == 200
        assert token_count.json()["tokens"] > 0

        tunnel_open = client.post("/tunnel/open", json={"local_port": 8090})
        assert tunnel_open.status_code == 200
        assert tunnel_open.json()["active"] is True
        tunnel_status = client.get("/tunnel/status")
        assert tunnel_status.status_code == 200
        assert tunnel_status.json()["active"] is True
        tunnel_close = client.post("/tunnel/close")
        assert tunnel_close.status_code == 200
        assert tunnel_close.json()["active"] is False


def test_chat_stream_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.post(
            "/chat/stream",
            json={"text": "hello stream"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        body = resp.text
        assert "event: done" in body
        assert "data: 0:" in body
