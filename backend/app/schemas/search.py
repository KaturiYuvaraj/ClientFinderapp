from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Union
from datetime import datetime
from app.schemas.lead import NormalizedBusiness

class SearchRequest(BaseModel):
    service: Union[str, List[str]] = "Website Design"
    services: Optional[List[str]] = None
    category: str
    location: str
    radius: str = "20 km"
    keywords: Optional[str] = None

class DiscoveredLeadItem(NormalizedBusiness):
    lead_score: int = 0
    opportunity_type: str = ""
    opportunity_reason: str = ""
    confidence: str = "Moderate"
    verified_facts: List[str] = []
    inferences: List[str] = []
    suggested_approach: Optional[str] = None
    is_saved: bool = False
    saved_lead_id: Optional[int] = None

class SearchResponse(BaseModel):
    query: SearchRequest
    total: int
    results: List[DiscoveredLeadItem]

class SearchHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service: str
    category: str
    location: str
    radius: str
    keywords: Optional[str] = None
    created_at: datetime
