from typing import Optional
from copaw_tool.domain.model.strategy_ir import StrategyIR
from copaw_tool.domain.model.report_model import CompletenessReport


class MarkdownExporter:
    def export_pseudocode(self, pseudocode: str, ir: Optional[StrategyIR] = None) -> str:
        lines = ["# 标准化伪代码\n"]
        if ir:
            lines.append(f"**策略ID**: {ir.strategy_id}  ")
            lines.append(f"**规则数量**: {len(ir.rules)}\n")
        lines.append("```text")
        lines.append(pseudocode)
        lines.append("```")
        return "\n".join(lines)

    def export_report(self, report: CompletenessReport) -> str:
        lines = [
            "# 逻辑完整性报告\n",
            f"**策略ID**: {report.strategy_id}  ",
            f"**规则数量**: {report.total_rules}  ",
            f"**问题数量**: {report.issue_count}  ",
            f"**覆盖度评分**: {report.coverage_score:.1f}%\n",
        ]
        if report.issues:
            lines.append("## 检测到的问题\n")
            for issue in report.issues:
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.severity, "⚪")
                lines.append(f"- {severity_emoji} **[{issue.severity.upper()}]** {issue.message}")
                if issue.suggestion:
                    lines.append(f"  - 建议：{issue.suggestion}")
        lines.append(f"\n## 结论\n\n{report.conclusion}")
        if report.recommendations:
            lines.append("\n## 建议\n")
            for rec in report.recommendations:
                lines.append(f"- {rec}")
        return "\n".join(lines)
