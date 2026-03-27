from copaw_tool.application.workflows.graph_state import GraphState


def report_node(state: GraphState) -> GraphState:
    """Build final_output dict with pseudocode + report."""
    final_output = {
        "pseudocode": state.get("pseudocode", ""),
        "report": state.get("completeness_report", {}),
        "strategy_ir": state.get("strategy_ir", {}),
        "errors": state.get("errors", []),
    }
    return {**state, "final_output": final_output}
