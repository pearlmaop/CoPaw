import pytest
from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule, Condition, Action
from copaw_tool.domain.checkers.conflict_checker import ConflictChecker


def test_no_conflicts():
    checker = ConflictChecker()
    action1 = Action(lhs="A", op="==", rhs="1")
    action2 = Action(lhs="B", op="==", rhs="2")
    rule = Rule(rule_id="R001", actions=[action1, action2])
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    issues = checker.check(ir)
    assert issues == []


def test_conflict_detected():
    checker = ConflictChecker()
    action1 = Action(lhs="A", op="==", rhs="开启")
    action2 = Action(lhs="A", op="==", rhs="关闭")
    rule = Rule(rule_id="R001", actions=[action1, action2])
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    issues = checker.check(ir)
    assert len(issues) >= 1
    assert issues[0].category == "conflict"
    assert issues[0].severity == "medium"


def test_no_conflict_same_value():
    checker = ConflictChecker()
    action1 = Action(lhs="A", op="==", rhs="开启")
    action2 = Action(lhs="A", op="==", rhs="开启")
    rule = Rule(rule_id="R001", actions=[action1, action2])
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    issues = checker.check(ir)
    assert issues == []


def test_empty_ir():
    checker = ConflictChecker()
    ir = StrategyIR(strategy_id="STRAT_001")
    issues = checker.check(ir)
    assert issues == []
