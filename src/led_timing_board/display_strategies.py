import os
from abc import ABC, abstractmethod
from multiprocessing.connection import wait
from time import monotonic
from typing import Optional


class DisplayStrategy(ABC):
    @abstractmethod
    def update(self) -> Optional[str]:
        ...


class Initial(DisplayStrategy):

    parts = (os.environ.get("LED_TIMING_BOARD_INITIAL", "#???"), "RDY")

    def __init__(self) -> None:
        self._index = -1
        self._index_started = 0.0

    def update(self) -> Optional[str]:
        now = monotonic()
        if now - self._index_started > 1.0:
            self._index = (self._index + 1) % len(self.parts)
            self._index_started = now
            return self.parts[self._index]
        return None


class Alternating(DisplayStrategy):
    pass


class Blinking(DisplayStrategy):
    def __init__(self, text: str) -> None:
        self._text = text
        self._show = False
        self._status_started = 0.0

    def update(self) -> Optional[str]:
        now = monotonic()
        wait_time = 1.0 if self._show else 0.1
        if now - self._status_started > wait_time:
            self._show = not self._show
            self._status_started = now
            return self._text if self._show else ""
        return None


class Fixed(DisplayStrategy):
    def __init__(self, text: str) -> None:
        self._text = text
        self._active = False

    def update(self) -> Optional[str]:
        if not self._active:
            self.active = True
            return self._text
        return None
