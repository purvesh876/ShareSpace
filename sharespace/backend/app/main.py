from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Initialize logging and verify environment
    setup_logging(debug=settings.debug)
    logger.info(
        "Starting %s v%s in [%s] mode",
        settings.app_name,
        settings.app_version,
        settings.app_env,
    )
    logger.info("Configured CORS origins: %s (regex: %s)", settings.cors_origins, settings.cors_origin_regex)
    if settings.database_url:
        # Redact password before logging DB target host
        safe_db_url = settings.database_url.split("@")[-1] if "@" in settings.database_url else "configured"
        logger.info("Configured Database target: %s", safe_db_url)
    else:
        logger.info("No DATABASE_URL configured yet. Running in detached mode.")

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ShareSpace Backend: Resource-sharing platform for college and research communities.",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url=f"{settings.api_v1_str}/docs",
    redoc_url=f"{settings.api_v1_str}/redoc",
    lifespan=lifespan,
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=600,
)

# Exception handlers for consistent API responses
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include API v1 router
app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "docs": f"{settings.api_v1_str}/docs",
        "health": f"{settings.api_v1_str}/health",
        "ready": f"{settings.api_v1_str}/ready",
    }
