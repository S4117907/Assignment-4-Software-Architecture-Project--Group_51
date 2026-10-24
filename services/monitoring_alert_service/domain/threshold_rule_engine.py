"""Threshold Rule Engine component.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.dev_seed import seed

SEVERITY_ORDER = {"WARNING": 1, "CRITICAL": 2}


@dataclass(frozen=True)
class RuleMatch:
    alert_type: str
    severity: str
    threshold: float
    direction: str  # "below" or "above"


class ThresholdRuleEngine:
    def __init__(self) -> None:
        self._rules: list[dict[str, Any]] = seed("alertThresholds")

    def evaluate(self, metric: str, value: float) -> RuleMatch | None:
        best: RuleMatch | None = None
        for rule in self._rules:
            if rule["metric"] != metric:
                continue
            if "below" in rule and value < rule["below"]:
                match = RuleMatch(rule["alertType"], rule["severity"], rule["below"], "below")
            elif "above" in rule and value > rule["above"]:
                match = RuleMatch(rule["alertType"], rule["severity"], rule["above"], "above")
            else:
                continue
            if best is None or SEVERITY_ORDER[match.severity] > SEVERITY_ORDER[best.severity]:
                best = match
        return best
