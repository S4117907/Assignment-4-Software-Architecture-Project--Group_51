"""Correlation-ID propagation and structured logging (ADR 8).

In production the API Gateway creates an ``X-Correlation-Id`` for every request and
OpenTelemetry exports logs, metrics and traces to the Observability Stack. 

"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request

CORRELATION_HEADER = "X-Correlation-Id"
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return _correlation_id.get() or "not-set"


def _build_logger(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_event(service_name: str, message: str, **fields: object) -> None:
    """Write one structured JSON log line (the format the OpenTelemetry Collector ingests)."""
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "service": service_name,
        "correlationId": get_correlation_id(),
        "message": message,
        **fields,
    }
    _build_logger(service_name).info(json.dumps(record, default=str))


def install_observability(app: FastAPI, service_name: str) -> None:
    """Add middleware that propagates the correlation ID and logs each request."""

    @app.middleware("http")
    async def _correlation_middleware(request: Request, call_next):
        correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
        token = _correlation_id.set(correlation_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers[CORRELATION_HEADER] = correlation_id
            log_event(
                service_name,
                "request.completed",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                durationMs=round((time.perf_counter() - started) * 1000, 2),
            )
            return response
        finally:
            _correlation_id.reset(token)
