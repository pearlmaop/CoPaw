from typing import Set
from copaw_tool.domain.model.strategy_ir import StrategyIR


class CoverageChecker:
    def compute_coverage(self, ir: StrategyIR) -> float:
        """Compute a simplified coverage score based on entity coverage."""
        if not ir.rules:
            return 0.0
        entities_with_conditions: Set[str] = set()
        entities_with_actions: Set[str] = set()
        for rule in ir.rules:
            for c in rule.conditions:
                entities_with_conditions.add(c.lhs)
            for a in rule.actions:
                entities_with_actions.add(a.lhs)
        total = len(entities_with_conditions | entities_with_actions)
        covered = len(entities_with_conditions & entities_with_actions)
        if total == 0:
            return 100.0
        return round((covered / total) * 100, 1)
