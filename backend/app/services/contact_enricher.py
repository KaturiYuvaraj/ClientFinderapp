import re
import logging
import asyncio
from typing import List, Tuple, Optional
from urllib.parse import urlparse
import httpx

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

from app.schemas.lead import NormalizedBusiness

logger = logging.getLogger("client_finder.contact_enricher")

# Aggregator, search, social, booking, and directory domains that shouldn't be selected as the business's official website
DIRECTORY_DOMAINS = {
    # Search engines & major portals
    'google.', 'bing.', 'yahoo.', 'duckduckgo.', 'ask.com', 'baidu.', 'yandex.',
    'apple.com', 'wikipedia.', 'wikidata.', 'gov.uk', 'gov',
    # Maps & Navigation
    'maps.apple.', 'mapquest.', 'openstreetmap.', 'waze.', 'tomtom.', 'here.com',
    'popmap.', 'mappcouk.', 'citymapper.',
    # Social Media & Media
    'facebook.', 'instagram.', 'twitter.', 'x.com', 'linkedin.', 'pinterest.',
    'tiktok.', 'youtube.', 'reddit.', 'quora.', 'threads.net', 'snapchat.',
    'tumblr.', 'flickr.', 'vimeo.',
    # Business Directories & Aggregators (US & Global)
    'chamberofcommerce.', 'yelp.', 'yellowpages.', 'whitepages.', 'superpages.',
    'manta.', 'bbb.org', 'citysearch.', 'merchantcircle.', 'angieslist.', 'angi.com',
    'thumbtack.', 'bark.com', 'nextdoor.', 'hotfrog.', 'localdatabase.', 'local.com',
    'dexknows.', 'showmelocal.', 'kompass.', 'usplaces.', 'allbiz.', 'infobel.',
    'cybo.com', 'yalwa.', 'spoke.com', 'botw.org', 'alignable.', 'expertise.com',
    'threebestrated.', 'patch.com', 'eventbrite.', 'meetup.', 'trustpilot.',
    'foursquare.', 'zoominfo.', 'dnb.com', 'bizapedia.', 'opencorporates.',
    'ezlocal.', 'cylex', 'hubbiz.', 'brownbook.', 'yellowbook.', 'kudzu.',
    'judysbook.', 'insiderpages.', 'citysquares.', 'myhuckleberry.',
    # UK & International Directories
    'yell.com', 'scoot.co.uk', 'touchlocal.', 'thomsonlocal.', 'freeindex.co.uk',
    '192.com', 'allinlondon.', 'find-open.', 'firmania.', 'nicelocal.',
    'check-trade.', 'bizseek.', 'hardens.com', 'crazygames.',
    # Food, Dining & Delivery Directories
    'tripadvisor.', 'opentable.', 'restaurantguru.', 'deliveroo.', 'just-eat.',
    'ubereats.', 'doordash.', 'grubhub.', 'seamless.', 'postmates.', 'instacart.',
    'timeout.', 'zomato.', 'restaurantji.', 'menuism.', 'greatbritishchefs.',
    'menupages.', 'sirved.', 'foodhygiene.',
    # Booking, Salon & Appointments Platforms
    'fresha.', 'vagaro.', 'booksy.', 'schedulicity.', 'setmore.', 'styleseat.',
    'mindbodyonline.', 'appointy.', 'zipappointments.', 'treatwell.', 'resy.com',
    'thefork.', 'booker.com', 'acuityscheduling.', 'calendly.',
}

DIRECTORY_PATH_PATTERNS = [
    re.compile(r'/(?:business-directory|directory|categories|category|salon|salons|places|place|biz|listing|listings|review|reviews|post|posts|lvp|city|search)/', re.IGNORECASE),
    re.compile(r'/sites/[^/]+', re.IGNORECASE),
]

GENERIC_STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'to', 'from',
    'inc', 'incorporated', 'llc', 'ltd', 'limited', 'corp', 'corporation', 'co', 'company',
    'est', 'established', 'group', 'services', 'service', 'solutions', 'center', 'centre',
    'shop', 'shops', 'store', 'stores', 'place', 'places', 'bar', 'cafe', 'restaurant',
    'salon', 'salons', 'clinic', 'office', 'agency', 'online', 'official', 'usa', 'uk'
}

# Accurate phone number regexes (UK, North American, International)
PHONE_PATTERNS = [
    # Explicit prefix: Telephone / Phone / Tel / Call / ☎ followed by number
    re.compile(r'(?:Telephone|Phone|Tel|Call|☎|📞)[:\s\-]*(0[1-9]\d{1,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4})', re.IGNORECASE),
    re.compile(r'(?:Telephone|Phone|Tel|Call|☎|📞)[:\s\-]*(\+\d{1,3}[\s.-]?(?:\(?\d{1,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4})', re.IGNORECASE),
    # UK landline & mobile formats: 020 xxxx xxxx, 01xx xxx xxxx, 07xxx xxxxxx
    re.compile(r'\b(020[\s.-]?\d{4}[\s.-]?\d{4})\b'),
    re.compile(r'\b(0[1-9]\d{2,3}[\s.-]?\d{3,4}[\s.-]?\d{3,4})\b'),
    # International +44 20 xxxx xxxx, +1 (xxx) xxx-xxxx, +91 xxxxx xxxxx
    re.compile(r'(\+44[\s.-]?\(?0?\)?[\s.-]?20[\s.-]?\d{4}[\s.-]?\d{4})'),
    re.compile(r'(\+\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4})'),
    # Standard North American: (xxx) xxx-xxxx or xxx-xxx-xxxx
    re.compile(r'(\(\d{3}\)[\s.-]?\d{3}[\s.-]?\d{4})'),
    re.compile(r'\b([2-9]\d{2}[\s.-]\d{3}[\s.-]\d{4})\b'),
]

def clean_phone_candidate(raw: str) -> Optional[str]:
    """Validates that extracted phone candidate has appropriate digit length."""
    if not raw:
        return None
    cleaned = raw.strip()
    digits = re.sub(r'[^\d]', '', cleaned)
    # Most valid phone numbers have 9 to 14 digits
    if 9 <= len(digits) <= 14:
        return cleaned
    return None

def extract_phone_from_text(text: str) -> str:
    """Searches text for verified phone number patterns."""
    if not text:
        return ""
    for pat in PHONE_PATTERNS:
        match = pat.search(text)
        if match:
            candidate = match.group(1) if match.groups() else match.group(0)
            valid = clean_phone_candidate(candidate)
            if valid:
                return valid
    return ""

def is_directory(domain: str) -> bool:
    d = domain.lower()
    return any(dir_tag in d for dir_tag in DIRECTORY_DOMAINS)

def token_matches_domain(token: str, domain_clean: str) -> bool:
    """Matches a word token against domain, tolerating singular/plural and common stems."""
    t = token.lower()
    if t in domain_clean:
        return True
    t_stem = t.rstrip('s')
    if len(t_stem) >= 3 and t_stem in domain_clean:
        return True
    # e.g. 'barbershops' -> 'barber'
    for suffix in ['shops', 'shop', 'services', 'service', 'ies', 'ing']:
        if t.endswith(suffix):
            base = t[:-len(suffix)]
            if len(base) >= 3 and base in domain_clean:
                return True
    return False

ALLOWED_SITE_BUILDERS = {'wixsite', 'squarespace', 'wordpress', 'weebly', 'webflow', 'godaddysites', 'myshopify'}
SECOND_LEVEL_TLDS = {'co', 'com', 'org', 'net', 'gov', 'edu', 'ac'}

def extract_brand_domain(netloc: str) -> str:
    """
    Extracts the actual brand name from domain netloc.
    Distinguishes real registered domains (e.g. blindbarber.com)
    from directory subdomains (e.g. blind-barber.wheree.com).
    """
    clean_netloc = netloc.lower().strip()
    for prefix in ['www.', 'm.', 'mobile.']:
        if clean_netloc.startswith(prefix):
            clean_netloc = clean_netloc[len(prefix):]

    parts = clean_netloc.split('.')
    if len(parts) <= 1:
        return clean_netloc

    # Determine registered domain index based on compound TLDs (.co.uk, .com.au)
    if len(parts) >= 3 and parts[-2] in SECOND_LEVEL_TLDS:
        reg_domain = parts[-3]
        subdomain = parts[0] if len(parts) >= 4 else ""
    else:
        reg_domain = parts[-2]
        subdomain = parts[0] if len(parts) >= 3 else ""

    if reg_domain in ALLOWED_SITE_BUILDERS and subdomain:
        return subdomain

    return reg_domain

def is_official_website(candidate_url: str, business_name: str, location: str = "", snippet_title: str = "") -> bool:
    """
    Rigorously verifies if a URL is actually the business's official website.
    Filters out directories, aggregators, booking sites, social media, and
    verifies that the domain name has strong lexical relevance to the business name.
    """
    if not candidate_url or not candidate_url.startswith(("http://", "https://")):
        return False

    try:
        parsed = urlparse(candidate_url)
    except Exception:
        return False

    netloc = parsed.netloc.lower().strip()
    for prefix in ['www.', 'm.', 'mobile.']:
        if netloc.startswith(prefix):
            netloc = netloc[len(prefix):]

    # Rule 1: Reject known directories / aggregators / social platforms
    if is_directory(netloc):
        return False

    # Rule 2: Reject directory-like path listings
    path = parsed.path.lower()
    for pat in DIRECTORY_PATH_PATTERNS:
        if pat.search(path):
            return False

    # Extract genuine brand domain name
    domain_name = extract_brand_domain(netloc)

    # Rule 3: Business name relevance matching
    name_clean = re.sub(r'[^a-z0-9\s]', ' ', business_name.lower())
    words = [w for w in name_clean.split() if len(w) >= 2]

    loc_words = set(re.sub(r'[^a-z0-9\s]', ' ', location.lower()).split()) if location else set()

    # Core brand tokens: filter out stopwords and location words
    core_tokens = [w for w in words if w not in GENERIC_STOPWORDS and w not in loc_words and len(w) >= 3]

    if not core_tokens:
        core_tokens = [w for w in words if len(w) >= 3]

    condensed_name = re.sub(r'[^a-z0-9]', '', business_name.lower())
    condensed_core = "".join(core_tokens)
    domain_clean = re.sub(r'[^a-z0-9]', '', domain_name)

    # A) Condensed full name or core name is contained in domain
    if condensed_core and (condensed_core in domain_clean or domain_clean == condensed_core):
        return True
    if len(condensed_name) >= 5 and condensed_name in domain_clean:
        return True

    # B) Multi-word businesses: MUST match ALL core tokens (or their stems)
    if len(core_tokens) >= 2:
        all_match = all(token_matches_domain(token, domain_clean) for token in core_tokens)
        if all_match:
            first_core = core_tokens[0].rstrip('s')
            first_word = words[0] if words else ""
            # Must start with first core token or first word (prevents '4cornersbarber' matching 'The Corner Barbershop')
            if domain_clean.startswith(first_core) or (first_word and domain_clean.startswith(first_word)):
                return True
            if snippet_title and (condensed_core in re.sub(r'[^a-z0-9]', '', snippet_title.lower()) or business_name.lower() in snippet_title.lower()):
                return True
        return False

    # C) Single core token business (e.g. "Nike" or "Bliss")
    if len(core_tokens) == 1:
        single = core_tokens[0].rstrip('s')
        if domain_clean.startswith(single) or domain_clean == single:
            return True

    return False

class AutoContactEnricher:
    """
    Automated background contact enricher.
    Automatically fetches missing phone numbers and official websites
    for local businesses so users never have to search Google manually.
    """

    def enrich_single_sync(
        self,
        name: str,
        category: str = "",
        location: str = "",
        address: str = "",
        current_phone: str = "",
        current_website: str = ""
    ) -> Tuple[str, str]:
        """
        Synchronously enriches a single business contact details.
        Designed to be called inside asyncio.to_thread.
        """
        phone = current_phone.strip() if current_phone else ""
        website = current_website.strip() if current_website else ""

        # If current_website is actually a directory or aggregator, invalidate it
        if website:
            parsed_curr = urlparse(website)
            if is_directory(parsed_curr.netloc) or not is_official_website(website, name, location):
                website = ""

        # If we already have both valid phone and verified website, no enrichment needed
        if phone and website:
            return phone, website

        # Build address-aware query for maximum accuracy (avoid duplicating business name)
        clean_addr = ""
        if address:
            parts = [p.strip() for p in address.split(",") if p.strip()]
            if parts and parts[0].lower().strip() == name.lower().strip():
                parts = parts[1:]
            clean_addr = " ".join(parts[:2])

        search_terms = [name]
        if clean_addr:
            search_terms.append(clean_addr)
        if location and location.lower() not in clean_addr.lower():
            search_terms.append(location)
        if category:
            search_terms.append(category)
        search_terms.append("phone")

        raw_query = " ".join(search_terms)
        query = re.sub(r'[\'\"\(\)]', '', raw_query).strip()

        if not DDGS:
            return phone, website

        try:
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=6))

            # Step 1: Scan search results for verified official website and phone in snippets/URLs
            for r in results:
                href = r.get("href", "")
                if href and href.startswith("http"):
                    # Check if this URL is an authentic official website
                    if not website:
                        title_str = r.get("title", "")
                        if is_official_website(href, name, location or clean_addr, snippet_title=title_str):
                            parsed = urlparse(href)
                            # Custom domain: keep scheme + netloc homepage
                            if parsed.netloc.count('.') <= 2 and not any(p in parsed.netloc for p in ['wixsite', 'squarespace', 'wordpress']):
                                website = f"{parsed.scheme}://{parsed.netloc}"
                            else:
                                website = href

                    # Extract phone from URL path if present
                    if not phone:
                        url_phone = extract_phone_from_text(href)
                        if url_phone:
                            phone = url_phone

                # Check phone in title and snippet body
                if not phone:
                    combined_snippet = f"{r.get('title', '')} {r.get('body', '')}"
                    found_ph = extract_phone_from_text(combined_snippet)
                    if found_ph:
                        phone = found_ph

            # Step 2: If we now have an official website, but phone is still missing,
            # quickly scrape the website homepage for tel: links or phone numbers.
            if website and not phone:
                try:
                    with httpx.Client(timeout=2.5, follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'}) as client:
                        resp = client.get(website)
                        if resp.status_code == 200:
                            html = resp.text
                            # Priority 1: <a href="tel:...">
                            tel_match = re.search(r'href=["\']tel:([^"\'\s?]+)["\']', html)
                            if tel_match:
                                raw_tel = tel_match.group(1).strip()
                                valid_tel = clean_phone_candidate(raw_tel)
                                if valid_tel:
                                    phone = raw_tel

                            # Priority 2: regex search on homepage html text
                            if not phone:
                                phone = extract_phone_from_text(html)
                except Exception as scrape_err:
                    logger.debug(f"Direct homepage scrape skipped for '{name}': {scrape_err}")

        except Exception as e:
            logger.debug(f"Enrichment search failed for '{name}': {e}")

        return phone, website

    async def enrich_batch(
        self,
        businesses: List[NormalizedBusiness],
        category: str,
        location: str,
        max_enrich: int = 10
    ) -> List[NormalizedBusiness]:
        """
        Enriches a list of businesses concurrently.
        Modifies missing phone and website fields in place.
        """
        if not DDGS:
            return businesses

        needy = [b for b in businesses if not b.phone or not b.website]
        if not needy:
            return businesses

        target_items = needy[:max_enrich]
        sem = asyncio.Semaphore(5)  # Concurrency limit

        async def _enrich_item(biz: NormalizedBusiness):
            async with sem:
                try:
                    new_phone, new_website = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.enrich_single_sync,
                            name=biz.name,
                            category=biz.category or category,
                            location=biz.city or location,
                            address=biz.address or "",
                            current_phone=biz.phone,
                            current_website=biz.website
                        ),
                        timeout=5.0
                    )
                    if new_phone:
                        biz.phone = new_phone
                    if new_website:
                        biz.website = new_website
                except Exception as err:
                    logger.debug(f"Batch item enrichment error on '{biz.name}': {err}")

        try:
            await asyncio.wait_for(
                asyncio.gather(*[_enrich_item(b) for b in target_items], return_exceptions=True),
                timeout=15.0
            )
            logger.info(f"AutoContactEnricher: Processed {len(target_items)} leads for missing contact details.")
        except asyncio.TimeoutError:
            logger.info("AutoContactEnricher: Batch timeout reached, proceeding with available contacts.")
        except Exception as e:
            logger.warning(f"AutoContactEnricher batch error: {e}")

        return businesses

auto_contact_enricher = AutoContactEnricher()
