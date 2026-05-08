from typing import List
from copaw_tool.domain.model.strategy_ir import StrategyIR
from copaw_tool.domain.model.report_model import Issue


class ConflictChecker:
    def check(self, ir: StrategyIR) -> List[Issue]:
        issues: List[Issue] = []
        for rule in ir.rules:
            seen = {}
            for action in rule.actions:
                if action.lhs in seen and seen[action.lhs] != action.rhs:
                    issues.append(Issue(
                        severity="medium",
                        rule_id=rule.rule_id,
                        category="conflict",
                        message=f"规则 {rule.rule_id} 中 {action.lhs} 被赋予冲突值: {seen[action.lhs]} vs {action.rhs}",
                        suggestion="请检查并消解动作冲突",
                    ))
                seen[action.lhs] = action.rhs
        return issues
