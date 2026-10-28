from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User, GeneratedMessage
from app.schemas.ai import (
    AnalyzeLeadRequest, AIOpportunityAnalysis,
    GenerateMessageRequest, GenerateMessageResponse
)
from app.services.ai_service import ai_service
from app.utils.auth import get_current_user
from app.utils.rate_limiter import check_rate_limit

router = APIRouter(prefix="/api/ai", tags=["AI Intelligence"])

@router.post("/analyze-lead", response_model=AIOpportunityAnalysis)
async def analyze_lead(
    req: AnalyzeLeadRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    On-demand AI opportunity analysis for any business listing.
    """
    check_rate_limit(request, user_id=str(current_user.id))
    analysis = await ai_service.analyze_business(req.business, req.service)
    return analysis

@router.post("/generate-message", response_model=GenerateMessageResponse)
async def generate_outreach_message(
    req: GenerateMessageRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a concise, personalized outreach message based on business data and verified facts.
    Records message in database.
    """
    check_rate_limit(request, user_id=str(current_user.id))
    sender_name = req.sender_name or current_user.name
    message_text = await ai_service.generate_message(
        business_name=req.business_name,
        category=req.category,
        location=req.location,
        service=req.service,
        opportunity_reason=req.opportunity_reason,
        verified_facts=req.verified_facts,
        sender_name=sender_name
    )

    # Store generated message
    try:
        msg_record = GeneratedMessage(
            lead_id=req.lead_id,
            user_id=current_user.id,
            message=message_text
        )
        db.add(msg_record)
        db.commit()
    except Exception:
        db.rollback()

    return GenerateMessageResponse(message=message_text, lead_id=req.lead_id)
