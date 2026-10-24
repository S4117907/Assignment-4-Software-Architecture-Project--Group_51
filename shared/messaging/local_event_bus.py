"""Local stand-in for the Apache Kafka Message Broker (ADR 6).

* Events carry a key (the farmId) that would select the Kafka partition (ADR 2).
* Each consuming service keeps its own read offset, like a Kafka consumer group,
  so the same event can be consumed independently by several services.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..observability import get_correlation_id

_REPO_ROOT = Path(__file__).resolve().parents[2]
_lock = threading.Lock()


def bus_directory() -> Path:
    path = Path(os.environ.get("OZAGRIMATE_EVENT_BUS_DIR", _REPO_ROOT / ".local_event_bus"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _topic_file(topic: str) -> Path:
    return bus_directory() / f"{topic}.log"


class EventPublisher:
    """Publishes data-based event payloads to a topic."""

    def __init__(self, producer: str):
        self.producer = producer

    def publish(self, topic: str, key: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "eventId": f"EV-{uuid.uuid4().hex[:12]}",
            "eventType": event_type,
            "topic": topic,
            "key": key,
            "schemaVersion": 1,
            "producer": self.producer,
            "occurredAt": datetime.now(timezone.utc).isoformat(),
            "correlationId": get_correlation_id(),
            "payload": payload,
        }
        line = json.dumps(event, default=str)
        with _lock, _topic_file(topic).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return event


class EventConsumer:
    """Reads new events from a topic, remembering its own offset (consumer group)."""

    def __init__(self, topic: str, group: str):
        self.topic = topic
        self.group = group
        self._offset = 0  # number of events already consumed by this group

    def poll(self) -> list[dict[str, Any]]:
        path = _topic_file(self.topic)
        if not path.exists():
            return []
        with _lock, path.open("r", encoding="utf-8") as handle:
            lines = [line for line in handle.read().splitlines() if line.strip()]
        new_lines = lines[self._offset:]
        self._offset = len(lines)
        events: list[dict[str, Any]] = []
        for line in new_lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue  
        return events
