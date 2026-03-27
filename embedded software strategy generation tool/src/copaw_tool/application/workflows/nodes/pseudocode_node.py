from copaw_tool.application.workflows.graph_state import GraphState
from copaw_tool.domain.model.strategy_ir import StrategyIR
from copaw_tool.domain.generators.pseudocode_renderer import PseudocodeRenderer


def pseudocode_node(state: GraphState) -> GraphState:
    """Call PseudocodeRenderer.render()."""
    strategy_ir_dict = state.get("strategy_ir") or {}
    ir = StrategyIR(**strategy_ir_dict)
    renderer = PseudocodeRenderer()
    pseudocode = renderer.render(ir)
    return {**state, "pseudocode": pseudocode}
