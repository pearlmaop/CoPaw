import json
import re
from typing import List, Dict, Any, Optional

from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule, Condition, Action


class RuleParser:
    """Parse strategy text/JSON into StrategyIR."""

    def parse_from_json(self, data: Dict[str, Any]) -> StrategyIR:
        return StrategyIR(**data)

    def parse_from_text(self, text: str, strategy_id: str = "STRAT_001") -> StrategyIR:
        """Simple regex-based parser for structured text."""
        rules = []
        blocks = self._split_rule_blocks(text)
        for i, block in enumerate(blocks):
            rule = self._parse_block(block, f"R{i+1:03d}")
            if rule:
                rules.append(rule)
        return StrategyIR(strategy_id=strategy_id, rules=rules)

    def _split_rule_blocks(self, text: str) -> List[str]:
        pattern = r'(?i)(?:if\s+(?:all|any)|如果)'
        parts = re.split(pattern, text)
        return [p.strip() for p in parts if p.strip()]

    def _parse_block(self, block: str, rule_id: str) -> Optional[Rule]:
        split_pattern = r'(?i)(?:then|那么|则)'
        parts = re.split(split_pattern, block)
        if len(parts) < 1:
            return None
        cond_text = parts[0]
        action_text = parts[1] if len(parts) > 1 else ""
        conditions = self._parse_assignments(cond_text)
        actions = [Action(lhs=a.lhs, op=a.cmp, rhs=a.rhs) for a in self._parse_assignments(action_text)]
        return Rule(rule_id=rule_id, conditions=conditions, actions=actions)

    def _parse_assignments(self, text: str) -> List[Condition]:
        items = []
        pattern = r'([^=!<>;\n]+?)\s*(==|!=|>=|<=|>|<)\s*([^=!<>;\n]+?)(?:;|$)'
        for m in re.finditer(pattern, text, re.MULTILINE):
            lhs, cmp, rhs = m.group(1).strip(), m.group(2), m.group(3).strip()
            if lhs and rhs:
                items.append(Condition(lhs=lhs, cmp=cmp, rhs=rhs))
        return items
