import pytest
from copaw_tool.adapters.exporters.markdown_exporter import MarkdownExporter
from copaw_tool.domain.model.strategy_ir import StrategyIR, Rule, Condition, Action
from copaw_tool.domain.model.report_model import CompletenessReport, Issue


def make_ir():
    cond = Condition(lhs="A", cmp="==", rhs="B")
    action = Action(lhs="C", op="==", rhs="D")
    rule = Rule(rule_id="R001", conditions=[cond], actions=[action])
    return StrategyIR(strategy_id="STRAT_001", rules=[rule])


def make_report(with_issues=False):
    issues = []
    if with_issues:
        issues = [Issue(severity="high", rule_id="R001", category="missing_action",
                        message="规则 R001 缺少动作", suggestion="请补充执行动作")]
    return CompletenessReport(
        strategy_id="STRAT_001",
        total_rules=1,
        issue_count=len(issues),
        issues=issues,
        coverage_score=90.0,
        conclusion="逻辑基本完整",
        recommendations=["建议补充条件"],
    )


def test_export_pseudocode_contains_text():
    exporter = MarkdownExporter()
    pseudocode = "if all {\n    A == B;\n}\nthen {\n    C == D;\n}"
    result = exporter.export_pseudocode(pseudocode)
    assert "标准化伪代码" in result
    assert "if all" in result
    assert "```text" in result


def test_export_pseudocode_with_ir():
    exporter = MarkdownExporter()
    ir = make_ir()
    pseudocode = "if all {\n    A == B;\n}"
    result = exporter.export_pseudocode(pseudocode, ir=ir)
    assert "STRAT_001" in result
    assert "1" in result


def test_export_report_contains_fields():
    exporter = MarkdownExporter()
    report = make_report()
    result = exporter.export_report(report)
    assert "逻辑完整性报告" in result
    assert "STRAT_001" in result
    assert "90.0%" in result


def test_export_report_with_issues():
    exporter = MarkdownExporter()
    report = make_report(with_issues=True)
    result = exporter.export_report(report)
    assert "🔴" in result
    assert "规则 R001 缺少动作" in result


def test_export_report_conclusion():
    exporter = MarkdownExporter()
    report = make_report()
    result = exporter.export_report(report)
    assert "逻辑基本完整" in result
    assert "建议补充条件" in result
