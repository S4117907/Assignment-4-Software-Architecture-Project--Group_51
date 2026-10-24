"""Circuit Breaker used by every External Integration Service adapter (ADR 3).


This stops a failing weather, mapping or notification provider from tying up threads
and keeps core farm monitoring available (ASR8).
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitBreaker:
    CLOSED, OPEN, HALF_OPEN = "CLOSED", "OPEN", "HALF_OPEN"

    def __init__(self, name: str, failure_threshold: int = 3, reset_timeout: float = 30.0,
                 clock: Callable[[], float] = time.monotonic):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return self.CLOSED
        if self._clock() - self._opened_at >= self.reset_timeout:
            return self.HALF_OPEN
        return self.OPEN

    def call(self, operation: Callable[[], T], fallback: Callable[[], T]) -> T:
        if self.state == self.OPEN:
            return fallback()
        try:
            result = operation()
        except Exception:
            self._failures += 1
            if self.state == self.HALF_OPEN or self._failures >= self.failure_threshold:
                self._opened_at = self._clock()
            return fallback()
        self._failures = 0
        self._opened_at = None
        return result
