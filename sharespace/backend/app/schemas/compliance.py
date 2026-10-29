from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SafetyPermitCreate(BaseModel):
    user_id: UUID
    permit_type: str = Field(..., max_length=100)
    issuer: Optional[str] = Field(None, max_length=255)
    issue_date: datetime
    expiry_date: datetime
    document_url: Optional[str] = Field(None, max_length=1024)


class SafetyPermitResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    permit_type: str
    issuer: Optional[str] = None
    issue_date: datetime
    expiry_date: datetime
    status: str
    document_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QualificationCreate(BaseModel):
    user_id: UUID
    resource_id: Optional[UUID] = None
    qualification_code: str = Field(..., max_length=100)
    title: str = Field(..., max_length=255)
    certified_by: Optional[str] = Field(None, max_length=255)
    certified_at: datetime
    expires_at: Optional[datetime] = None


class QualificationResponse(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: UUID
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    resource_id: Optional[UUID] = None
    resource_name: Optional[str] = None
    qualification_code: str
    title: str
    certified_by: Optional[str] = None
    certified_at: datetime
    expires_at: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    user_email: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    payload_before: Optional[dict] = None
    payload_after: Optional[dict] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
