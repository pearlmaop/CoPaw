from click.testing import CliRunner
from fastapi.testclient import TestClient

from testpaw.api.app import create_app
from testpaw.cli.main import cli


def test_cli_command_parity_contract() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    out = result.output

    required = [
        "app",
        "channels",
        "channel",
        "daemon",
        "chats",
        "chat",
        "clean",
        "cron",
        "env",
        "init",
        "models",
        "skills",
        "uninstall",
        "desktop",
        "update",
        "shutdown",
        "auth",
        "agents",
        "agent",
    ]
    for cmd in required:
        assert cmd in out


def test_api_route_parity_contract() -> None:
    app = create_app()
    with TestClient(app) as client:
        checks = [
            ("GET", "/health", None),
            ("POST", "/chat", {"text": "hello"}),
            ("POST", "/chat/stream", {"text": "hello"}),
            ("GET", "/agents", None),
            ("POST", "/auth/login", {"username": "u"}),
            ("POST", "/auth/logout", {}),
            ("GET", "/workspace/info", None),
            ("GET", "/messages", None),
            ("GET", "/files", None),
            ("GET", "/console/push-messages", None),
            ("POST", "/daemon/restart", {}),
            ("GET", "/chats", None),
            ("GET", "/config", None),
            ("POST", "/config/channels", ["console"]),
            ("POST", "/cron/jobs", {"job_id": "j", "every_seconds": 5, "message": "m"}),
            ("GET", "/cron/jobs", None),
            ("POST", "/mcp/register", {"name": "mcp", "config": {}}),
            ("GET", "/mcp/clients", None),
            ("GET", "/memory/default-session", None),
            ("POST", "/skills/scan", {"text": "safe"}),
            ("POST", "/approvals/request", {"request_id": "r", "payload": {}}),
            ("GET", "/approvals/pending", None),
            ("POST", "/envs/set", {"key": "A", "value": "1"}),
            ("GET", "/envs/get/A", None),
            ("POST", "/local-models", {"model_id": "m1", "backend": "b"}),
            ("GET", "/local-models", None),
            ("GET", "/token-usage", None),
            ("POST", "/tokenizer/count", {"text": "hello"}),
            ("POST", "/tunnel/open", {"local_port": 8080}),
            ("GET", "/tunnel/status", None),
            ("GET", "/providers", None),
            ("POST", "/providers/activate", {"provider_id": "mock"}),
        ]

        for method, path, payload in checks:
            if method == "GET":
                resp = client.get(path)
            else:
                resp = client.post(path, json=payload)
            assert resp.status_code == 200, (method, path, resp.text)
