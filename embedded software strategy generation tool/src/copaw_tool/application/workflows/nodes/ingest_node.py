from pathlib import Path
from typing import Any, Dict
from copaw_tool.application.workflows.graph_state import GraphState


def ingest_node(state: GraphState) -> GraphState:
    """Validate file_paths, ensure files exist."""
    errors = list(state.get("errors") or [])
    file_paths = state.get("file_paths") or []
    valid_paths = []
    for fp in file_paths:
        path = Path(fp)
        if path.exists():
            valid_paths.append(fp)
        else:
            errors.append(f"File not found: {fp}")
    return {**state, "file_paths": valid_paths, "errors": errors}
