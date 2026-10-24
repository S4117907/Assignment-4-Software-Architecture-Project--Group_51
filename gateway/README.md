# API Gateway (container)

Single entry point for the open API v1. It validates JWTs from the Identity Provider, applies rate
limiting, creates the `X-Correlation-Id`, forwards verified identity claims (`X-User-Id`,
`X-User-Role`, `X-Farm-Access`) and routes each path to its domain service. See `api_gateway/kong.yml`.

**Not implemented in the prototype** (the brief excludes it). Postman sends the claim headers directly to
each service, which is exactly what the gateway would forward.
