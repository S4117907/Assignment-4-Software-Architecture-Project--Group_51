# AI Advisory Service (container)

**Responsibility:** produces explainable irrigation and resource-optimisation recommendations
from telemetry, weather and crop data. Every recommendation states its input data period and
a confidence score (ASR25), and AI-generated irrigation changes are only *suggested*. A farm
manager must confirm them, and the Irrigation Control Service enforces that confirmation (ASR27).

| Component | Folder | Status in prototype |
|---|---|---|
| Recommendation API Router | `api/` | Planned |
| Telemetry Feature Consumer (`telemetry.received`) | `domain/` | Planned |
| Irrigation Recommendation Engine | `domain/` | Planned |
| Model Registry (versioned ML models) | `models/` | Planned |
| Recommendation Repository | `repository/` | Planned |

None of the 8 documented endpoints belong to this service, so the folders are intentionally empty.
