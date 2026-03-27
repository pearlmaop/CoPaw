import base64
from pathlib import Path
from typing import List, Dict, Any

from copaw_tool.adapters.extraction.base import BaseExtractor


class VLMAdapter(BaseExtractor):
    """Vision Language Model adapter for image extraction."""

    def __init__(self, llm_client=None):
        self._client = llm_client

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp")

    def extract(self, file_path: Path) -> List[Dict[str, Any]]:
        if self._client is None:
            return [{"text": "", "source": str(file_path), "type": "image", "error": "LLM client not configured"}]
        try:
            with open(file_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            suffix = file_path.suffix.lower().lstrip(".")
            mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix
            result = self._client.extract_from_image(image_data, mime)
            return [{"text": result, "source": str(file_path), "type": "image"}]
        except Exception as e:
            return [{"text": "", "source": str(file_path), "type": "image", "error": str(e)}]
