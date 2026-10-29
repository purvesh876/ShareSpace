from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    app_name: str = Field(..., example="ShareSpace API")
    version: str = Field(..., example="0.1.0")
    environment: str = Field(..., example="development")
    timestamp: datetime = Field(..., example="2026-10-28T15:30:00Z")
    database_configured: bool = Field(
        default=False,
        example=False,
        description="Whether a PostgreSQL DATABASE_URL is configured in backend settings",
    )


class ReadinessResponse(BaseModel):
    status: str = Field(..., example="ready")
    database: str = Field(..., example="connected")
    timestamp: datetime = Field(..., example="2026-10-28T15:30:00Z")
    message: Optional[str] = Field(None, example="Database connection verified successfully.")
