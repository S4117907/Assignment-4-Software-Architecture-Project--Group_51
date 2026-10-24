"""Deduplication Filter component (ASR10).
"""

from __future__ import annotations

import threading
from datetime import datetime


class DeduplicationFilter:
    def __init__(self) -> None:
        self._seen: dict[str, datetime] = {}
        self._lock = threading.Lock()

    def first_seen(self, event_id: str) -> datetime | None:
        return self._seen.get(event_id)

    def remember(self, event_id: str, received_at: datetime) -> None:
        with self._lock:
            self._seen.setdefault(event_id, received_at)
