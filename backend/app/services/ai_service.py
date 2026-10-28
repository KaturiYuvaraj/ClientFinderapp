import logging
import httpx
from typing import List, Optional
from app.schemas.lead import NormalizedBusiness
from app.schemas.ai import AIOpportunityAnalysis
from app.config import settings

logger = logging.getLogger("client_finder.ai")

class AIService:
    def __init__(self):
        self.provider = (settings.AI_PROVIDER or "rule_based").lower()
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL or "gemini-1.5-flash"

    async def analyze_business(self, business: NormalizedBusiness, service: str) -> AIOpportunityAnalysis:
        """
        Analyze a discovered business against the requested service.
        Strictly distinguishes verified facts from AI inferences.
        """
        # If API key is provided and provider is gemini/openai, try LLM API
        if self.api_key and self.provider in ["gemini", "openai"]:
            try:
                if self.provider == "gemini":
                    return await self._analyze_with_gemini(business, service)
                elif self.provider == "openai":
                    return await self._analyze_with_openai(business, service)
            except Exception as e:
                logger.warning(f"LLM API analysis failed ({e}), falling back to deterministic AI evaluator.")

        # Default robust deterministic rule-based analysis
        return self._rule_based_analysis(business, service)

    async def generate_message(
        self,
        business_name: str,
        category: Optional[str],
        location: Optional[str],
        service: str,
        opportunity_reason: Optional[str] = None,
        verified_facts: Optional[List[str]] = None,
        sender_name: Optional[str] = None
    ) -> str:
        """
        Generate a professional, non-spammy personalized outreach message.
        """
        if self.api_key and self.provider in ["gemini", "openai"]:
            try:
                if self.provider == "gemini":
                    return await self._generate_message_gemini(
                        business_name, category, location, service, opportunity_reason, sender_name
                    )
                elif self.provider == "openai":
                    return await self._generate_message_openai(
                        business_name, category, location, service, opportunity_reason, sender_name
                    )
            except Exception as e:
                logger.warning(f"LLM message generation failed ({e}), falling back to template engine.")

        return self._generate_template_message(
            business_name, category, location, service, opportunity_reason, sender_name
        )

    def _rule_based_analysis(self, business: NormalizedBusiness, service: str) -> AIOpportunityAnalysis:
        """
        Analyzes business attributes to assign an objective lead score (0-100),
        reason, verified facts, and actionable inferences.
        """
        service_clean = service.strip().lower()
        has_website = bool(business.website and len(business.website.strip()) > 3)
        has_phone = bool(business.phone and len(business.phone.strip()) > 5)
        has_mobile_app = bool(getattr(business, "has_mobile_app", False))
        has_digital_marketing = bool(
            getattr(business, "has_social_media", False) or (has_website and (business.review_count or 0) >= 40)
        )
        rating = business.rating or 0.0
        review_count = business.review_count or 0
        cat = (business.category or "business").title()

        verified_facts = []
        inferences = []
        score = 50
        opportunity_type = service.title()
        reason = ""
        confidence = "Moderate"
        suggested_approach = ""

        # Gather verified facts on Website/WebApp, Mobile App, Digital Marketing, and Phone
        if has_website:
            verified_facts.append(f"Business has an active website listed: {business.website}")
        else:
            verified_facts.append("Missing Website / Web App: No official website or web app found in public records")

        if not has_mobile_app:
            verified_facts.append("Missing Mobile Application: No dedicated iOS or Android mobile app detected")

        if not has_digital_marketing:
            verified_facts.append("Missing Digital Marketing: No active social media funnel or SEO presence linked")
        else:
            verified_facts.append("Social media or digital marketing footprint detected")

        if has_phone:
            verified_facts.append(f"Public contact number available ({business.phone})")
        else:
            verified_facts.append("No public phone number listed")

        if review_count > 0:
            verified_facts.append(f"Customer feedback present: {rating} stars across {review_count} reviews")
        else:
            verified_facts.append("No public customer reviews recorded")

        verified_facts.append(f"Categorized as {cat} in {business.city or 'target area'}")

        # Boost score to 95 when business has a verified phone and lacks all 3: Website/WebApp, Mobile App, and Digital Marketing
        missing_all_three = (not has_website) and (not has_mobile_app) and (not has_digital_marketing)

        # Opportunity Logic per service
        if any(w in service_clean for w in ["web", "site", "landing", "software"]):
            opportunity_type = "Website Development & Modernization"
            if not has_website:
                if has_phone and (review_count > 50 or rating >= 4.0):
                    score = 94
                    confidence = "Very High"
                    reason = "Popular establishment with active customer demand and verified phone number, but completely missing an official website."
                    inferences.append("High footfall and review volume indicate strong business viability and ability to invest in a web presence.")
                    inferences.append("Losing potential online orders, reservations, and direct search traffic to competitors with websites.")
                    suggested_approach = "Present a clean mobile-friendly restaurant/business demo showcasing online menu, opening hours, and direct booking/inquiry."
                elif has_phone:
                    score = 90
                    confidence = "High"
                    reason = "Genuine local business with a verified phone number, but no official website exists in public records."
                    inferences.append("Customers searching via mobile web cannot view service catalog or operating details.")
                    suggested_approach = "Call or WhatsApp directly with an easy-to-manage modern starter website proposal."
                else:
                    score = 54
                    confidence = "Moderate"
                    reason = "No website found, though public phone contact details are not listed."
                    inferences.append("May need verification of primary decision maker contact channel.")
                    suggested_approach = "Visit business address directly or connect via local social directories."
            else:
                # Business has a website
                if "http://" in business.website:
                    score = 72 if has_phone else 55
                    confidence = "High" if has_phone else "Moderate"
                    reason = "Website detected, but uses unencrypted HTTP protocol."
                    inferences.append("Outdated website that would benefit from HTTPS security and a modern responsive redesign.")
                    suggested_approach = "Offer a complimentary website audit highlighting security, speed, and mobile responsiveness."
                else:
                    score = 62 if has_phone else 35
                    confidence = "Moderate" if has_phone else "Low"
                    reason = "Business operates an active website and has verified phone contact for expansion services." if has_phone else "Business already operates an active website."
                    inferences.append("Opportunity focused on website redesign, custom mobile app, SEO optimization, or conversion upgrades.")
                    suggested_approach = "Pitch performance audits, conversion rate optimization, or companion mobile application add-ons."

        elif any(w in service_clean for w in ["app", "mobile", "ios", "android", "application"]):
            opportunity_type = "Mobile Application Development"
            if review_count > 30 or rating >= 4.0:
                score = 91
                confidence = "High"
                reason = f"High-traction {cat} with engaged local customer base prime for a custom mobile app for direct ordering, bookings, and customer loyalty."
                inferences.append("Repeat customers and high footfall mean a dedicated mobile app can drive repeat orders and appointments without marketplace commissions.")
                inferences.append("Push notifications on mobile offer 4x higher retention and repeat engagement compared to email or web.")
                suggested_approach = "Pitch a branded iOS & Android mobile application with automated appointments/ordering, push notifications, and a digital loyalty card."
            elif has_website:
                score = 82
                confidence = "High"
                reason = f"Established {cat} with an existing website that is ready to expand with a native mobile application."
                inferences.append("Existing online customers can be converted into high-LTV mobile app users with seamless mobile access.")
                suggested_approach = "Offer a companion mobile application that syncs with their current catalog/website."
            else:
                score = 75
                confidence = "Moderate"
                reason = f"Local {cat} that can gain a competitive edge in {business.city or 'their area'} with a modern mobile app."
                inferences.append("Most local competitors only use social media; a dedicated app builds credibility and convenience.")
                suggested_approach = "Showcase a simple, modern mobile app starter designed specifically for their business category."

        elif any(w in service_clean for w in ["logo", "brand", "identity", "design"]):
            opportunity_type = "Branding & Visual Identity"
            if not has_website or review_count < 100:
                score = 85
                confidence = "High"
                reason = f"Growing {cat} business lacking cohesive digital branding or dedicated brand website."
                inferences.append("A refreshed visual identity and professional brand assets can elevate market positioning and attract premium clients.")
                suggested_approach = "Share a 3-concept moodboard or branding portfolio tailored to their specific industry."
            else:
                score = 55
                confidence = "Moderate"
                reason = "Established presence, but may benefit from brand refresh or promotional collateral."
                inferences.append("Could need social media templates, uniform collateral, or packaging design.")
                suggested_approach = "Focus on collateral expansion: menus, signage, and social media branding kits."

        elif any(w in service_clean for w in ["video", "reels", "media", "tiktok", "youtube"]):
            opportunity_type = "Video Editing & Content Creation"
            if review_count > 80:
                score = 89
                confidence = "High"
                reason = f"High-traction {cat} with engaged local customer base, prime for short-form video marketing."
                inferences.append("Visually appealing items/services could drive significant engagement on Instagram Reels and YouTube Shorts.")
                suggested_approach = "Pitch a monthly package of 8-12 edited short-form videos highlighting dishes, customer experiences, or behind-the-scenes."
            else:
                score = 60
                confidence = "Moderate"
                reason = "Growing business that can utilize video marketing to drive local awareness."
                inferences.append("Video content can help stand out from local competitors.")
                suggested_approach = "Offer a single test video or promotional reel to demonstrate ROI."

        elif any(w in service_clean for w in ["seo", "ranking", "search engine"]):
            opportunity_type = "Local SEO & Search Optimization"
            score = 88 if not has_website else 78
            confidence = "High"
            reason = f"High-intent local searches for {cat} can drive steady client acquisition with localized Google optimization."
            inferences.append("Competitors with optimized local listings dominate 'near me' organic search rankings.")
            suggested_approach = "Offer a local keyword audit and Google Business Profile optimization package."

        elif any(w in service_clean for w in ["social", "instagram", "facebook"]):
            opportunity_type = "Social Media Marketing & Management"
            score = 85 if review_count > 20 else 72
            confidence = "High"
            reason = f"Visual {cat} category benefits significantly from active social presence and regular community engagement."
            inferences.append("Target audience actively explores local recommendations on Instagram and TikTok.")
            suggested_approach = "Pitch a monthly social growth retainer including content calendar, reels, and community interaction."

        elif any(w in service_clean for w in ["ads", "ppc", "google ads"]):
            opportunity_type = "Performance Advertising (Google & Meta Ads)"
            score = 89 if has_phone else 75
            confidence = "High"
            reason = f"Direct local lead generation for {cat} with measurable ROI through localized search and map ads."
            inferences.append("High immediate customer intent can be converted directly into incoming phone calls and bookings.")
            suggested_approach = "Propose a pilot ad campaign with guaranteed lead tracking and phone call reporting."

        elif any(w in service_clean for w in ["whatsapp", "bot", "chat"]):
            opportunity_type = "WhatsApp Business Automation & CRM"
            score = 86 if has_phone else 70
            confidence = "High"
            reason = f"Instant messaging for {cat} automates appointment bookings, FAQs, and repeat customer retention."
            inferences.append("Over 70% of modern customers prefer instant messaging over phone calls for pricing and inquiries.")
            suggested_approach = "Demo a customized 24/7 WhatsApp auto-reply and booking flow for their services."

        else:
            # Generic or Multi-Service Bundle
            is_bundle = "," in service
            score = 86 if (not has_website and is_bundle) else (78 if is_bundle else (75 if not has_website else 50))
            opportunity_type = f"Digital Growth Package ({service})" if is_bundle else f"{service.title()} Consulting"
            reason = f"Identified {cat} with active local presence in {business.city or 'the region'}."
            if is_bundle:
                inferences.append(f"Multi-service synergy: Combining {service} delivers faster customer acquisition and higher retention.")
            inferences.append(f"Business could leverage professional {service} to expand operations and market share.")
            suggested_approach = "Present a comprehensive multi-service proposal addressing web presence, customer acquisition, and retention."

        if missing_all_three and has_phone:
            score = max(score, 95)
            confidence = "Very High"
            reason = (
                f"High-priority {cat} lead with a verified phone number ({business.phone}) that currently has "
                "NO Website/Web App, NO Mobile Application, and NO Digital Marketing presence."
            )

        return AIOpportunityAnalysis(
            service_match=True,
            lead_score=score,
            opportunity_type=opportunity_type,
            reason=reason,
            confidence=confidence,
            verified_facts=verified_facts,
            inferences=inferences,
            suggested_approach=suggested_approach
        )

    def _generate_template_message(
        self,
        business_name: str,
        category: Optional[str],
        location: Optional[str],
        service: str,
        opportunity_reason: Optional[str] = None,
        sender_name: Optional[str] = None
    ) -> str:
        loc = location or "your area"
        cat = category or "business"
        sender = sender_name or "A local service partner"

        if "web" in service.lower():
            return (
                f"Hi {business_name},\n\n"
                f"I came across your business while researching popular {cat.lower()}s in {loc}. "
                f"I noticed that your business has great customer ratings, but you don't currently have an official website listed.\n\n"
                f"I specialize in building clean, modern, and mobile-friendly websites for {cat.lower()}s that make it effortless "
                f"for customers to browse your menu/services, find your hours, and contact you directly.\n\n"
                f"I've put together a quick preview of how a modern website could look for {business_name}. "
                f"Would you be open to a brief 5-minute chat this week to take a look?\n\n"
                f"Best regards,\n{sender}"
            )
        elif "app" in service.lower() or "mobile" in service.lower():
            return (
                f"Hi {business_name},\n\n"
                f"I came across your business while researching popular {cat.lower()}s in {loc}. "
                f"I noticed your strong customer feedback and active local presence!\n\n"
                f"I specialize in building custom, high-speed mobile applications (iOS & Android) for {cat.lower()}s that make it effortless "
                f"for customers to browse your services, book appointments or place orders directly, and receive VIP updates right on their phones—saving you from heavy marketplace commissions.\n\n"
                f"I've put together a quick preview of how a dedicated mobile app could work for {business_name}. "
                f"Would you be open to a brief 5-minute chat this week to take a look?\n\n"
                f"Best regards,\n{sender}"
            )
        elif "brand" in service.lower() or "logo" in service.lower():
            return (
                f"Hi {business_name},\n\n"
                f"I hope you're having a productive week! I was reviewing standout {cat.lower()}s in {loc} and was impressed by your reviews.\n\n"
                f"I help local businesses modernize their branding and visual identity—from logos and social media banners to print menus and storefront assets.\n\n"
                f"Would you be open to seeing a couple of tailored branding ideas for {business_name}?\n\n"
                f"Warm regards,\n{sender}"
            )
        elif "video" in service.lower():
            return (
                f"Hi {business_name},\n\n"
                f"I love the positive customer reception {business_name} has built in {loc}! "
                f"With so many customers searching for recommendations on Instagram and YouTube, short-form video has become one of the fastest ways for {cat.lower()}s to attract new customers.\n\n"
                f"I produce high-engagement reels and promotional videos tailored for businesses in your sector. "
                f"Could I share a 1-minute concept tailored specifically for {business_name}?\n\n"
                f"Best,\n{sender}"
            )
        else:
            return (
                f"Hi {business_name},\n\n"
                f"I came across your business while researching top {cat.lower()}s in {loc}. "
                f"I help businesses in your space solve key challenges through professional {service.lower()}.\n\n"
                f"{opportunity_reason or 'I noticed an opportunity to expand your digital reach.'}\n\n"
                f"Would you be open to a brief conversation to explore how this could help {business_name} attract more clients?\n\n"
                f"Best regards,\n{sender}"
            )

    async def _analyze_with_gemini(self, business: NormalizedBusiness, service: str) -> AIOpportunityAnalysis:
        # Fallback to rule-based if anything fails
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = f"""
        Analyze this business for potential {service} opportunity.
        Business Data:
        Name: {business.name}
        Category: {business.category}
        Phone: {business.phone}
        Website: {business.website}
        Address: {business.address}, {business.city}
        Rating: {business.rating} ({business.review_count} reviews)

        You MUST distinguish verified facts from inferences. Do NOT invent facts.
        Return ONLY valid JSON with keys:
        - service_match (boolean)
        - lead_score (integer 0-100)
        - opportunity_type (string)
        - reason (string)
        - confidence ("Very High", "High", "Moderate", "Low")
        - verified_facts (array of strings)
        - inferences (array of strings)
        - suggested_approach (string)
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            if resp.status_code == 200:
                import json
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = text.strip().replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_json)
                return AIOpportunityAnalysis(**parsed)
            else:
                return self._rule_based_analysis(business, service)

    async def _analyze_with_openai(self, business: NormalizedBusiness, service: str) -> AIOpportunityAnalysis:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        prompt = f"""
        Analyze this business for potential {service} opportunity.
        Business Data:
        Name: {business.name}
        Category: {business.category}
        Phone: {business.phone}
        Website: {business.website}
        Address: {business.address}, {business.city}
        Rating: {business.rating} ({business.review_count} reviews)

        Return strictly valid JSON with keys:
        service_match, lead_score (0-100), opportunity_type, reason, confidence, verified_facts, inferences, suggested_approach.
        """
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                import json
                text = resp.json()["choices"][0]["message"]["content"]
                parsed = json.loads(text)
                return AIOpportunityAnalysis(**parsed)
            else:
                return self._rule_based_analysis(business, service)

    async def _generate_message_gemini(self, business_name, category, location, service, reason, sender) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        prompt = f"""
        Write a short, personalized, professional outreach message for:
        Business Name: {business_name}
        Category: {category}
        Location: {location}
        Service Offered: {service}
        Opportunity Context: {reason}
        Sender Name: {sender or 'A local service provider'}

        Keep it under 120 words. Friendly, not spammy, polite call to action.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            return self._generate_template_message(business_name, category, location, service, reason, sender)

    async def _generate_message_openai(self, business_name, category, location, service, reason, sender) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        prompt = f"""
        Write a short, personalized, professional outreach message for:
        Business Name: {business_name}
        Category: {category}
        Location: {location}
        Service Offered: {service}
        Opportunity Context: {reason}
        Sender Name: {sender or 'A local service provider'}

        Keep it under 120 words. Friendly, not spammy, polite call to action.
        """
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            return self._generate_template_message(business_name, category, location, service, reason, sender)

ai_service = AIService()
