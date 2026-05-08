from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Condition(BaseModel):
    lhs: str
    cmp: Literal["==", "!=", ">", "<", ">=", "<="]
    rhs: str

class Action(BaseModel):
    lhs: str
    op: Literal["==", ":=", "set"] = "=="
    rhs: str

class Rule(BaseModel):
    rule_id: str
    op: Literal["all", "any"] = "all"
    conditions: List[Condition] = Field(default_factory=list)
    actions: List[Action] = Field(default_factory=list)
    priority: int = 0
    description: Optional[str] = None

class StrategyIR(BaseModel):
    strategy_id: str
    source_file: Optional[str] = None
    entities: List[dict] = Field(default_factory=list)
    rules: List[Rule] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
