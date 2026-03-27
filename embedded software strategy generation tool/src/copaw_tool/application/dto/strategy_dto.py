from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class StrategyRequest(BaseModel):
    file_paths: List[str] = Field(default_factory=list)
    strategy_id: Optional[str] = "STRAT_001"
    use_llm: bool = False


class StrategyResponse(BaseModel):
    strategy_id: str
    pseudocode: str
    report: Dict[str, Any]
    strategy_ir: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)
