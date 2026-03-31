import pytest
from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule, Condition, Action
from copaw_tool.domain.generators.pseudocode_renderer import PseudocodeRenderer


def make_ir():
    cond = Condition(lhs="长续航开关状态", cmp="==", rhs="开启")
    action = Action(lhs="长续航模式仪表提示标志", op="==", rhs="无效")
    rule = Rule(rule_id="R001", conditions=[cond], actions=[action])
    return StrategyIR(strategy_id="STRAT_001", rules=[rule])


def test_render_returns_string():
    renderer = PseudocodeRenderer()
    ir = make_ir()
    result = renderer.render(ir)
    assert isinstance(result, str)
    assert len(result) > 0


def test_render_contains_condition():
    renderer = PseudocodeRenderer()
    ir = make_ir()
    result = renderer.render(ir)
    assert "长续航开关状态" in result
    assert "==" in result
    assert "开启" in result


def test_render_contains_action():
    renderer = PseudocodeRenderer()
    ir = make_ir()
    result = renderer.render(ir)
    assert "长续航模式仪表提示标志" in result
    assert "无效" in result


def test_render_structure():
    renderer = PseudocodeRenderer()
    ir = make_ir()
    result = renderer.render(ir)
    assert "if all {" in result
    assert "then {" in result
    assert "}" in result


def test_render_multiple_rules():
    renderer = PseudocodeRenderer()
    cond1 = Condition(lhs="A", cmp="==", rhs="B")
    action1 = Action(lhs="C", op="==", rhs="D")
    rule1 = Rule(rule_id="R001", conditions=[cond1], actions=[action1])
    cond2 = Condition(lhs="X", cmp="!=", rhs="Y")
    action2 = Action(lhs="Z", op="==", rhs="W")
    rule2 = Rule(rule_id="R002", conditions=[cond2], actions=[action2])
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule1, rule2])
    result = renderer.render(ir)
    assert "A == B" in result
    assert "X != Y" in result


def test_render_empty_ir():
    renderer = PseudocodeRenderer()
    ir = StrategyIR(strategy_id="EMPTY")
    result = renderer.render(ir)
    assert result == ""


def test_render_any_op():
    renderer = PseudocodeRenderer()
    cond = Condition(lhs="A", cmp="==", rhs="B")
    action = Action(lhs="C", op="==", rhs="D")
    rule = Rule(rule_id="R001", op="any", conditions=[cond], actions=[action])
    ir = StrategyIR(strategy_id="STRAT_001", rules=[rule])
    result = renderer.render(ir)
    assert "if any {" in result
