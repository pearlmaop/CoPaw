import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI-compatible API client."""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        return self._client

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> str:
        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content

    def extract_from_image(self, image_data: str, mime: str = "jpeg") -> str:
        client = self._get_client()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "请提取图片中所有策略相关文字，保持原有结构，输出纯文本。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{image_data}"}},
                ],
            }],
            temperature=0.0,
        )
        return resp.choices[0].message.content

    def extract_strategy_ir(self, text: str, system_prompt: Optional[str] = None, user_prompt_template: Optional[str] = None) -> dict:
        """Extract strategy IR as JSON from text."""
        sys_prompt = system_prompt or """你是一个嵌入式软件策略分析专家。请从输入的策略文本中提取结构化的策略IR（中间表示）。
输出严格的JSON格式，包含以下字段：
{
  "strategy_id": "STRAT_001",
  "rules": [
    {
      "rule_id": "R001",
      "op": "all",
      "conditions": [{"lhs": "...", "cmp": "==", "rhs": "..."}],
      "actions": [{"lhs": "...", "op": "==", "rhs": "..."}],
      "description": "..."
    }
  ]
}
只输出JSON，不要其他解释。"""
        user_prompt = (user_prompt_template or "策略文本：\n{text}").format(text=text)
        response = self.chat(sys_prompt, user_prompt)
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return json.loads(response)
