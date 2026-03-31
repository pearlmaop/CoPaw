import pytest
from copaw_tool.domain.rules.rule_parser import RuleParser
from copaw_tool.domain.model.strategy_ir import StrategyIR


SAMPLE_TEXT = """如果 长续航开关状态==开启;
那么 长续航模式仪表提示标志==无效;

如果 充电状态==充电中;
那么 充电指示灯==亮起;"""


def test_parse_from_text_returns_strategy_ir():
    parser = RuleParser()
    ir = parser.parse_from_text(SAMPLE_TEXT)
    assert isinstance(ir, StrategyIR)


def test_parse_from_text_finds_rules():
    parser = RuleParser()
    ir = parser.parse_from_text(SAMPLE_TEXT)
    assert len(ir.rules) >= 1


def test_parse_from_text_with_strategy_id():
    parser = RuleParser()
    ir = parser.parse_from_text(SAMPLE_TEXT, strategy_id="STRAT_TEST")
    assert ir.strategy_id == "STRAT_TEST"


def test_parse_from_json():
    parser = RuleParser()
    data = {
        "strategy_id": "STRAT_002",
        "rules": [
            {
                "rule_id": "R001",
                "op": "all",
                "conditions": [{"lhs": "A", "cmp": "==", "rhs": "B"}],
                "actions": [{"lhs": "C", "op": "==", "rhs": "D"}],
            }
        ],
    }
    ir = parser.parse_from_json(data)
    assert ir.strategy_id == "STRAT_002"
    assert len(ir.rules) == 1
    assert ir.rules[0].rule_id == "R001"


def test_parse_from_text_conditions_extracted():
    parser = RuleParser()
    text = "如果 长续航开关状态==开启;\n那么 长续航模式仪表提示标志==无效;"
    ir = parser.parse_from_text(text)
    assert len(ir.rules) >= 1
    rule = ir.rules[0]
    assert len(rule.conditions) >= 1
    assert rule.conditions[0].cmp == "=="


def test_parse_empty_text():
    parser = RuleParser()
    ir = parser.parse_from_text("")
    assert isinstance(ir, StrategyIR)
    assert ir.rules == []
