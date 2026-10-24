# IoT Device Hub (container): EMQX MQTT broker cluster

* Farm gateways connect over **MQTT 5 with TLS and per-device X.509 certificates** (ADR 4, ADR 5).
* Telemetry topic: `ozagrimate/farms/{farmId}/devices/{deviceId}/telemetry`. The Telemetry Ingestion
  Service's *MQTT Protocol Adapter* subscribes to it.
* Command topic: `ozagrimate/farms/{farmId}/zones/{zoneId}/commands` (QoS 1). The Irrigation Control
  Service's *Device Command Dispatcher* publishes here; gateways acknowledge on `.../commands/ack`.
* ACLs restrict each gateway certificate to its own farm's topics (tenant isolation).
* Gateways buffer readings while rural links are down and replay them with original timestamps (ASR9).

Not implemented in the prototype. Dispatched commands are
written to `.local_event_bus/iot-device-hub.commands.log` instead.
