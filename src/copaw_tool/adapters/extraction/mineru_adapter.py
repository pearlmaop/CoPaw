import logging
from pathlib import Path
from typing import List, Dict, Any

from copaw_tool.adapters.extraction.base import BaseExtractor

logger = logging.getLogger(__name__)


class MinerUAdapter(BaseExtractor):
    """MinerU-based PDF extraction. Falls back to PDFAdapter if MinerU unavailable."""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"

    def extract(self, file_path: Path) -> List[Dict[str, Any]]:
        try:
            # MinerU real integration not yet configured; fall back immediately
            raise ImportError("MinerU integration not configured; using fallback")
        except ImportError:
            logger.warning("MinerU not available, falling back to PDFAdapter")
            from copaw_tool.adapters.extraction.docx_pdf_adapter import PDFAdapter
            return PDFAdapter().extract(file_path)
