from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationMemberResponse(BaseModel):
    membership_id: UUID
    user_id: UUID
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool
    joined_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationContextResponse(BaseModel):
    organization: OrganizationResponse
    user_role: str
    membership_id: UUID


class AuditEventResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignMemberRequest(BaseModel):
    email: str
    role: str = "student"
    department: Optional[str] = None

