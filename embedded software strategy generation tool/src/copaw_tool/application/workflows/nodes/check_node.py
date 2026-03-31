from copaw_tool.application.workflows.graph_state import GraphState
from copaw_tool.domain.model.strategy_ir import StrategyIR
from copaw_tool.domain.checkers.completeness_checker import CompletenessChecker
from copaw_tool.domain.checkers.conflict_checker import ConflictChecker


def check_node(state: GraphState) -> GraphState:
    """Run CompletenessChecker + ConflictChecker."""
    strategy_ir_dict = state.get("strategy_ir") or {}
    ir = StrategyIR(**strategy_ir_dict)

    completeness_checker = CompletenessChecker()
    conflict_checker = ConflictChecker()

    report = completeness_checker.check(ir)
    conflict_issues = conflict_checker.check(ir)

    # Merge conflict issues into report
    all_issues = report.issues + conflict_issues
    updated_report = report.model_copy(update={
        "issues": all_issues,
        "issue_count": len(all_issues),
    })

    return {**state, "completeness_report": updated_report.model_dump()}
