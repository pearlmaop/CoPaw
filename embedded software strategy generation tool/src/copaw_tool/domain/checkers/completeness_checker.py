from typing import List
from copaw_tool.domain.model.strategy_ir import StrategyIR
from copaw_tool.domain.model.report_model import CompletenessReport, Issue


class CompletenessChecker:
    def check(self, ir: StrategyIR) -> CompletenessReport:
        issues: List[Issue] = []
        rules = ir.rules

        for rule in rules:
            if not rule.conditions:
                issues.append(Issue(
                    severity="high",
                    rule_id=rule.rule_id,
                    category="missing_condition",
                    message=f"规则 {rule.rule_id} 缺少条件",
                    suggestion="请补充触发条件",
                ))
            if not rule.actions:
                issues.append(Issue(
                    severity="high",
                    rule_id=rule.rule_id,
                    category="missing_action",
                    message=f"规则 {rule.rule_id} 缺少动作",
                    suggestion="请补充执行动作",
                ))

        score = max(0.0, 100.0 - len(issues) * 10)
        conclusion = "逻辑基本完整，可复核后使用" if score >= 80 else "存在明显缺陷，建议修订后再使用"
        recommendations = []
        if any(i.category == "missing_condition" for i in issues):
            recommendations.append("请为每条规则补充完整的触发条件")
        if any(i.category == "missing_action" for i in issues):
            recommendations.append("请为每条规则补充明确的执行动作")

        return CompletenessReport(
            strategy_id=ir.strategy_id,
            total_rules=len(rules),
            issue_count=len(issues),
            issues=issues,
            coverage_score=score,
            conclusion=conclusion,
            recommendations=recommendations,
        )
