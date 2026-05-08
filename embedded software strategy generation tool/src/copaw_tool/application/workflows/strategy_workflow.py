from typing import Any, Dict, List


def _run_sequential(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback sequential runner when langgraph is not available."""
    from copaw_tool.application.workflows.nodes import (
        ingest_node, extract_node, normalize_node, ir_build_node,
        pseudocode_node, check_node, report_node,
    )
    for node_fn in [ingest_node, extract_node, normalize_node, ir_build_node,
                    pseudocode_node, check_node, report_node]:
        state = node_fn(state)
    return state


def build_workflow():
    """Build a LangGraph workflow, or return a simple sequential runner as fallback."""
    try:
        from langgraph.graph import StateGraph, END
        from copaw_tool.application.workflows.graph_state import GraphState
        from copaw_tool.application.workflows.nodes import (
            ingest_node, extract_node, normalize_node, ir_build_node,
            pseudocode_node, check_node, report_node,
        )

        g = StateGraph(GraphState)
        g.add_node("ingest", ingest_node)
        g.add_node("extract", extract_node)
        g.add_node("normalize", normalize_node)
        g.add_node("ir_build", ir_build_node)
        g.add_node("pseudocode", pseudocode_node)
        g.add_node("check", check_node)
        g.add_node("report", report_node)

        g.set_entry_point("ingest")
        g.add_edge("ingest", "extract")
        g.add_edge("extract", "normalize")
        g.add_edge("normalize", "ir_build")
        g.add_edge("ir_build", "pseudocode")
        g.add_edge("pseudocode", "check")
        g.add_edge("check", "report")
        g.add_edge("report", END)
        return g.compile()
    except ImportError:
        return _run_sequential
