from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Union, List
from datetime import datetime, date

class NormalizedBusiness(BaseModel):
    name: str
    category: Optional[str] = ""
    phone: Optional[str] = ""
    website: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0
    rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    source: Optional[str] = "Authorized Business API"
    source_url: Optional[str] = ""
    provider_id: Optional[str] = None
    has_social_media: Optional[bool] = False
    has_mobile_app: Optional[bool] = False
    digital_footprint: List[str] = []

    @field_validator(
        "name", "category", "phone", "website", "address",
        "city", "source", "source_url", "provider_id",
        mode="before"
    )
    @classmethod
    def coerce_str(cls, v):
        if v is None:
            return ""
        return str(v)

class LeadCreate(BaseModel):
    provider_id: Optional[str] = None
    business_name: str
    category: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    source: Optional[str] = "Authorized Business API"
    source_url: Optional[str] = None
    service: str
    lead_score: Optional[int] = 0
    opportunity_type: Optional[str] = None
    opportunity_reason: Optional[str] = None
    confidence: Optional[str] = "Moderate"
    status: Optional[str] = "New"
    notes: Optional[str] = None
    follow_up_date: Optional[Union[date, str]] = None

    @field_validator("follow_up_date", mode="before")
    @classmethod
    def parse_follow_up_date(cls, v):
        if v == "" or v is None:
            return None
        return v

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[Union[date, str]] = None
    opportunity_reason: Optional[str] = None
    lead_score: Optional[int] = None

    @field_validator("follow_up_date", mode="before")
    @classmethod
    def parse_follow_up_date(cls, v):
        if v == "" or v is None:
            return None
        return v

class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    provider_id: Optional[str] = None
    business_name: str
    category: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = 0.0
    review_count: Optional[int] = 0
    source: Optional[str] = None
    source_url: Optional[str] = None
    service: str
    lead_score: int
    opportunity_type: Optional[str] = None
    opportunity_reason: Optional[str] = None
    confidence: Optional[str] = None
    status: str
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
