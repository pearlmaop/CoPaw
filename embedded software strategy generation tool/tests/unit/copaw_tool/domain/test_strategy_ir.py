import pytest
from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule, Condition, Action


def test_condition_creation():
    cond = Condition(lhs="长续航开关状态", cmp="==", rhs="开启")
    assert cond.lhs == "长续航开关状态"
    assert cond.cmp == "=="
    assert cond.rhs == "开启"


def test_action_creation():
    action = Action(lhs="长续航模式仪表提示标志", op="==", rhs="无效")
    assert action.lhs == "长续航模式仪表提示标志"
    assert action.op == "=="
    assert action.rhs == "无效"


def test_rule_creation():
    cond = Condition(lhs="A", cmp="==", rhs="B")
    action = Action(lhs="C", op="==", rhs="D")
    rule = Rule(rule_id="R001", conditions=[cond], actions=[action])
    assert rule.rule_id == "R001"
    assert len(rule.conditions) == 1
    assert len(rule.actions) == 1
    assert rule.op == "all"


def test_strategy_ir_creation():
    ir = StrategyIR(strategy_id="STRAT_001")
    assert ir.strategy_id == "STRAT_001"
    assert ir.rules == []
    assert ir.entities == []


def test_strategy_ir_serialization():
    cond = Condition(lhs="X", cmp=">", rhs="10")
    action = Action(lhs="Y", op=":=", rhs="1")
    rule = Rule(rule_id="R001", conditions=[cond], actions=[action])
    ir = StrategyIR(strategy_id="STRAT_TEST", rules=[rule])
    data = ir.model_dump()
    assert data["strategy_id"] == "STRAT_TEST"
    assert len(data["rules"]) == 1
    # Deserialize back
    ir2 = StrategyIR(**data)
    assert ir2.strategy_id == ir.strategy_id
    assert ir2.rules[0].rule_id == "R001"


def test_rule_default_priority():
    rule = Rule(rule_id="R001")
    assert rule.priority == 0


def test_strategy_ir_with_metadata():
    ir = StrategyIR(strategy_id="STRAT_001", metadata={"version": "1.0"})
    assert ir.metadata["version"] == "1.0"
