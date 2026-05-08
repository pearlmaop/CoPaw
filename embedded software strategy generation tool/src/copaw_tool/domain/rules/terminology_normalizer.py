from typing import Dict
import re

from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule, Condition, Action

DEFAULT_SYNONYMS: Dict[str, str] = {
    "开": "开启", "关": "关闭", "使能": "开启", "禁止": "关闭",
    "true": "开启", "false": "关闭", "1": "开启", "0": "关闭",
    "enable": "开启", "disable": "关闭",
}


class TerminologyNormalizer:
    def __init__(self, synonyms: Dict[str, str] = None):
        self.synonyms = synonyms or DEFAULT_SYNONYMS

    def normalize(self, text: str) -> str:
        for src, tgt in self.synonyms.items():
            # Use word boundaries only for ASCII terms; for non-ASCII (e.g. Chinese), match exactly
            if src.isascii():
                pattern = rf'\b{re.escape(src)}\b'
            else:
                pattern = re.escape(src)
            text = re.sub(pattern, tgt, text, flags=re.IGNORECASE)
        return text

    def normalize_ir(self, ir: StrategyIR) -> StrategyIR:
        """Normalize all string values in a StrategyIR."""
        new_rules = []
        for rule in ir.rules:
            new_conds = [
                Condition(lhs=self.normalize(c.lhs), cmp=c.cmp, rhs=self.normalize(c.rhs))
                for c in rule.conditions
            ]
            new_actions = [
                Action(lhs=self.normalize(a.lhs), op=a.op, rhs=self.normalize(a.rhs))
                for a in rule.actions
            ]
            new_rules.append(rule.model_copy(update={"conditions": new_conds, "actions": new_actions}))
        return ir.model_copy(update={"rules": new_rules})
