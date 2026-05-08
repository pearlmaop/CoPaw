from pathlib import Path
from typing import List, Dict, Any
from copaw_tool.application.workflows.graph_state import GraphState


def extract_node(state: GraphState) -> GraphState:
    """Route files to appropriate extractors."""
    from copaw_tool.adapters.extraction.docx_pdf_adapter import DocxAdapter, PDFAdapter
    from copaw_tool.adapters.extraction.vlm_adapter import VLMAdapter
    from copaw_tool.adapters.extraction.mineru_adapter import MinerUAdapter

    llm_client = state.get("llm_client")
    extractors = [
        VLMAdapter(llm_client=llm_client),
        DocxAdapter(),
        MinerUAdapter(),
    ]

    segments: List[Dict[str, Any]] = []
    errors = list(state.get("errors") or [])

    for fp in state.get("file_paths") or []:
        path = Path(fp)
        matched = False
        for extractor in extractors:
            if extractor.supports(path):
                try:
                    result = extractor.extract(path)
                    segments.extend(result)
                except Exception as e:
                    errors.append(f"Extraction error for {fp}: {e}")
                matched = True
                break
        if not matched:
            errors.append(f"No extractor found for: {fp}")

    return {**state, "extracted_segments": segments, "errors": errors}
