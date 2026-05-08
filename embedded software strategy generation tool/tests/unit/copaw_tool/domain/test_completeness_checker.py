import pytest
from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule, Condition, Action
from copaw_tool.domain.checkers.completeness_checker import CompletenessChecker


def make_valid_rule(rule_id="R001"):
    cond = Condition(lhs="A", cmp="==", rhs="B")
    action = Action(lhs="C", op="==", rhs="D")
    return Rule(rule_id=rule_id, conditions=[cond], actions=[action])


def test_check_valid_ir():
    checker = CompletenessChecker()
    rule = make_valid_rule()
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    report = checker.check(ir)
    assert report.issue_count == 0
    assert report.coverage_score == 100.0
    assert "完整" in report.conclusion


def test_check_missing_conditions():
    checker = CompletenessChecker()
    action = Action(lhs="C", op="==", rhs="D")
    rule = Rule(rule_id="R001", actions=[action])
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    report = checker.check(ir)
    assert report.issue_count > 0
    issues_cats = [i.category for i in report.issues]
    assert "missing_condition" in issues_cats


def test_check_missing_actions():
    checker = CompletenessChecker()
    cond = Condition(lhs="A", cmp="==", rhs="B")
    rule = Rule(rule_id="R001", conditions=[cond])
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    report = checker.check(ir)
    assert report.issue_count > 0
    issues_cats = [i.category for i in report.issues]
    assert "missing_action" in issues_cats


def test_check_empty_ir():
    checker = CompletenessChecker()
    ir = StrategyIR(strategy_id="STRAT_EMPTY")
    report = checker.check(ir)
    assert report.total_rules == 0
    assert report.issue_count == 0


def test_check_score_decreases_with_issues():
    checker = CompletenessChecker()
    rule = Rule(rule_id="R001")  # no conditions, no actions
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    report = checker.check(ir)
    assert report.coverage_score < 100.0


def test_check_recommendations_added():
    checker = CompletenessChecker()
    rule = Rule(rule_id="R001")  # no conditions, no actions
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    report = checker.check(ir)
    assert len(report.recommendations) > 0
