from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Issue(BaseModel):
    severity: Literal["high", "medium", "low"]
    rule_id: Optional[str] = None
    category: str
    message: str
    suggestion: Optional[str] = None

class CompletenessReport(BaseModel):
    strategy_id: str
    total_rules: int
    issue_count: int
    issues: List[Issue] = Field(default_factory=list)
    coverage_score: float
    conclusion: str
    recommendations: List[str] = Field(default_factory=list)
