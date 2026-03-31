from pathlib import Path


def test_top_level_module_families_exist() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "testpaw"
    expected = {
        "agents",
        "api",
        "app",
        "channels",
        "cli",
        "config",
        "crons",
        "envs",
        "local_models",
        "mcp",
        "memory",
        "providers",
        "runtime",
        "security",
        "token_usage",
        "tokenizer",
        "tunnel",
        "utils",
        "approvals",
    }
    present = {p.name for p in root.iterdir() if p.is_dir()}
    assert expected.issubset(present)
