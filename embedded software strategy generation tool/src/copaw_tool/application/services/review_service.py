from typing import List
from copaw_tool.domain.model.strategy_ir import StrategyIR
from copaw_tool.domain.model.report_model import CompletenessReport, Issue
from copaw_tool.domain.checkers.completeness_checker import CompletenessChecker
from copaw_tool.domain.checkers.conflict_checker import ConflictChecker
from copaw_tool.domain.checkers.coverage_checker import CoverageChecker


class ReviewService:
    def __init__(self):
        self._completeness_checker = CompletenessChecker()
        self._conflict_checker = ConflictChecker()
        self._coverage_checker = CoverageChecker()

    def review(self, ir: StrategyIR) -> CompletenessReport:
        report = self._completeness_checker.check(ir)
        conflict_issues = self._conflict_checker.check(ir)
        coverage_score = self._coverage_checker.compute_coverage(ir)

        all_issues = report.issues + conflict_issues
        return report.model_copy(update={
            "issues": all_issues,
            "issue_count": len(all_issues),
            "coverage_score": coverage_score,
        })
