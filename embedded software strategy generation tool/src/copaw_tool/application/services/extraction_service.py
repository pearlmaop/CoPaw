from pathlib import Path
from typing import List, Dict, Any, Optional

from copaw_tool.adapters.extraction.docx_pdf_adapter import DocxAdapter, PDFAdapter
from copaw_tool.adapters.extraction.vlm_adapter import VLMAdapter
from copaw_tool.adapters.extraction.mineru_adapter import MinerUAdapter


class ExtractionService:
    def __init__(self, llm_client=None):
        self._extractors = [
            VLMAdapter(llm_client=llm_client),
            DocxAdapter(),
            MinerUAdapter(),
        ]

    def extract(self, file_path: Path) -> List[Dict[str, Any]]:
        for extractor in self._extractors:
            if extractor.supports(file_path):
                return extractor.extract(file_path)
        raise ValueError(f"No extractor available for: {file_path}")

    def extract_all(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        segments = []
        for fp in file_paths:
            segments.extend(self.extract(fp))
        return segments
