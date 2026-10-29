from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ResourceCategory


class ResourceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    category: str = Field(default=ResourceCategory.LAB_INSTRUMENT.value)
    description: Optional[str] = None
    location: Optional[str] = None
    requires_approval: bool = True
    requires_permit: bool = False
    requires_qualification: bool = False
    hourly_rate_credits: int = Field(default=0, ge=0)
    specifications_json: Optional[Dict[str, Any]] = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    is_available: Optional[bool] = None
    requires_approval: Optional[bool] = None
    requires_permit: Optional[bool] = None
    requires_qualification: Optional[bool] = None
    hourly_rate_credits: Optional[int] = Field(None, ge=0)
    specifications_json: Optional[Dict[str, Any]] = None


class ResourceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    category: str
    description: Optional[str] = None
    location: Optional[str] = None
    is_available: bool = True
    requires_approval: bool = True
    requires_permit: Optional[bool] = False
    requires_qualification: Optional[bool] = False
    hourly_rate_credits: Optional[int] = 0

    specifications_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    status: str


class ResourceAvailabilityResponse(BaseModel):
    resource_id: UUID
    resource_name: str
    is_available: bool
    requires_approval: bool
    reserved_slots: List[TimeSlot]
