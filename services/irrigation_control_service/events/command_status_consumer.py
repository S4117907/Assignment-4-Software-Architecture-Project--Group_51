"""Command Status Consumer component.

"""

from __future__ import annotations

from shared.messaging import EventConsumer, topics

from ..repository.command_repository import CommandRepository

CONSUMER_GROUP = "irrigation-control-service"
VALID_STATUSES = {"RUNNING", "COMPLETED", "FAILED", "ACK_TIMEOUT"}


class CommandStatusConsumer:
    def __init__(self, repository: CommandRepository):
        self._repository = repository
        self._consumer = EventConsumer(topics.IRRIGATION_COMMAND_STATUS, CONSUMER_GROUP)

    def drain(self) -> int:
        events = self._consumer.poll()
        for event in events:
            payload = event.get("payload", {})
            command = self._repository.get(payload.get("commandId", ""))
            if command and payload.get("status") in VALID_STATUSES:
                command["status"] = payload["status"]
        return len(events)
