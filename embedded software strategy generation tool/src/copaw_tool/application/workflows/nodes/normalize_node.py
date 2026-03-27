from copaw_tool.application.workflows.graph_state import GraphState
from copaw_tool.domain.rules.terminology_normalizer import TerminologyNormalizer


def normalize_node(state: GraphState) -> GraphState:
    """Run TerminologyNormalizer on extracted text."""
    normalizer = TerminologyNormalizer()
    segments = state.get("extracted_segments") or []
    combined = "\n".join(seg.get("text", "") for seg in segments if seg.get("text"))
    normalized = normalizer.normalize(combined)
    return {**state, "normalized_text": normalized}
