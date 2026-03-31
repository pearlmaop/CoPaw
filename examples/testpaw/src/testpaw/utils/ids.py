from __future__ import annotations

import secrets


def short_id(length: int = 6) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(alphabet[secrets.randbelow(len(alphabet))] for _ in range(length))
