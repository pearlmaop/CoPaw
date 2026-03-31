import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMSettings:
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"
    temperature: float = 0.1


@dataclass
class Settings:
    llm: LLMSettings = field(default_factory=LLMSettings)
    upload_dir: str = "data/uploads"
    output_dir: str = "data/outputs"
    prompts_dir: str = "prompts"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm=LLMSettings(
                api_key=os.getenv("OPENAI_API_KEY", ""),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            ),
            upload_dir=os.getenv("UPLOAD_DIR", "data/uploads"),
            output_dir=os.getenv("OUTPUT_DIR", "data/outputs"),
        )
