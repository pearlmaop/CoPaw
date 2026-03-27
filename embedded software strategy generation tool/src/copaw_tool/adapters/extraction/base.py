from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract text segments from file. Returns list of {'text': str, 'source': str}."""
        pass

    def supports(self, file_path: Path) -> bool:
        return False
