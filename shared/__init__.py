"""OzAgriMate shared library.

A small, versioned library bundled with every domain service. It contains only cross-cutting concerns:

* errors        - the standard JSON error envelope used by every service
* observability - correlation-ID propagation and structured JSON logging (ADR 8)
* security      - reading identity claims forwarded by the API Gateway (ADR 5)
* messaging     - a local stand-in for the Apache Kafka Message Broker (ADR 6)

"""

__version__ = "1.0.0"
