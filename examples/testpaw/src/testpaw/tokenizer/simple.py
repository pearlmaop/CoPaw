from __future__ import annotations


def estimate_tokens(text: str) -> int:
    # Simple heuristic: split by whitespace + punctuation fallback.
    stripped = text.strip()
    if not stripped:
        return 0
    words = [w for w in stripped.replace("\n", " ").split(" ") if w]
    return max(len(words), int(len(stripped) / 4))
