from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule


class PseudocodeRenderer:
    """Render StrategyIR into standardized pseudocode."""

    def render(self, ir: StrategyIR) -> str:
        blocks = []
        for rule in ir.rules:
            block = self._render_rule(rule)
            blocks.append(block)
        return "\n\n".join(blocks)

    def _render_rule(self, rule: Rule) -> str:
        lines = []
        op = rule.op
        lines.append(f"if {op} {{")
        for cond in rule.conditions:
            lines.append(f"    {cond.lhs} {cond.cmp} {cond.rhs};")
        lines.append("}")
        lines.append("then {")
        for action in rule.actions:
            lines.append(f"    {action.lhs} {action.op} {action.rhs};")
        lines.append("}")
        return "\n".join(lines)
