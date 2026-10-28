from pydantic import BaseModel
from typing import Optional, List
from app.schemas.lead import NormalizedBusiness

class AIOpportunityAnalysis(BaseModel):
    service_match: bool = True
    lead_score: int
    opportunity_type: str
    reason: str
    confidence: str  # "Very High", "High", "Moderate", "Low"
    verified_facts: List[str]
    inferences: List[str]
    suggested_approach: Optional[str] = None

class AnalyzeLeadRequest(BaseModel):
    business: NormalizedBusiness
    service: str

class GenerateMessageRequest(BaseModel):
    business_name: str
    category: Optional[str] = None
    location: Optional[str] = None
    service: str
    opportunity_reason: Optional[str] = None
    verified_facts: Optional[List[str]] = []
    sender_name: Optional[str] = None
    lead_id: Optional[int] = None

class GenerateMessageResponse(BaseModel):
    message: str
    lead_id: Optional[int] = None
