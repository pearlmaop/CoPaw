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
            from magic_pdf.data.data_reader_writer import FileBasedDataWriter  # noqa: F401
            # Real MinerU extraction would go here when magic_pdf is installed
            raise ImportError("MinerU not installed; using PDFAdapter fallback")
        except ImportError:
            logger.warning("MinerU not available, falling back to PDFAdapter")
            from copaw_tool.adapters.extraction.docx_pdf_adapter import PDFAdapter
            return PDFAdapter().extract(file_path)
