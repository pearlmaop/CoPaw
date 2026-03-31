from testpaw.providers.manager import ProviderManager
from testpaw.runtime.graph import AgentGraphBuilder
from testpaw.runtime.tools import build_default_tool_registry
from testpaw.security.tool_guard import ToolGuardEngine


def _build_graph():
    manager = ProviderManager()
    builder = AgentGraphBuilder(
        tool_guard=ToolGuardEngine(),
        tools=build_default_tool_registry(),
        model_reply=manager.generate,
    )
    return builder.compile()


def test_graph_model_path_trace() -> None:
    graph = _build_graph()
    out = graph.invoke({"input_text": "hello world", "trace": []})
    assert out["trace"] == ["normalize", "guard", "plan", "model_reply"]
    assert out["response"].endswith("hello world")


def test_graph_tool_path_trace() -> None:
    graph = _build_graph()
    out = graph.invoke({"input_text": "/calc 9/3", "trace": []})
    assert out["trace"] == ["normalize", "guard", "plan", "run_tool"]
    assert out["response"] == "Result: 3.0"


def test_graph_blocked_path_trace() -> None:
    graph = _build_graph()
    out = graph.invoke({"input_text": "drop table users", "trace": []})
    assert out["trace"] == ["normalize", "guard", "blocked_reply"]
    assert "blocked" in out["response"].lower()
