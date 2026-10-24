"""
Records every irrigation-control action with actor and timestamp. Each record stores the
SHA-256 hash of the previous record, forming a hash chain: altering or deleting any past
record breaks every later hash, which makes tampering evident.

"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any

GENESIS_HASH = "0" * 64


class AuditLogger:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: list[dict[str, Any]] = []

    def record(self, actor: str, action: str, details: dict[str, Any]) -> str:
        with self._lock:
            previous_hash = self._records[-1]["hash"] if self._records else GENESIS_HASH
            record = {
                "auditRecordId": f"AUD-{len(self._records) + 1:06d}",
                "actor": actor,
                "action": action,
                "details": details,
                "recordedAt": datetime.now(timezone.utc).isoformat(),
                "previousHash": previous_hash,
            }
            record["hash"] = hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()
            self._records.append(record)
            return record["auditRecordId"]

    def verify_chain(self) -> bool:
        previous = GENESIS_HASH
        for record in self._records:
            body = {k: v for k, v in record.items() if k != "hash"}
            expected = hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()
            if record["previousHash"] != previous or record["hash"] != expected:
                return False
            previous = record["hash"]
        return True

    @property
    def records(self) -> list[dict[str, Any]]:
        return list(self._records)
