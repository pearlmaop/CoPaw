from __future__ import annotations


class TokenUsageTracker:
    def __init__(self) -> None:
        self._total_input = 0
        self._total_output = 0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self._total_input += max(input_tokens, 0)
        self._total_output += max(output_tokens, 0)

    def summary(self) -> dict:
        return {
            "input_tokens": self._total_input,
            "output_tokens": self._total_output,
            "total_tokens": self._total_input + self._total_output,
        }

    def reset(self) -> None:
        self._total_input = 0
        self._total_output = 0
