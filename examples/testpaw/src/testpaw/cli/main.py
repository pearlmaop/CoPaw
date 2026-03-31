from __future__ import annotations

import json

import click
import uvicorn


class LazyGroup(click.Group):
    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        base = super().list_commands(ctx)
        return sorted(set(base) | set(self.lazy_subcommands.keys()))

    def get_command(self, ctx, cmd_name):
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        if cmd_name in self.lazy_subcommands:
            module_path, attr_name = self.lazy_subcommands[cmd_name]
            module = __import__(module_path, fromlist=[attr_name])
            cmd = getattr(module, attr_name)
            self.add_command(cmd, cmd_name)
            return cmd
        return None


@click.group(
    cls=LazyGroup,
    lazy_subcommands={
        "app": ("testpaw.cli.main", "app_cmd"),
        "channels": ("testpaw.cli.main", "channels_group"),
        "channel": ("testpaw.cli.main", "channels_group"),
        "daemon": ("testpaw.cli.main", "daemon_group"),
        "chats": ("testpaw.cli.main", "chats_group"),
        "chat": ("testpaw.cli.main", "chats_group"),
        "clean": ("testpaw.cli.main", "clean_cmd"),
        "cron": ("testpaw.cli.main", "cron_group"),
        "env": ("testpaw.cli.main", "env_group"),
        "init": ("testpaw.cli.main", "init_cmd"),
        "models": ("testpaw.cli.main", "models_group"),
        "skills": ("testpaw.cli.main", "skills_group"),
        "uninstall": ("testpaw.cli.main", "uninstall_cmd"),
        "desktop": ("testpaw.cli.main", "desktop_cmd"),
        "update": ("testpaw.cli.main", "update_cmd"),
        "shutdown": ("testpaw.cli.main", "shutdown_cmd"),
        "auth": ("testpaw.cli.main", "auth_group"),
        "agents": ("testpaw.cli.main", "agents_group"),
        "agent": ("testpaw.cli.main", "agents_group"),
    },
)
def cli() -> None:
    """testpaw CLI."""


@click.command("app")
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8090, type=int)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug"]),
)
def app_cmd(host: str, port: int, log_level: str) -> None:
    """Run HTTP API server."""
    uvicorn.run(
        "testpaw.api.app:app",
        host=host,
        port=port,
        log_level=log_level,
    )


@click.group("channels")
def channels_group() -> None:
    """Manage channel configuration."""


@channels_group.command("list")
def channels_list_cmd() -> None:
    click.echo("console")


@click.group("daemon")
def daemon_group() -> None:
    """Daemon operations."""


@daemon_group.command("status")
def daemon_status_cmd() -> None:
    click.echo("daemon: running")


@click.group("chats")
def chats_group() -> None:
    """Chat operations."""


@chats_group.command("list")
def chats_list_cmd() -> None:
    click.echo("[]")


@click.command("clean")
def clean_cmd() -> None:
    click.echo("cleaned")


@click.group("cron")
def cron_group() -> None:
    """Cron operations."""


@cron_group.command("list")
def cron_list_cmd() -> None:
    click.echo("[]")


@click.group("env")
def env_group() -> None:
    """Environment operations."""


@env_group.command("dump")
@click.option("--keys", default="", help="Comma-separated env keys")
def env_dump_cmd(keys: str) -> None:
    items = [k.strip() for k in keys.split(",") if k.strip()]
    payload = {k: "" for k in items}
    click.echo(json.dumps(payload, ensure_ascii=False))


@click.command("init")
def init_cmd() -> None:
    click.echo("initialized")


@click.group("models")
def models_group() -> None:
    """Model provider operations."""


@models_group.command("list")
def models_list_cmd() -> None:
    click.echo("mock\nopenai-compatible")


@click.group("skills")
def skills_group() -> None:
    """Skills operations."""


@skills_group.command("scan")
def skills_scan_cmd() -> None:
    click.echo("safe")


@click.command("uninstall")
def uninstall_cmd() -> None:
    click.echo("uninstall simulated")


@click.command("desktop")
def desktop_cmd() -> None:
    click.echo("desktop mode not enabled")


@click.command("update")
def update_cmd() -> None:
    click.echo("already latest")


@click.command("shutdown")
def shutdown_cmd() -> None:
    click.echo("shutdown signal sent")


@click.group("auth")
def auth_group() -> None:
    """Authentication operations."""


@auth_group.command("login")
@click.option("--username", required=True)
def auth_login_cmd(username: str) -> None:
    click.echo(f"logged in: {username}")


@click.group("agents")
def agents_group() -> None:
    """Agent operations."""


@agents_group.command("list")
def agents_list_cmd() -> None:
    click.echo("default")


if __name__ == "__main__":
    cli()
