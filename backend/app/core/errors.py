from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):

    code: str = "app_error"
    status_code: int = 500
    message: str = "Internal application error"

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or {}


class NotFoundError(AppError):
    code = "not_found"
    status_code = 404
    message = "Resource not found"


class ValidationAppError(AppError):
    code = "validation_error"
    status_code = 422
    message = "Validation failed"


class LLMError(AppError):
    code = "llm_error"
    status_code = 502
    message = "LLM provider returned an invalid response"


def _envelope(code: str, message: str, status: int, details: Any = None) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": code, "message": message, "status": status}}
    if details:
        body["error"]["details"] = details
    return body


async def app_error_handler(_: Request, exc: AppError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.code, exc.message, exc.status_code, exc.details or None),
    )


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=exc.status_code,
        content=_envelope("http_error", str(exc.detail), exc.status_code),
    )


async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=422,
        content=_envelope("validation_error", "Request validation failed", 422, exc.errors()),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> ORJSONResponse:
    import logging

    logging.getLogger(__name__).exception("unhandled_exception", exc_info=exc)
    return ORJSONResponse(
        status_code=500,
        content=_envelope("internal_error", "Internal server error", 500),
    )
