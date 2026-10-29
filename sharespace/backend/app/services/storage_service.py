import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.logging import logger

# Maximum allowed file size: 10 MB
MAX_EVIDENCE_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Strictly permitted image MIME types and their canonical extensions
ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def validate_image_file_content(file_bytes: bytes, declared_content_type: str) -> str:
    """
    Validate declared content-type, file size, and inspect binary magic bytes.
    Returns canonical file extension.
    Fails closed on disguised executables, scripts, or non-image payloads.
    """
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evidence file payload is empty.",
        )

    if len(file_bytes) > MAX_EVIDENCE_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Evidence file exceeds maximum permitted size of {MAX_EVIDENCE_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    content_type = (declared_content_type or "").lower().split(";")[0].strip()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{content_type}'. Allowed types: {list(ALLOWED_MIME_TYPES.keys())}.",
        )

    # Magic byte inspection
    is_valid_magic = False
    if content_type == "image/jpeg" and file_bytes.startswith(b"\xff\xd8\xff"):
        is_valid_magic = True
    elif content_type == "image/png" and file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        is_valid_magic = True
    elif content_type == "image/webp" and file_bytes.startswith(b"RIFF") and b"WEBP" in file_bytes[:16]:
        is_valid_magic = True

    if not is_valid_magic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File signature does not match declared image MIME type. File content rejected.",
        )

    return ALLOWED_MIME_TYPES[content_type]


class StorageService:
    @staticmethod
    def is_configured() -> bool:
        """
        Check if Supabase Storage credentials and bucket are properly configured.
        """
        return bool(
            settings.supabase_url
            and settings.supabase_service_role_key
            and settings.resolved_storage_bucket
        )

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        bucket = settings.resolved_storage_bucket
        configured = cls.is_configured()
        return {
            "configured": configured,
            "provider": settings.evidence_storage_provider,
            "bucket_name": bucket if configured else None,
        }

    @classmethod
    async def upload_evidence(
        cls,
        organization_id: UUID,
        booking_id: UUID,
        handover_type: str,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
    ) -> Dict[str, Any]:
        """
        Securely upload an evidence photograph to the private Supabase Storage bucket.
        Validates payload bytes, derives opaque tenant-scoped key, and generates short-lived signed URL.
        """
        if not cls.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Private evidence storage is not configured in this environment.",
            )

        clean_handover = handover_type.lower().strip()
        if clean_handover not in ("checkin", "return"):
            clean_handover = "checkin"

        extension = validate_image_file_content(file_bytes, content_type)

        # Build opaque tenant-isolated object path
        token_id = uuid.uuid4().hex[:12]
        object_path = f"org_{organization_id}/booking_{booking_id}/{clean_handover}_{token_id}{extension}"
        bucket = settings.resolved_storage_bucket
        base_url = settings.supabase_url.rstrip("/")
        service_key = settings.supabase_service_role_key

        headers = {
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        # 1. Upload to Supabase Storage REST API
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                upload_res = await client.post(
                    f"{base_url}/storage/v1/object/{bucket}/{object_path}",
                    headers=headers,
                    content=file_bytes,
                )
        except Exception as exc:
            logger.error("Failed to connect to Supabase Storage: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to connect to storage service provider.",
            ) from exc

        if upload_res.status_code not in (200, 201):
            logger.error(
                "Supabase Storage upload failed [%s]: %s",
                upload_res.status_code,
                upload_res.text,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to upload evidence object to storage provider.",
            )

        # 2. Generate initial signed download URL
        signed_url = await cls.generate_signed_url(
            organization_id=organization_id,
            booking_id=booking_id,
            storage_path=object_path,
            expires_in=settings.storage_signed_url_expiry,
        )

        return {
            "storage_path": object_path,
            "signed_url": signed_url,
            "filename": original_filename,
            "content_type": content_type,
            "size_bytes": len(file_bytes),
            "handover_type": clean_handover,
            "uploaded_at": datetime.now(timezone.utc),
        }

    @classmethod
    async def generate_signed_url(
        cls,
        organization_id: UUID,
        booking_id: UUID,
        storage_path: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a short-lived authenticated download URL for a private evidence object.
        Enforces strict path prefix validation to prevent cross-tenant object access.
        """
        if not cls.is_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Private evidence storage is not configured in this environment.",
            )

        expected_prefix = f"org_{organization_id}/booking_{booking_id}/"
        if not storage_path.startswith(expected_prefix):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: storage path does not belong to the requested booking scope.",
            )

        bucket = settings.resolved_storage_bucket
        base_url = settings.supabase_url.rstrip("/")
        service_key = settings.supabase_service_role_key

        headers = {
            "Authorization": f"Bearer {service_key}",
            "apikey": service_key,
            "Content-Type": "application/json",
        }

        payload = {"expiresIn": max(60, min(expires_in, 86400))}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                sign_res = await client.post(
                    f"{base_url}/storage/v1/object/sign/{bucket}/{storage_path}",
                    headers=headers,
                    json=payload,
                )
        except Exception as exc:
            logger.error("Failed to connect to Supabase Storage sign endpoint: %s", str(exc))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to connect to storage service provider.",
            ) from exc

        if sign_res.status_code != 200:
            logger.error(
                "Supabase Storage sign failed [%s]: %s",
                sign_res.status_code,
                sign_res.text,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence object not found or could not be signed.",
            )

        data = sign_res.json()
        relative_signed_url = data.get("signedURL")
        if not relative_signed_url:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Storage provider did not return signed download URL.",
            )

        return f"{base_url}/storage/v1{relative_signed_url}"
