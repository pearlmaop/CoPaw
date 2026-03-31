from __future__ import annotations

import json
import time
from dataclasses import dataclass
from urllib import request, error


@dataclass
class OpenAICompatibleProvider:
    provider_id: str = "openai-compatible"
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    timeout_seconds: int = 30
    max_retries: int = 2
    retry_backoff_seconds: float = 0.2

    def model_name(self) -> str:
        return f"{self.provider_id}/{self.model}"

    def configure(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        if model is not None and model.strip():
            self.model = model.strip()
        if base_url is not None and base_url.strip():
            self.base_url = base_url.rstrip("/")
        if api_key is not None:
            self.api_key = api_key.strip()

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "configured": bool(self.api_key),
        }

    def generate(self, prompt: str, urlopen_fn=None) -> str:
        # Keep test/dev environment deterministic and offline-friendly.
        if not self.api_key:
            return (
                "[openai-compatible/error][not-configured] "
                "missing API key, fallback reply: "
                f"{prompt}"
            )

        if urlopen_fn is None:
            urlopen_fn = request.urlopen

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url=url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.api_key}")

        last_error = ""
        attempts = max(self.max_retries + 1, 1)
        for i in range(attempts):
            try:
                with urlopen_fn(req, timeout=self.timeout_seconds) as resp:
                    body = resp.read().decode("utf-8")
                    parsed = json.loads(body)
                choices = parsed.get("choices", [])
                if not choices:
                    return "[openai-compatible/error][invalid-response] no choices"
                message = choices[0].get("message", {})
                content = str(message.get("content", "")).strip()
                if not content:
                    return "[openai-compatible/error][invalid-response] empty content"
                return content
            except error.HTTPError as exc:
                return f"[openai-compatible/error][http:{exc.code}] {exc.reason}"
            except error.URLError as exc:
                last_error = str(exc)
                if i < attempts - 1:
                    time.sleep(self.retry_backoff_seconds * (2**i))
                    continue
            except Exception as exc:  # pragma: no cover
                return f"[openai-compatible/error][unexpected] {exc}"

        return f"[openai-compatible/error][network] {last_error}"
