"""Loads the dummy reference data that stands in for the shared Operational Database."""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SEED_FILE = Path(__file__).resolve().parents[1] / "infrastructure" / "operational_database" / "seed_data.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with SEED_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)


def seed(section: str) -> list[dict[str, Any]]:
    """Return a deep copy so each service owns its in-memory data independently."""
    return copy.deepcopy(_load()[section])
