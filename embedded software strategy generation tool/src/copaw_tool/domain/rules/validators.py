from typing import List
from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule


def validate_rule(rule: Rule) -> List[str]:
    """Return list of validation error messages for a rule."""
    errors = []
    if not rule.rule_id:
        errors.append("rule_id is required")
    if not rule.conditions:
        errors.append(f"Rule {rule.rule_id} has no conditions")
    if not rule.actions:
        errors.append(f"Rule {rule.rule_id} has no actions")
    return errors


def validate_ir(ir: StrategyIR) -> List[str]:
    """Return list of validation error messages for a StrategyIR."""
    errors = []
    if not ir.strategy_id:
        errors.append("strategy_id is required")
    for rule in ir.rules:
        errors.extend(validate_rule(rule))
    return errors
