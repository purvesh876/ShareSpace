import re
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import logger


def _with_cors_headers(request: Request, response: JSONResponse) -> JSONResponse:
    """Ensure custom exception responses always preserve required CORS headers."""
    origin = request.headers.get("origin")
    if not origin:
        return response

    is_allowed = False
    if origin in settings.cors_origins:
        is_allowed = True
    elif settings.cors_origin_regex and re.match(settings.cors_origin_regex, origin):
        is_allowed = True

    if is_allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Vary"] = "Origin"

    return response


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


class DatabaseUnavailableException(AppException):
    def __init__(self, message: str = "Database connection is not configured or unavailable"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="DATABASE_UNAVAILABLE"
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning("Application error: [%s] %s on %s", exc.code, exc.message, request.url.path)
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )
    return _with_cors_headers(request, response)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.info("Validation error on %s: %s", request.url.path, exc.errors())
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request payload validation failed.",
                "details": jsonable_encoder(exc.errors()),
            }
        },
    )
    return _with_cors_headers(request, response)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.warning("HTTP error %s on %s: %s", exc.status_code, request.url.path, exc.detail)
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc.detail),
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": {}
            }
        }
    )
    return _with_cors_headers(request, response)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled server exception on %s: %s", request.url.path, str(exc), exc_info=True)
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {}
            }
        }
    )
    return _with_cors_headers(request, response)

