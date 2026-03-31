from copaw_tool.application.workflows.graph_state import GraphState
from copaw_tool.domain.rules.rule_parser import RuleParser


def ir_build_node(state: GraphState) -> GraphState:
    """If LLM client available, call LLM to build IR. Otherwise use RuleParser."""
    text = state.get("normalized_text") or ""
    llm_client = state.get("llm_client")
    errors = list(state.get("errors") or [])

    strategy_ir_dict = None
    if llm_client is not None:
        try:
            strategy_ir_dict = llm_client.extract_strategy_ir(text)
        except Exception as e:
            errors.append(f"LLM IR extraction failed: {str(e)}, falling back to rule parser")

    if strategy_ir_dict is None:
        parser = RuleParser()
        ir = parser.parse_from_text(text)
        strategy_ir_dict = ir.model_dump()

    return {**state, "strategy_ir": strategy_ir_dict, "errors": errors}
