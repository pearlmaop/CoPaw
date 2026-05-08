import pytest
from copaw_tool.domain.rules.terminology_normalizer import TerminologyNormalizer
from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule, Condition, Action


def test_normalize_basic_synonyms():
    normalizer = TerminologyNormalizer()
    # enable -> 开启
    result = normalizer.normalize("enable")
    assert result == "开启"


def test_normalize_disable():
    normalizer = TerminologyNormalizer()
    result = normalizer.normalize("disable")
    assert result == "关闭"


def test_normalize_ir():
    normalizer = TerminologyNormalizer()
    cond = Condition(lhs="状态", cmp="==", rhs="enable")
    action = Action(lhs="灯", op="==", rhs="disable")
    rule = Rule(rule_id="R001", conditions=[cond], actions=[action])
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    normalized = normalizer.normalize_ir(ir)
    assert normalized.rules[0].conditions[0].rhs == "开启"
    assert normalized.rules[0].actions[0].rhs == "关闭"


def test_custom_synonyms():
    normalizer = TerminologyNormalizer(synonyms={"foo": "bar"})
    result = normalizer.normalize("foo")
    assert result == "bar"


def test_no_change_when_no_match():
    normalizer = TerminologyNormalizer()
    result = normalizer.normalize("未知状态")
    assert result == "未知状态"
