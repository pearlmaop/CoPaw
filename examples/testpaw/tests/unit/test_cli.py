from click.testing import CliRunner

from testpaw.cli.main import cli


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "app" in result.output
    assert "testpaw" in result.output.lower()


def test_cli_app_invokes_uvicorn(monkeypatch) -> None:
    called = {}

    def fake_run(target: str, host: str, port: int, log_level: str) -> None:
        called["target"] = target
        called["host"] = host
        called["port"] = port
        called["log_level"] = log_level

    monkeypatch.setattr("testpaw.cli.main.uvicorn.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["app", "--host", "0.0.0.0", "--port", "9000", "--log-level", "debug"],
    )

    assert result.exit_code == 0
    assert called == {
        "target": "testpaw.api.app:app",
        "host": "0.0.0.0",
        "port": 9000,
        "log_level": "debug",
    }


def test_cli_parity_commands_callable() -> None:
    runner = CliRunner()
    cases = [
        ["channels", "list"],
        ["daemon", "status"],
        ["chats", "list"],
        ["cron", "list"],
        ["env", "dump", "--keys", "A,B"],
        ["models", "list"],
        ["skills", "scan"],
        ["auth", "login", "--username", "alice"],
        ["agents", "list"],
        ["clean"],
        ["init"],
        ["uninstall"],
        ["desktop"],
        ["update"],
        ["shutdown"],
    ]
    for argv in cases:
        result = runner.invoke(cli, argv)
        assert result.exit_code == 0, (argv, result.output)
