from pathlib import Path
from typing import Optional


class PromptLoader:
    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or Path(__file__).parent.parent.parent.parent.parent / "prompts"

    def load(self, category: str, name: str) -> str:
        path = self.prompts_dir / category / name
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""
