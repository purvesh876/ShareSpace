from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookingCreate(BaseModel):
    resource_id: UUID
    start_time: datetime
    end_time: datetime
    purpose: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode="after")
    def validate_time_range(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class BookingDecisionRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = Field(None, max_length=500)


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class BookingCheckinRequest(BaseModel):
    checklist_completed: bool = Field(True, description="Confirmation that pre-use safety checklist was completed")
    condition_notes: Optional[str] = Field(None, max_length=1000, description="Notes on initial equipment condition")
    photo_evidence_url: Optional[str] = Field(None, max_length=1024, description="URL or reference key of initial condition photo")


class BookingReturnRequest(BaseModel):
    checklist_completed: bool = Field(True, description="Confirmation that post-use return checklist was completed")
    condition_notes: Optional[str] = Field(None, max_length=1000, description="Notes on final equipment condition")
    incident_reported: bool = Field(False, description="Whether an incident or defect occurred during use")
    photo_evidence_url: Optional[str] = Field(None, max_length=1024, description="URL or reference key of return condition photo")


class BookingResponse(BaseModel):
    id: UUID
    organization_id: UUID
    resource_id: UUID
    resource_name: Optional[str] = None
    user_id: UUID
    user_email: Optional[str] = None
    user_full_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    purpose: Optional[str] = None
    total_credits: Optional[int] = 0
    rejection_reason: Optional[str] = None


    checkin_time: Optional[datetime] = None
    checkout_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
