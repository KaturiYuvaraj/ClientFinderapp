from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.database.models import User, Lead
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes dashboard analytics: pipeline counts, conversion rate,
    service breakdown, and top opportunity leads.
    """
    user_id = current_user.id
    total_leads = db.query(func.count(Lead.id)).filter(Lead.user_id == user_id).scalar() or 0

    # Counts by status
    status_counts_raw = db.query(
        Lead.status, func.count(Lead.id)
    ).filter(Lead.user_id == user_id).group_by(Lead.status).all()
    status_map = {status: count for status, count in status_counts_raw}

    new_leads = status_map.get("New", 0)
    contacted = status_map.get("Contacted", 0)
    interested = status_map.get("Interested", 0)
    follow_up = status_map.get("Follow-up", 0) + status_map.get("Follow Up", 0)
    converted = status_map.get("Converted", 0)
    not_interested = status_map.get("Not Interested", 0)

    # High opportunity leads (score >= 75)
    high_opportunity_leads = db.query(func.count(Lead.id)).filter(
        Lead.user_id == user_id,
        Lead.lead_score >= 75
    ).scalar() or 0

    # Average score
    avg_score = db.query(func.avg(Lead.lead_score)).filter(Lead.user_id == user_id).scalar()
    avg_score_rounded = round(float(avg_score), 1) if avg_score else 0.0

    # Conversion rate
    conversion_rate = round((converted / total_leads * 100), 1) if total_leads > 0 else 0.0

    # Service distribution
    service_raw = db.query(
        Lead.service, func.count(Lead.id)
    ).filter(Lead.user_id == user_id).group_by(Lead.service).all()
    service_distribution = [{"service": s, "count": c} for s, c in service_raw]

    # Top high opportunity leads
    recent_leads = db.query(Lead).filter(
        Lead.user_id == user_id
    ).order_by(Lead.lead_score.desc(), Lead.created_at.desc()).limit(5).all()

    recent_summary = [
        {
            "id": l.id,
            "business_name": l.business_name,
            "category": l.category,
            "city": l.city,
            "address": l.address,
            "rating": l.rating,
            "review_count": l.review_count,
            "source": l.source,
            "source_url": l.source_url,
            "service": l.service,
            "lead_score": l.lead_score,
            "opportunity_type": l.opportunity_type or l.service,
            "opportunity_reason": l.opportunity_reason,
            "confidence": l.confidence,
            "status": l.status,
            "phone": l.phone,
            "website": l.website,
            "notes": l.notes,
            "follow_up_date": str(l.follow_up_date) if l.follow_up_date else None
        }
        for l in recent_leads
    ]

    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "contacted": contacted,
        "interested": interested,
        "follow_up": follow_up,
        "converted": converted,
        "not_interested": not_interested,
        "high_opportunity_leads": high_opportunity_leads,
        "avg_lead_score": avg_score_rounded,
        "conversion_rate": conversion_rate,
        "status_distribution": [
            {"status": "New", "count": new_leads, "color": "#6366f1"},
            {"status": "Contacted", "count": contacted, "color": "#0ea5e9"},
            {"status": "Interested", "count": interested, "color": "#f59e0b"},
            {"status": "Follow-up", "count": follow_up, "color": "#8b5cf6"},
            {"status": "Converted", "count": converted, "color": "#10b981"},
            {"status": "Not Interested", "count": not_interested, "color": "#64748b"}
        ],
        "service_distribution": service_distribution,
        "recent_high_opportunity": recent_summary
    }
