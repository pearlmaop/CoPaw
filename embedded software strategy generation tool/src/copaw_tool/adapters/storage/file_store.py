import shutil
import uuid
from pathlib import Path
from typing import Optional


class FileStore:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path("data/uploads")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, source_path: Path, filename: Optional[str] = None) -> Path:
        name = filename or f"{uuid.uuid4().hex}_{source_path.name}"
        dest = self.base_dir / name
        shutil.copy2(str(source_path), str(dest))
        return dest

    def save_bytes(self, content: bytes, filename: str) -> Path:
        dest = self.base_dir / filename
        dest.write_bytes(content)
        return dest
