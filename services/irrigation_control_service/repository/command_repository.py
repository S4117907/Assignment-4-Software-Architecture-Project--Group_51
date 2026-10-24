"""Command Repository component.

Stores irrigation commands and their status history in the ``irrigation`` schema of the
Operational Database (ADR 7).
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any

ACTIVE_STATUSES = {"PENDING_DISPATCH", "DISPATCHED", "RUNNING"}


class CommandRepository:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._commands: dict[str, dict[str, Any]] = {}
        self._next_number = 1

    def next_command_id(self) -> str:
        with self._lock:
            command_id = f"CMD-{self._next_number:06d}"
            self._next_number += 1
            return command_id

    def save(self, command: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._commands[command["commandId"]] = command
        return command

    def get(self, command_id: str) -> dict[str, Any] | None:
        return self._commands.get(command_id)

    def active_start_for_zone(self, farm_id: str, zone_id: str) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc)
        for command in self._commands.values():
            if (command["farmId"], command["zoneId"], command["action"]) != (farm_id, zone_id, "START"):
                continue
            if command["status"] not in ACTIVE_STATUSES:
                continue
            if command["createdAt"] + timedelta(minutes=command["durationMinutes"]) > now:
                return command
        return None

    def stop_active_for_zone(self, farm_id: str, zone_id: str) -> None:
        with self._lock:
            for command in self._commands.values():
                if (command["farmId"], command["zoneId"], command["action"]) == (farm_id, zone_id, "START") \
                        and command["status"] in ACTIVE_STATUSES:
                    command["status"] = "SUPERSEDED_BY_STOP"
