# OzAgriMate Platform: Architecture Prototype - Assignment 4

A partial implementation of the OzAgriMate service-based architecture. It shows that the rchitecture in the Software Architecture Document can be realised in code.
**Eight REST endpoints** are implemented across **four independently deployable FastAPI services**, using in-memory dummy data as the brief requires.

## Team - Group 51

| Member | Name | Student ID | ADRs | Endpoints | Diagrams |
|---|---|---|---|---|---|
| A | Dineth Praveena | s4117907 | 1, 2, 3 | 1, 2, 3 | System Context, Farm and Device Component, Deployment |
| B | Md Abrar Waez Nahian | s4111762 | 4, 5, 6 | 4, 5, 6 | Container, Telemetry Ingestion Component, Telemetry runtime |
| C | Sheran Mickayel | s4064734 | 7, 8 | 7, 8 | Irrigation Control Component, Irrigation runtime |

## Run it

```bash
python -m pip install -r requirements.txt
python run_all.py            # starts all four services on ports 8001-8004
```

Then import `postman/OzAgriMate_API_v1.postman_collection.json` into Postman and run the folders in
order. Each service also has interactive OpenAPI docs at `http://localhost:<port>/docs`.
Restart `run_all.py` before re-running the collection so the in-memory data starts fresh.

Automated tests: `python -m pytest` (43 tests). Recorded results are in `docs/testing/`.

## The 8 endpoints (API v1)

| # | Method | Endpoint | Service (container) | Port |
|---|---|---|---|---|
| 1 | POST | `/api/v1/farms` | Farm and Device Management Service | 8001 |
| 2 | GET | `/api/v1/farms/{farmId}` | Farm and Device Management Service | 8001 |
| 3 | PUT | `/api/v1/farms/{farmId}` | Farm and Device Management Service | 8001 |
| 4 | POST | `/api/v1/telemetry` | Telemetry Ingestion Service | 8002 |
| 5 | GET | `/api/v1/farms/{farmId}/telemetry/latest` | Telemetry Ingestion Service | 8002 |
| 6 | GET | `/api/v1/farms/{farmId}/alerts` | Monitoring and Alert Service | 8003 |
| 7 | POST | `/api/v1/farms/{farmId}/irrigation-commands` | Irrigation Control Service | 8004 |
| 8 | DELETE | `/api/v1/farms/{farmId}/devices/{deviceId}` | Farm and Device Management Service | 8001 |

Identity headers (`X-User-Id`, `X-User-Role`, `X-Farm-Access`) stand in for the claims the API Gateway
forwards after validating a JWT (ADR 5). Every response carries an `X-Correlation-Id` (ADR 8).

## How the repository mirrors the architecture

**Container Diagram map to top-level folders:**

| Container | Folder | Implemented? |
|---|---|---|
| Web and Mobile Application | `clients/web_mobile_application/` | No (UI excluded by the brief) |
| API Gateway | `gateway/api_gateway/kong.yml` | Configuration only |
| Farm and Device Management Service | `services/farm_device_management_service/` | **Yes** (endpoints 1, 2, 3, 8) |
| Telemetry Ingestion Service | `services/telemetry_ingestion_service/` | **Yes** (endpoints 4, 5) |
| Monitoring and Alert Service | `services/monitoring_alert_service/` | **Yes** (endpoint 6) |
| Irrigation Control Service | `services/irrigation_control_service/` | **Yes** (endpoint 7) |
| AI Advisory Service | `services/ai_advisory_service/` | Structure only |
| External Integration Service | `services/external_integration_service/` | Circuit breaker only |
| IoT Device Hub (EMQX) | `infrastructure/iot_device_hub/` | Documented; local log stand-in |
| Message Broker (Kafka) | `infrastructure/message_broker/topics.yaml` + `shared/messaging/` | Local file-log stand-in |
| Operational Database (PostgreSQL) | `infrastructure/operational_database/` | Schema + seed data; in-memory at runtime |
| Time-Series Database (TimescaleDB) | `infrastructure/time_series_database/` | Schema; in-memory at runtime |

**Component Diagrams map to modules inside each service:**

| Component | Module |
|---|---|
| *Farm and Device Management Service* | |
| Farm API Router | `api/farm_router.py` |
| Device API Router | `api/device_router.py` |
| Access Policy Guard | `security/access_policy_guard.py` |
| Farm Manager | `domain/farm_manager.py` |
| Device Registry | `domain/device_registry.py` |
| Farm and Device Repository | `repository/farm_device_repository.py` |
| Domain Event Publisher | `events/domain_event_publisher.py` |
| *Telemetry Ingestion Service* | |
| Telemetry API Router | `api/telemetry_router.py` |
| MQTT Protocol Adapter | `adapters/mqtt_protocol_adapter.py` |
| Payload Normaliser | `adapters/payload_normaliser.py` |
| Ingestion Pipeline | `domain/ingestion_pipeline.py` (+ `latest_telemetry_query.py`) |
| Telemetry Validator | `domain/telemetry_validator.py` |
| Deduplication Filter | `domain/deduplication_filter.py` |
| Telemetry Repository | `repository/telemetry_repository.py` |
| Telemetry Event Publisher | `events/telemetry_event_publisher.py` |
| Device Directory Cache | `events/device_directory_cache.py` |
| *Irrigation Control Service* | |
| Irrigation Command API Router | `api/irrigation_command_router.py` |
| Access Policy Guard | `security/access_policy_guard.py` |
| Irrigation Command Manager | `domain/irrigation_command_manager.py` |
| Command Safety Validator | `domain/command_safety_validator.py` |
| Zone and Actuator Directory | `events/zone_actuator_directory.py` |
| Command Repository | `repository/command_repository.py` |
| Audit Logger | `audit/audit_logger.py` |
| Device Command Dispatcher | `dispatch/device_command_dispatcher.py` |
| Command Status Consumer | `events/command_status_consumer.py` |

`shared/` is a small versioned **shared library** (errors, security claims, observability,
messaging). It holds cross-cutting code only and never business logic, so services stay independent.

## Architecture decisions visible in code

| ADR | Where to look |
|---|---|
| 1 Service-based + event-driven telemetry | One deployable app per service; services interact only via `shared/messaging` events |
| 2 Scalability | Stateless services; events keyed by `farmId` ; `infrastructure/deployment/kubernetes/` HPA |
| 3 Availability | `external_integration_service/resilience/circuit_breaker.py`; multi-AZ spread in the Kubernetes manifest |
| 4 Interoperability | `/api/v1` versioned paths; `payload_normaliser.py` and `mqtt_protocol_adapter.py` |
| 5 Security | `shared/security.py` + each `access_policy_guard.py` (tenant checks, AI confirmation rule) |
| 6 Message broker | `shared/messaging/local_event_bus.py` (topic logs, consumer offsets) and `topics.yaml` |
| 7 Separate data stores | `operational_database/schema.sql` (schema per service) vs `time_series_database/schema.sql` |
| 8 Observability | `shared/observability.py` (correlation IDs, structured JSON logs) |
