import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from fastapi import HTTPException, status
from app.database.models import Lead
from app.schemas.lead import LeadCreate, LeadUpdate
from app.utils.validators import normalize_string, normalize_phone

logger = logging.getLogger("client_finder.lead_service")

class LeadService:
    def create_lead(self, db: Session, user_id: int, lead_in: LeadCreate) -> Lead:
        """
        Creates a new lead after rigorous duplicate check for this user.
        """
        # Check duplicate by provider_id
        if lead_in.provider_id:
            existing = db.query(Lead).filter(
                Lead.user_id == user_id,
                Lead.provider_id == lead_in.provider_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"This business ('{existing.business_name}') is already saved in your leads."
                )

        # Check duplicate by normalized name + phone or normalized name + address
        user_leads = db.query(Lead).filter(Lead.user_id == user_id).all()
        clean_name = normalize_string(lead_in.business_name)
        clean_phone = normalize_phone(lead_in.phone or "")
        clean_address = normalize_string(lead_in.address or "")

        for ex in user_leads:
            ex_name = normalize_string(ex.business_name)
            if ex_name == clean_name:
                # Same name and matching phone
                if clean_phone and normalize_phone(ex.phone or "") == clean_phone:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Lead with name '{ex.business_name}' and matching phone is already saved."
                    )
                # Same name and matching address
                if clean_address and normalize_string(ex.address or "") == clean_address:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Lead with name '{ex.business_name}' and matching address is already saved."
                    )

        lead = Lead(
            user_id=user_id,
            provider_id=lead_in.provider_id,
            business_name=lead_in.business_name,
            category=lead_in.category,
            phone=lead_in.phone,
            website=lead_in.website,
            address=lead_in.address,
            city=lead_in.city,
            latitude=lead_in.latitude,
            longitude=lead_in.longitude,
            rating=lead_in.rating or 0.0,
            review_count=lead_in.review_count or 0,
            source=lead_in.source or "Authorized Business API",
            source_url=lead_in.source_url,
            service=lead_in.service,
            lead_score=lead_in.lead_score or 0,
            opportunity_type=lead_in.opportunity_type,
            opportunity_reason=lead_in.opportunity_reason,
            confidence=lead_in.confidence or "Moderate",
            status=lead_in.status or "New",
            notes=lead_in.notes,
            follow_up_date=lead_in.follow_up_date
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        logger.info(f"Saved new lead ID {lead.id} ('{lead.business_name}') for user {user_id}")
        return lead

    def get_lead(self, db: Session, user_id: int, lead_id: int) -> Lead:
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == user_id).first()
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found."
            )
        return lead

    def list_leads(
        self,
        db: Session,
        user_id: int,
        status_filter: Optional[str] = None,
        service_filter: Optional[str] = None,
        city_filter: Optional[str] = None,
        min_score: Optional[int] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Lead], int]:
        query = db.query(Lead).filter(Lead.user_id == user_id)

        if status_filter and status_filter.lower() != "all":
            if status_filter.lower() in ("follow-up", "follow up"):
                query = query.filter(Lead.status.in_(["Follow-up", "Follow Up"]))
            else:
                query = query.filter(Lead.status == status_filter)

        if service_filter and service_filter.lower() != "all":
            query = query.filter(Lead.service.ilike(f"%{service_filter}%"))

        if city_filter and city_filter.lower() != "all":
            query = query.filter(Lead.city.ilike(f"%{city_filter}%"))

        if min_score is not None:
            query = query.filter(Lead.lead_score >= min_score)

        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Lead.business_name.ilike(term),
                    Lead.category.ilike(term),
                    Lead.phone.ilike(term),
                    Lead.address.ilike(term),
                    Lead.notes.ilike(term)
                )
            )

        total = query.count()
        leads = query.order_by(desc(Lead.created_at)).offset(skip).limit(limit).all()
        return leads, total

    def update_lead(self, db: Session, user_id: int, lead_id: int, lead_update: LeadUpdate) -> Lead:
        lead = self.get_lead(db, user_id, lead_id)
        update_data = lead_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(lead, key, value)

        db.commit()
        db.refresh(lead)
        logger.info(f"Updated lead ID {lead_id} for user {user_id}")
        return lead

    def delete_lead(self, db: Session, user_id: int, lead_id: int) -> bool:
        lead = self.get_lead(db, user_id, lead_id)
        db.delete(lead)
        db.commit()
        logger.info(f"Deleted lead ID {lead_id} for user {user_id}")
        return True

lead_service = LeadService()
