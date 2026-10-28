from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.database.models import User, Lead, SearchHistory
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from app.schemas.search import SearchRequest, SearchResponse, SearchHistoryResponse
from app.services.business_search import business_search_service
from app.services.lead_service import lead_service
from app.services.export_service import export_service
from app.utils.auth import get_current_user
from app.utils.rate_limiter import check_rate_limit


class EnrichPreviewRequest(BaseModel):
    name: str
    category: Optional[str] = "business"
    location: Optional[str] = ""
    address: Optional[str] = ""
    phone: Optional[str] = ""
    website: Optional[str] = ""


class EnrichPreviewResponse(BaseModel):
    phone: str
    website: str
    enriched: bool


router = APIRouter(prefix="/api/leads", tags=["Leads & Search"])

@router.post("/search", response_model=SearchResponse)
async def search_businesses(
    search_req: SearchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search businesses via configured business provider and analyze opportunities with AI.
    Protected by rate limiter.
    """
    check_rate_limit(request, user_id=str(current_user.id))
    results = await business_search_service.search_and_analyze(search_req, current_user.id, db)
    return results

@router.get("/search-history", response_model=List[SearchHistoryResponse])
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns user's previous search queries to repeat previous searches easily.
    """
    history = db.query(SearchHistory).filter(
        SearchHistory.user_id == current_user.id
    ).order_by(SearchHistory.created_at.desc()).limit(limit).all()
    return history

@router.get("/export")
def export_leads_csv(
    status_filter: Optional[str] = Query(None, alias="status"),
    service_filter: Optional[str] = Query(None, alias="service"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exports saved leads to downloadable CSV file.
    """
    leads, _ = lead_service.list_leads(
        db=db,
        user_id=current_user.id,
        status_filter=status_filter,
        service_filter=service_filter,
        limit=10000
    )
    csv_content = export_service.generate_csv(leads)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=client_finder_leads.csv"
        }
    )

@router.get("", response_model=List[LeadResponse])
@router.get("/", response_model=List[LeadResponse], include_in_schema=False)
def list_saved_leads(
    status: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves saved leads with filtering, search, and pagination.
    """
    leads, _ = lead_service.list_leads(
        db=db,
        user_id=current_user.id,
        status_filter=status,
        service_filter=service,
        city_filter=city,
        min_score=min_score,
        search_query=search,
        skip=skip,
        limit=limit
    )
    return leads

@router.get("/{id}", response_model=LeadResponse)
def get_lead_by_id(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch single lead details including AI opportunity analysis.
    """
    return lead_service.get_lead(db, current_user.id, id)

@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def save_lead(
    lead_in: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a business as a new lead. Detects duplicates automatically.
    """
    return lead_service.create_lead(db, current_user.id, lead_in)

@router.put("/{id}", response_model=LeadResponse)
def update_lead(
    id: int,
    lead_update: LeadUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update lead status (New, Contacted, Interested, Follow-up, Converted, Not Interested),
    notes, or follow-up date.
    """
    return lead_service.update_lead(db, current_user.id, id, lead_update)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a saved lead.
    """
    lead_service.delete_lead(db, current_user.id, id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/enrich-preview", response_model=EnrichPreviewResponse)
async def enrich_preview(
    item: EnrichPreviewRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Enriches an unsaved discovered lead preview with phone & website on demand.
    """
    import asyncio
    from app.services.contact_enricher import auto_contact_enricher

    p, w = await asyncio.to_thread(
        auto_contact_enricher.enrich_single_sync,
        name=item.name,
        category=item.category or "business",
        location=item.location or "",
        address=item.address or "",
        current_phone=item.phone or "",
        current_website=item.website or ""
    )
    return EnrichPreviewResponse(
        phone=p,
        website=w,
        enriched=bool((p and p != item.phone) or (w and w != item.website))
    )

@router.post("/{id}/enrich", response_model=LeadResponse)
async def enrich_saved_lead(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enriches a saved lead with automatically discovered phone number and official website.
    """
    import asyncio
    from app.services.contact_enricher import auto_contact_enricher

    lead = db.query(Lead).filter(Lead.id == id, Lead.user_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    new_phone, new_site = await asyncio.to_thread(
        auto_contact_enricher.enrich_single_sync,
        name=lead.business_name,
        category=lead.category or "business",
        location=lead.city or "",
        address=lead.address or "",
        current_phone=lead.phone or "",
        current_website=lead.website or ""
    )
    if new_phone:
        lead.phone = new_phone
    if new_site:
        lead.website = new_site

    db.commit()
    db.refresh(lead)
    return lead_service.get_lead(db, current_user.id, id)

