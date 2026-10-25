# Architectural Decision Records

Recorded with the course ADR template. Source of truth for the report tables.

## ADR 1: Service-Based Architecture with Event-Driven Telemetry Processing for OzAgriMate

**Status:** Accepted

**Context:** OzAgriMate must grow from 5,000 to over 50,000 farms, remain available for time
sensitive monitoring and irrigation, and integrate heterogeneous devices and providers. 
Telemetry arrives continuously, while farm management is request-driven. Alternatives 
considered: layered or modular monolith (cheap and simple, but one-star scalability, 
elasticity and fault tolerance); microkernel with device plug-ins (extensible, yet still a 
single deployment unit); pure event-driven architecture (five-star responsiveness and 
fault tolerance, but poor testability and simplicity); and microservices (five-star 
scalability, but highest cost, lowest simplicity and limited team experience). 

**Decision:** We will use a service-based architecture of six coarse-grained domain services (Farm 
and Device Management, Telemetry Ingestion, Monitoring and Alert, External 
Integration) behind an API Gateway, with an event-driven Message Broker for 
telemetry and alert flows. Services deploy and scale independently, so high-volume 
ingestion scales without scaling farm administration, and one failed service does not 
stop others. Service-based architecture offers four-star maintainability, testability and 
deployability at moderate cost; the event-driven path adds the responsiveness telemetry 
needs without microservices' operational complexity. 

**Consequences:** Positive: independent deployment, targeted scaling, and domain-partitioned code 
matching the business. Negative: network latency and partial failures between services; 
the shared Operational Database couples services at schema level and harder end-to
end testing; coarse services may later need splitting if growth exceeds forecasts. 

**Compliance:** Architecture reviews and automated dependency checks will confirm services interact 
only through published APIs or broker topics, never through another service's code or 
database schema. 

## ADR 2: Horizontal Auto-Scaling of Stateless Services and Farm-Partitioned Telemetry Streams for Scalability

**Status:** Accepted

**Context:** Farm numbers will grow tenfold to over 50,000, and ASR2 requires at least 99% 
acceptance of valid telemetry at that load, with 95% reaching monitoring within 5 
seconds (ASR3). Telemetry volume grows faster than user traffic because every farm 
adds many devices, and irrigation season creates peaks. Alternatives considered: 
vertical scaling onto larger servers; permanent provisioning for peak load (wasteful 
outside irrigation season); and horizontal scaling of stateless instances with partitioned 
event streams. 

**Decision:** We will keep every service stateless and run it on Kubernetes with Horizontal Pod 
Autoscalers driven by CPU and broker consumer lag. Telemetry events are keyed by 
farmId and spread across Message Broker partitions, so Telemetry Ingestion and 
Monitoring and Alert instances process different farms in parallel while preserving 
each farm's event order. Each service therefore scales to its own load, and growth is 
handled by adding instances and partitions rather than redesigning the system. 

**Consequences:** Positive: near-linear throughput growth, cost proportional to load, and preserved per
farm ordering. Negative: partition counts must be planned; a very large farm can create 
a hot partition; new instances need warm-up time; caches and session state must live 
outside instances. 

**Compliance:** Quarterly load tests at 50,000-farm volume must show at least 99% telemetry 
acceptance and P95 five-second processing; dashboards track consumer lag and 
autoscaling events. 

## ADR 3: Redundant Multi-Zone Instances, Health Checks and Circuit Breakers for Availability

**Status:** Accepted

**Context:** ASR7 requires 99.9% monthly availability (about 43 minutes of downtime), and ASR8 
requires that a failed weather, mapping or notification provider must not make core 
monitoring unavailable. Farms irrigate around the clock, so outages have physical 
consequences. Alternatives considered: a single-zone deployment with backups; active
active multi-region deployment and multi-zone redundancy combined with health 
checks and fault-isolation patterns. 

**Decision:** We will run at least two instances of every service across availability zones in the 
AWS Sydney region, with Kubernetes readiness and liveness probes removing 
unhealthy instances automatically. The Operational Database uses Multi-AZ failover, 
and the Message Broker replicates partitions across three zones. All external providers 
are called only through the External Integration Service, using timeouts and circuit 
breakers that return cached weather or map data when a provider fails. This meets 
99.9% at reasonable cost without multi-region complexity. 

**Consequences:** Positive: tolerates instance and zone failures; failed instances recover automatically. 
Negative: duplicate capacity raises infrastructure cost; cached provider data may be 
stale and must be flagged to users. 

**Compliance:** Synthetic probes measure monthly availability against the 99.9% objective; quarterly 
chaos tests terminate instances, a zone and a provider to confirm monitoring continues. 

## ADR 4: Versioned REST APIs and Protocol Adapters for Interoperability

**Status:** Accepted

**Context:** OzAgriMate needs to receive data from sensors made by different suppliers and 
connect with services such as weather, GIS and notifications. These systems may not 
use the same protocol or data format. If every service connects to them directly, the 
platform will become difficult to update and maintain. We considered requiring all 
devices to use one protocol and using standard APIs with protocol adapters.

**Decision:** We decided to use versioned REST APIs with JSON for communication between 
OzAgriMate services and external providers. Protocol adapters will convert MQTT and 
vendor-specific device messages into one shared telemetry format. API versioning will 
help us introduce changes without immediately breaking existing clients. This option 
gives the platform more flexibility, reduces dependence on specific vendors and makes 
it easier to add new devices and external services later. 

**Consequences:** This makes the platform easier to extend and reduces changes to core services when a 
new device or provider is added. However, the adapters and shared formats must be 
maintained carefully. Translation can also add a small processing delay and create 
more components to test and monitor. 

**Compliance:** We will use API contract tests to check JSON formats and version compatibility. 
Integration tests will verify that each supported device format converts into the shared 
telemetry model. 

## ADR 5: JWT, Role-Based Access and Encryption for Platform Security

**Status:** Accepted

**Context:** OzAgriMate stores farm information, sensor readings and irrigation commands. If an 
account or API is accessed without permission, private data could be exposed and 
equipment could be controlled incorrectly. The platform also serves different users, 
including farmers and administrators, who should not have the same permissions. We 
considered using API keys only, network-level protection, and a layered approach 
using authenticated identities, roles and encryption. 

**Decision:** We decided to protect OzAgriMate with TLS for data in transit, JWT-based 
authentication and role-based access control. Each request will be checked to confirm 
the user's identity, role and farm access before protected information or commands are 
processed. Tenant data will be separated by farm, and important actions will be 
recorded in audit logs. Administrators must also use multi-factor authentication. This 
layered approach provides stronger protection than API keys or network restrictions 
alone. 

**Consequences:** Farm data and irrigation controls receive stronger protection, while roles limit what 
each user can view or change. However, token management, permission rules and 
tenant separation add development effort. Incorrect security configuration could block 
legitimate users or expose information. 

**Compliance:** Automated tests will verify authentication, role permissions and tenant isolation. TLS 
configuration and audit logs will be reviewed before release and during security 
checks. 

## ADR 6: Apache Kafka for Asynchronous Telemetry and Alert Messaging

**Status:** Accepted

**Context:** OzAgriMate may receive continuous telemetry from thousands of farms. If Telemetry 
Ingestion calls the Monitoring and Alert services directly, unavailable service could delay incoming readings and cause failures to spread. The platform needs a reliable 
way to pass telemetry and alert events between services without making them depend 
directly on each other. We considered synchronous REST calls, RabbitMQ and Apache 
Kafka.  

**Decision:** We decided to use Apache Kafka as the message broker for telemetry and alert events. 
The Telemetry Ingestion Service will publish events to Kafka, while the Monitoring 
and Alert Service and AI Advisory Service will consume them independently. Kafka 
was selected because it can handle large event streams, retain messages for replay and 
scale through partitioning. This supports the expected growth from 5,000 to more than 
50,000 farms and prevents telemetry processing from being blocked by slower 
services.

**Consequences:** Services can process events independently, scale separately and recover missed events 
through replay. Temporary consumer outages will not stop telemetry ingestion. 
However, Kafka adds deployment and monitoring complexity, uses more 
infrastructure. Duplicate or out-of-order events may also need to be handled. 

**Compliance:** Monitoring will track broker availability, consumer lag and failed messages. 
Integration tests will verify event schemas, delivery and safe handling of duplicate 
telemetry events. 

## ADR 7: Separate Operational Relational Data from Time-Series Telemetry Data

**Status:** Accepted

**Context:** OzAgriMate stores two very different kinds of data. Telemetry is append-only, very 
high-volume, queried by time range and grows with every device. Keeping both in one 
database would let telemetry writes slow down farm management. Alternatives 
considered: one shared relational database; a separate database for every service 
(microservices-style); and two stores, a shared operational database plus a dedicated 
time-series database.

**Decision:** We will store farms, devices, alerts, commands and audit records in a PostgreSQL 
Operational Database, with a separate schema owned by each service, and store 
telemetry in a TimescaleDB Time-Series Database written only by the Telemetry 
Ingestion Service. Other services receive telemetry through Message Broker events 
instead of reading its tables. This applies the service-based 'break apart the database' 
variant: each store suits its workload, and compression are managed independently. 

**Consequences:** Positive: each workload uses an optimised store; telemetry scales, compresses and 
expires independently; transactional data keeps ACID guarantees. Negative: two 
database technologies to operate, back up and secure; cross-store reports need 
application-level joins or an analytics pipeline; schema ownership must be enforced. 

**Compliance:** Database permissions grant each service access only to its own schema, and only 
Telemetry Ingestion may write telemetry. Recovery tests verify the 15-minute RPO. 

## ADR 8: Centralised Logging, Metrics and Distributed Tracing with OpenTelemetry for Observability

**Status:** Accepted

**Context:** One request, such as an irrigation command, several services, the Message Broker and 
farm devices. When something fails, support staff must find where and why quickly to 
meet the two-hour RTO (ASR23), and ASR24 requires health, latency, error-rate and 
throughput telemetry. Observability was an implicit characteristic in Assignment 2 that 
becomes critical in a distributed design. Alternatives considered: local log files per service; a commercial all-in-one monitoring product; and vendor-neutral 
OpenTelemetry instrumentation feeding open-source back ends. 

**Decision:** We will instrument every service with OpenTelemetry and send structured JSON logs, 
metrics and traces to an OpenTelemetry Collector, which forwards them to Loki (logs), 
Prometheus (metrics) and Tempo (traces), visualised in Grafana. Vendor-neutral 
instrumentation avoids lock-in, supports our interoperability goal, and lets support staff 
follow one request across all services. 

**Consequences:** 
Positive: faster diagnosis, measurable service-level objectives and early warning of 
capacity or availability problems. Negative: extra infrastructure and storage cost; 
instrumentation effort in every service; logs must exclude sensitive farm or personal 
data; high-volume telemetry paths need trace sampling. 

**Compliance:**  
Release checks verify every service emits structured logs, metrics and correlation IDs; 
Grafana alerts fire when error-rate or latency objectives are breached. 