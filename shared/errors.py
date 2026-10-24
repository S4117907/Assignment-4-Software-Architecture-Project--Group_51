"""Standard error handling shared by all OzAgriMate services.

Every error response uses the same envelope so API consumers (the Web and Mobile
Application, farm gateways and third-party systems) can handle failures uniformly:

"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .observability import get_correlation_id


class ApiError(Exception):
    """A business error that maps directly to an HTTP status code."""

    def __init__(self, status_code: int, code: str, message: str, details: list[Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def not_found(code: str, message: str) -> ApiError:
    return ApiError(status.HTTP_404_NOT_FOUND, code, message)


def conflict(code: str, message: str) -> ApiError:
    return ApiError(status.HTTP_409_CONFLICT, code, message)


def unprocessable(code: str, message: str, details: list[Any] | None = None) -> ApiError:
    return ApiError(422, code, message, details)


def forbidden(code: str, message: str) -> ApiError:
    return ApiError(status.HTTP_403_FORBIDDEN, code, message)


def unauthorized(code: str, message: str) -> ApiError:
    return ApiError(status.HTTP_401_UNAUTHORIZED, code, message)


def _envelope(code: str, message: str, details: list[Any] | None = None) -> dict[str, Any]:
    return {
        "error": {"code": code, "message": message, "details": details or []},
        "correlationId": get_correlation_id(),
    }


def install_error_handlers(app: FastAPI) -> None:
    """Register handlers so every error leaves the service in the standard envelope."""

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_envelope(exc.code, exc.message, exc.details))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in err.get("loc", []) if part != "body"),
                "issue": err.get("msg", "Invalid value"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_envelope("VALIDATION_FAILED", "The request contains invalid data.", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        if exc.status_code == 405:
            code = "METHOD_NOT_ALLOWED"
        return JSONResponse(status_code=exc.status_code, content=_envelope(code, str(exc.detail)))
