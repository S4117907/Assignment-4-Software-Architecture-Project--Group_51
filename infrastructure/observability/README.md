# Observability Stack (ADR 8)

| Element | Role |
|---|---|
| OpenTelemetry SDK (in every service) | Emits structured logs, metrics and traces |
| OpenTelemetry Collector | Receives OTLP data and routes it to the back ends |
| Prometheus | Metrics: latency, error rate, throughput, Kafka consumer lag |
| Loki | Centralised structured JSON logs |
| Tempo | Distributed traces linked by `X-Correlation-Id` |
| Grafana | Dashboards and SLO alerts for the Operations / Support team |

Prototype evidence: `shared/observability.py` propagates `X-Correlation-Id` on every response and
event, and writes one JSON log line per request in the format the collector ingests.
