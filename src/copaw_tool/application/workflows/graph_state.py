from typing import TypedDict, List, Dict, Any, Optional


class GraphState(TypedDict, total=False):
    task_id: str
    file_paths: List[str]
    extracted_segments: List[Dict[str, Any]]
    normalized_text: str
    strategy_ir: Dict[str, Any]
    pseudocode: str
    completeness_report: Dict[str, Any]
    final_output: Dict[str, Any]
    errors: List[str]
    llm_client: Any
