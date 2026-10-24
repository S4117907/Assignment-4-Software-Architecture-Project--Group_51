# External Integration Service (container)

**Responsibility:** the only service that talks to third-party providers. It isolates the
platform from provider failures and protocol differences (ADR 3, ADR 4).

| Component | Folder | Status in prototype |
|---|---|---|
| Weather Provider Adapter | `adapters/` | Planned |
| Mapping / GIS Adapter | `adapters/` | Planned |
| Notification Adapter (SMS, email, push) | `adapters/` | Planned |
| Third-party Agricultural API Adapter (open API v1) | `adapters/` | Planned |
| Alert Notification Consumer (`alert.raised` topic) | `consumers/` | Planned |
| Circuit Breaker | `resilience/circuit_breaker.py` | **Implemented and unit-tested** |

None of the 8 documented endpoints belong to this service, so it has no API router yet.
