from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MembershipSummary(BaseModel):
    membership_id: UUID
    organization_id: UUID
    organization_name: str
    organization_slug: str
    role: str
    department: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    user: UserResponse
    memberships: List[MembershipSummary] = []


class DemoTokenRequest(BaseModel):
    persona: Optional[str] = Field(
        default=None,
        description="Demo persona to impersonate (student, manager, admin, technician, researcher, auditor)",
    )
    role: Optional[str] = Field(
        default=None,
        description="Alternative field for persona",
    )

    @model_validator(mode="after")
    def validate_persona(self) -> "DemoTokenRequest":
        chosen = self.persona or self.role
        if not chosen or chosen not in ("student", "manager", "admin", "technician", "researcher", "auditor"):
            raise ValueError(f"Invalid persona '{chosen}'. Must be one of: student, manager, admin, technician, researcher, auditor")
        self.persona = chosen
        return self



class DemoTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    active_role: str
