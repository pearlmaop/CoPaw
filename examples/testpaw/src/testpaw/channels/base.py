from __future__ import annotations

from abc import ABC, abstractmethod


class BaseChannel(ABC):
    name: str

    @abstractmethod
    def send(self, user_id: str, message: str) -> str:
        raise NotImplementedError
