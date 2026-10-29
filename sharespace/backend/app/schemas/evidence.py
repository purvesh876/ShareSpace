from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StorageStatusResponse(BaseModel):
    configured: bool = Field(..., description="Whether private evidence storage is configured")
    provider: str = Field(..., description="Configured storage provider")
    bucket_name: Optional[str] = Field(None, description="Name of the private bucket")


class EvidenceUploadResponse(BaseModel):
    storage_path: str = Field(..., description="Opaque tenant-scoped object key in storage bucket")
    signed_url: str = Field(..., description="Short-lived authenticated download URL")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="Validated MIME type")
    size_bytes: int = Field(..., description="Uploaded payload size in bytes")
    handover_type: str = Field(..., description="Handover step: checkin or return")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class SignedUrlResponse(BaseModel):
    storage_path: str = Field(..., description="Storage object key")
    signed_url: str = Field(..., description="Short-lived authenticated download URL")
    expires_in: int = Field(..., description="Expiration window in seconds")
