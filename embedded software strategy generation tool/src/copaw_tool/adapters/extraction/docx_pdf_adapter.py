from pathlib import Path
from typing import List, Dict, Any
from copaw_tool.adapters.extraction.base import BaseExtractor


class DocxAdapter(BaseExtractor):
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in (".doc", ".docx")

    def extract(self, file_path: Path) -> List[Dict[str, Any]]:
        try:
            import docx
            doc = docx.Document(str(file_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)
            return [{"text": text, "source": str(file_path), "type": "docx"}]
        except ImportError:
            return [{"text": "", "source": str(file_path), "type": "docx", "error": "python-docx not installed"}]
        except Exception as e:
            return [{"text": "", "source": str(file_path), "type": "docx", "error": str(e)}]


class PDFAdapter(BaseExtractor):
    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"

    def extract(self, file_path: Path) -> List[Dict[str, Any]]:
        try:
            import pdfplumber
            with pdfplumber.open(str(file_path)) as pdf:
                pages = []
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages.append({"text": text, "source": f"{file_path}#page{i+1}", "type": "pdf"})
            return pages
        except ImportError:
            try:
                import fitz  # pymupdf
                doc = fitz.open(str(file_path))
                pages = []
                for i, page in enumerate(doc):
                    text = page.get_text()
                    pages.append({"text": text, "source": f"{file_path}#page{i+1}", "type": "pdf"})
                return pages
            except ImportError:
                return [{"text": "", "source": str(file_path), "type": "pdf", "error": "No PDF library available"}]
