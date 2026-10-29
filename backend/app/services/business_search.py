import logging
import asyncio
from typing import List
from sqlalchemy.orm import Session
from app.schemas.search import SearchRequest, SearchResponse, DiscoveredLeadItem
from app.schemas.lead import NormalizedBusiness
from app.services.contact_enricher import auto_contact_enricher
from app.providers.business_provider import get_business_provider
from app.services.ai_service import ai_service
from app.database.models import SearchHistory, Lead
from app.utils.validators import normalize_string, normalize_phone

logger = logging.getLogger("client_finder.search_service")

class BusinessSearchService:
    async def search_and_analyze(
        self,
        query: SearchRequest,
        user_id: int,
        db: Session
    ) -> SearchResponse:
        """
        Executes a business discovery query, records search history,
        runs AI opportunity analysis, and annotates existing saved status.
        """
        # 1. Normalize service string for multi-selection
        service_str = (
            ", ".join(query.service)
            if isinstance(query.service, list)
            else (", ".join(query.services) if query.services else str(query.service))
        )

        # 2. Record search history
        try:
            history = SearchHistory(
                user_id=user_id,
                service=service_str[:255],
                category=query.category,
                location=query.location,
                radius=query.radius,
                keywords=query.keywords
            )
            db.add(history)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to record search history: {e}")
            db.rollback()

        # 3. Get business listings from configured provider
        provider = get_business_provider()
        raw_businesses: List[NormalizedBusiness] = await provider.search(query)

        # 3.1 Automatically enrich missing phone & website directly
        if raw_businesses:
            try:
                raw_businesses = await auto_contact_enricher.enrich_batch(
                    businesses=raw_businesses,
                    category=query.category,
                    location=query.location,
                    max_enrich=12
                )
            except Exception as e:
                logger.warning(f"Contact enrichment batch error: {e}")

        # 4. Retrieve user's existing saved leads for duplicate/saved indicator check
        saved_leads = db.query(Lead).filter(Lead.user_id == user_id).all()
        saved_lookup = {}
        for l in saved_leads:
            if l.provider_id:
                saved_lookup[f"pid_{l.provider_id}"] = l.id
            saved_lookup[f"np_{normalize_string(l.business_name)}_{normalize_phone(l.phone)}"] = l.id
            saved_lookup[f"na_{normalize_string(l.business_name)}_{normalize_string(l.address)}"] = l.id

        # 5. Analyze each business with AI concurrently
        async def analyze_item(biz: NormalizedBusiness) -> DiscoveredLeadItem:
            analysis = await ai_service.analyze_business(biz, service_str)

            has_website = bool(biz.website and len(biz.website.strip()) > 3)
            has_mobile_app = bool(biz.has_mobile_app)
            has_digital_marketing = bool(
                biz.has_social_media or (has_website and (biz.review_count or 0) >= 40)
            )
            missing_services = []
            if not has_website:
                missing_services.append("No Website / Web App")
            if not has_mobile_app:
                missing_services.append("No Mobile App")
            if not has_digital_marketing:
                missing_services.append("No Digital Marketing")

            # Check if saved
            is_saved = False
            saved_id = None
            if biz.provider_id and f"pid_{biz.provider_id}" in saved_lookup:
                is_saved = True
                saved_id = saved_lookup[f"pid_{biz.provider_id}"]
            elif f"np_{normalize_string(biz.name)}_{normalize_phone(biz.phone)}" in saved_lookup:
                is_saved = True
                saved_id = saved_lookup[f"np_{normalize_string(biz.name)}_{normalize_phone(biz.phone)}"]
            elif f"na_{normalize_string(biz.name)}_{normalize_string(biz.address)}" in saved_lookup:
                is_saved = True
                saved_id = saved_lookup[f"na_{normalize_string(biz.name)}_{normalize_string(biz.address)}"]

            return DiscoveredLeadItem(
                name=biz.name,
                category=biz.category or query.category,
                phone=biz.phone,
                website=biz.website,
                address=biz.address,
                city=biz.city or query.location,
                latitude=biz.latitude,
                longitude=biz.longitude,
                rating=biz.rating,
                review_count=biz.review_count,
                source=biz.source,
                source_url=biz.source_url,
                provider_id=biz.provider_id,
                has_social_media=biz.has_social_media,
                has_website=has_website,
                has_mobile_app=has_mobile_app,
                has_digital_marketing=has_digital_marketing,
                missing_services=missing_services,
                digital_footprint=biz.digital_footprint or [],
                lead_score=analysis.lead_score,
                opportunity_type=analysis.opportunity_type,
                opportunity_reason=analysis.reason,
                confidence=analysis.confidence,
                verified_facts=analysis.verified_facts,
                inferences=analysis.inferences,
                suggested_approach=analysis.suggested_approach,
                is_saved=is_saved,
                saved_lead_id=saved_id
            )

        analyzed_items = await asyncio.gather(*[analyze_item(b) for b in raw_businesses])

        # Sort by lead score descending, prioritizing leads missing all 3 (Website/WebApp, Mobile App, Digital Marketing) with a verified phone
        sorted_items = sorted(
            analyzed_items,
            key=lambda x: (
                x.lead_score,
                len(x.missing_services) == 3 and bool(x.phone),
                len(x.missing_services),
            ),
            reverse=True,
        )

        # 6. HARD FILTRATION: Strictly exclude businesses that already have the targeted digital asset(s)
        service_low = service_str.lower()
        wants_website = any(w in service_low for w in ("web", "site", "e-commerce", "landing"))
        wants_app = any(w in service_low for w in ("mobile", "app", "ios", "android"))
        wants_marketing = any(w in service_low for w in ("marketing", "seo", "social", "ads", "content", "email"))

        if wants_website and wants_app and wants_marketing:
            # Strictly return ONLY businesses that have NO website/webapp, NO mobile app, AND NO digital marketing
            sorted_items = [
                x for x in sorted_items
                if not x.has_website and not x.has_mobile_app and not x.has_digital_marketing
            ]
        else:
            if wants_website:
                sorted_items = [x for x in sorted_items if not x.has_website]
            if wants_app:
                sorted_items = [x for x in sorted_items if not x.has_mobile_app]
            if wants_marketing:
                sorted_items = [x for x in sorted_items if not x.has_digital_marketing]

        return SearchResponse(
            query=query,
            total=len(sorted_items),
            results=sorted_items
        )

business_search_service = BusinessSearchService()
