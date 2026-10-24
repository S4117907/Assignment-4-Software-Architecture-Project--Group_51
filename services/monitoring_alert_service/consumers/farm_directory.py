"""Farm Directory: local replica of known farms, kept current from ``farm.events``."""

from __future__ import annotations

from shared.dev_seed import seed
from shared.messaging import EventConsumer, topics

CONSUMER_GROUP = "monitoring-alert-service"


class FarmDirectory:
    def __init__(self) -> None:
        self._farms = {farm["farmId"] for farm in seed("farms")}
        self._consumer = EventConsumer(topics.FARM_EVENTS, CONSUMER_GROUP)

    def exists(self, farm_id: str) -> bool:
        for event in self._consumer.poll():
            if event["eventType"] == "FarmRegistered":
                self._farms.add(event["payload"]["farmId"])
        return farm_id in self._farms
