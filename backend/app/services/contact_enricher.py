import re
import logging
import asyncio
import unicodedata
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
    # Food, Dining & Delivery Directories (Global & India)
    'tripadvisor.', 'opentable.', 'restaurantguru.', 'deliveroo.', 'just-eat.',
    'ubereats.', 'doordash.', 'grubhub.', 'seamless.', 'postmates.', 'instacart.',
    'timeout.', 'zomato.', 'swiggy.', 'magicpin.', 'eazydiner.', 'dineout.', 'eatsure.',
    'restaurantji.', 'menuism.', 'greatbritishchefs.', 'menupages.', 'sirved.', 'foodhygiene.',
    # Booking, Salon & Appointments Platforms
    'fresha.', 'vagaro.', 'booksy.', 'schedulicity.', 'setmore.', 'styleseat.',
    'mindbodyonline.', 'appointy.', 'zipappointments.', 'treatwell.', 'resy.com',
    'thefork.', 'booker.com', 'acuityscheduling.', 'calendly.', 'business.site',
    # Indian Directories & Portals
    'justdial.', 'sulekha.', 'indiamart.', 'tradeindia.', 'magicbricks.', '99acres.',
    'housing.com', 'nobroker.', 'practo.', 'urbancompany.',
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
    host = domain.lower().strip().split(":")[0]
    for prefix in ("www.", "m.", "mobile."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    if host.endswith(".gov"):
        return True
    for dir_tag in DIRECTORY_DOMAINS:
        if dir_tag == "gov":
            continue
        if dir_tag.endswith("."):
            if host.startswith(dir_tag) or ("." + dir_tag) in host:
                return True
        else:
            if host == dir_tag or host.endswith("." + dir_tag):
                return True
    return False

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

    # Rule 3: Business name relevance matching (normalize accents so Épicerie -> epicerie)
    norm_biz_name = unicodedata.normalize('NFKD', str(business_name or '')).encode('ascii', 'ignore').decode('ascii')
    norm_title = unicodedata.normalize('NFKD', str(snippet_title or '')).encode('ascii', 'ignore').decode('ascii')
    name_clean = re.sub(r'[^a-z0-9\s]', ' ', norm_biz_name.lower())
    words = [w for w in name_clean.split() if len(w) >= 2]

    loc_words = set(re.sub(r'[^a-z0-9\s]', ' ', location.lower()).split()) if location else set()

    # Core brand tokens: filter out stopwords and location words
    core_tokens = [w for w in words if w not in GENERIC_STOPWORDS and w not in loc_words and len(w) >= 3]

    if not core_tokens:
        core_tokens = [w for w in words if len(w) >= 3]

    condensed_name = re.sub(r'[^a-z0-9]', '', norm_biz_name.lower())
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
            if norm_title and (condensed_core in re.sub(r'[^a-z0-9]', '', norm_title.lower()) or norm_biz_name.lower() in norm_title.lower()):
                return True
        return False

    # C) Single core token business (e.g. "Nike" or "Bliss")
    if len(core_tokens) == 1:
        single = core_tokens[0].rstrip('s')
        if domain_clean.startswith(single) or domain_clean == single:
            return True

    return False

PARKED_DOMAIN_MARKERS = (
    "domain is for sale", "buy this domain", "parked free", "sedoparking",
    "hugedomains", "afternic", "dan.com", "godaddy.com/forsale",
    "parkingcrew", "domainnamesales", "this domain may be for sale",
)


def _ascii_str(val: str) -> str:
    return unicodedata.normalize("NFKD", str(val or "")).encode("ascii", "ignore").decode("ascii")


class AutoContactEnricher:
    """
    Automated background contact enricher & digital presence verifier.
    Automatically discovers websites, social media, mobile app links, and phones
    so leads can be hard-filtered accurately without manual user searches.
    """

    @staticmethod
    def _domain_slug_candidates(name: str, city: str) -> List[str]:
        """Builds likely brand domain slugs: full name, without 'the', without legal suffixes, core tokens."""
        clean = _ascii_str(name).lower().replace("&", " and ")
        tokens = [t for t in re.sub(r"[^a-z0-9\s]", " ", clean).split() if t]
        if not tokens:
            return []
        legal = {"inc", "llc", "ltd", "co", "corp", "company", "nyc", "ny"}
        variants = []

        def add(tok_list):
            s = "".join(tok_list)
            if len(s) >= 4 and s not in variants:
                variants.append(s)

        add(tokens)
        no_the = tokens[1:] if tokens[0] == "the" else tokens
        add(no_the)
        no_legal = [t for t in no_the if t not in legal]
        add(no_legal)
        add([t for t in no_legal if t != "and"])
        core = [t for t in no_legal if t not in GENERIC_STOPWORDS and t != "and"]
        if len(core) >= 2:
            add(core)

        domains = []
        for v in variants[:3]:
            domains.append(f"https://www.{v}.com")
            domains.append(f"https://www.{v}.in")
            domains.append(f"https://{v}.com")
            domains.append(f"https://{v}.in")
            domains.append(f"https://www.{v}.co.in")
        return domains[:9]

    async def _probe_brand_domain_async(self, biz: NormalizedBusiness, location: str) -> None:
        """
        Fast async HTTP probe checking if the business owns a brand domain (e.g. www.<brand>.com).
        Catches businesses that have a live website which was not tagged in the map data.
        A candidate site is accepted only if it mentions the business name AND matches
        the business's phone number, ZIP code, street, or city.
        """
        if biz.website:
            return
        clean_name = _ascii_str(biz.name).lower()
        city_clean = _ascii_str((biz.city or location or "").split(",")[0]).strip().lower()
        candidates = self._domain_slug_candidates(biz.name, city_clean)
        if not candidates:
            return

        words = [w for w in re.sub(r"[^a-z0-9\s]", " ", clean_name).split() if len(w) >= 3 and w not in GENERIC_STOPWORDS]
        if not words:
            words = [w for w in re.sub(r"[^a-z0-9\s]", " ", clean_name).split() if len(w) >= 3]

        # Location evidence from the business record
        addr_ascii = _ascii_str(biz.address or "").lower()
        phone_digits = re.sub(r"[^\d]", "", biz.phone or "")
        phone_tail = phone_digits[-7:] if len(phone_digits) >= 7 else ""
        zip_codes = re.findall(r"\b\d{5,6}\b", addr_ascii)
        addr_parts = [p.strip() for p in addr_ascii.split(",") if p.strip()]
        street_tokens = []
        if len(addr_parts) >= 2:
            street_words = [w for w in re.sub(r"[^a-z\s]", " ", addr_parts[1]).split() if len(w) >= 4 and w not in ("street", "avenue", "road", "boulevard")]
            street_tokens = street_words[:2]
        city_tokens = [city_clean] if city_clean else []
        for p in addr_parts[2:4]:
            p_clean = re.sub(r"[^a-z\s]", "", p).strip()
            if len(p_clean) >= 4:
                city_tokens.append(p_clean)

        async def _check(client: httpx.AsyncClient, url: str):
            try:
                resp = await client.get(url)
                if resp.status_code != 200 or len(resp.text) < 600:
                    return None
                final_url = str(resp.url)
                parsed_final = urlparse(final_url)
                if is_directory(parsed_final.netloc):
                    return None
                html_full = _ascii_str(resp.text[:200000]).lower()
                if any(m in html_full[:30000] for m in PARKED_DOMAIN_MARKERS):
                    return None
                if words and not all(w in html_full for w in words[:2]):
                    return None
                html_digits = re.sub(r"[^\d]", "", html_full)
                evidence = (
                    (phone_tail and phone_tail in html_digits)
                    or any(z in html_full for z in zip_codes)
                    or (street_tokens and all(s in html_full for s in street_tokens))
                    or any(c and c in html_full for c in city_tokens)
                )
                if not evidence:
                    return None
                return parsed_final, html_full, resp.text
            except Exception:
                return None

        async with httpx.AsyncClient(timeout=3.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}) as client:
            results = await asyncio.gather(*[_check(client, u) for u in candidates])

        for res in results:
            if not res:
                continue
            parsed_final, html_full, raw_html = res
            biz.website = f"{parsed_final.scheme}://{parsed_final.netloc}"
            if "play.google.com" in html_full or "apps.apple.com" in html_full:
                biz.has_mobile_app = True
            if any(s in html_full for s in ("instagram.com/", "facebook.com/", "tiktok.com/", "googletagmanager.com")):
                biz.has_social_media = True
            if not biz.phone:
                found_ph = extract_phone_from_text(raw_html[:50000])
                if found_ph:
                    biz.phone = found_ph
            biz.digital_footprint = [f"Official Website Found: {biz.website}"]
            return

    def enrich_single_sync(
        self,
        name: str,
        category: str = "",
        location: str = "",
        address: str = "",
        current_phone: str = "",
        current_website: str = ""
    ) -> Tuple[str, str]:
        ph, web, _, _, _ = self.enrich_single_full_sync(
            name=name,
            category=category,
            location=location,
            address=address,
            current_phone=current_phone,
            current_website=current_website,
        )
        return ph, web

    def enrich_single_full_sync(
        self,
        name: str,
        category: str = "",
        location: str = "",
        address: str = "",
        current_phone: str = "",
        current_website: str = ""
    ) -> Tuple[str, str, bool, bool, List[str]]:
        """
        Synchronously enriches a single business contact details & digital presence.
        Returns: (phone, website, has_social_media, has_mobile_app, digital_footprint)
        """
        phone = current_phone.strip() if current_phone else ""
        website = current_website.strip() if current_website else ""
        has_social = False
        has_app = False
        footprint: List[str] = []

        # If current_website is actually a directory or aggregator, invalidate it
        if website:
            parsed_curr = urlparse(website if "://" in website else f"https://{website}")
            if is_directory(parsed_curr.netloc):
                website = ""

        # If we already have both valid phone and verified website, no enrichment needed
        if phone and website:
            footprint.append(f"Official Website: {website}")
            return phone, website, has_social, has_app, footprint

        clean_name = _ascii_str(name)
        city_short = _ascii_str(location.split(",")[0].strip()) if location else ""
        search_terms = [clean_name]
        if city_short:
            search_terms.append(city_short)
        elif address:
            parts = [p.strip() for p in address.split(",") if p.strip() and p.strip().lower() != name.lower().strip()]
            if parts:
                search_terms.append(_ascii_str(parts[0]))

        raw_query = " ".join(search_terms)
        query = re.sub(r'[\'\"\(\)]', '', raw_query).strip()

        if not DDGS:
            return phone, website, has_social, has_app, footprint

        try:
            ddgs = DDGS()
            try:
                results = list(ddgs.text(query, backend="lite", max_results=6))
            except Exception:
                results = list(ddgs.text(query, max_results=6))

            norm_name_tokens = [
                w for w in re.sub(r"[^a-z0-9\s]", " ", clean_name.lower()).split()
                if len(w) >= 3 and w not in GENERIC_STOPWORDS
            ]

            # Step 1: Scan search results for verified official website, social links, and phone
            for r in results:
                href = r.get("href", "")
                title_str = _ascii_str(r.get("title", ""))
                body_str = _ascii_str(r.get("body", ""))
                combined_text = f"{title_str} {body_str}".lower()
                name_mentioned = not norm_name_tokens or any(t in combined_text or t in href.lower() for t in norm_name_tokens)

                if href and href.startswith("http"):
                    href_low = href.lower()
                    if name_mentioned:
                        if any(s in href_low for s in ("instagram.com/", "facebook.com/", "tiktok.com/", "linkedin.com/")):
                            has_social = True
                            if "instagram.com" in href_low and "Instagram Profile Found" not in footprint:
                                footprint.append("Instagram Profile Found")
                            elif "facebook.com" in href_low and "Facebook Page Found" not in footprint:
                                footprint.append("Facebook Page Found")
                        if "apps.apple.com" in href_low or "play.google.com" in href_low:
                            has_app = True
                            if "Mobile App Store Listing Found" not in footprint:
                                footprint.append("Mobile App Store Listing Found")
                        if any(d in href_low for d in ("yelp.com/biz/", "doordash.com/store/", "ubereats.com/store/", "zomato.com/", "tripadvisor.")):
                            if "Directory / Delivery Listing Only" not in footprint:
                                footprint.append("Directory / Delivery Listing Only")

                    # Check if this URL is an authentic official website
                    if not website:
                        if is_official_website(href, clean_name, location or city_short, snippet_title=title_str):
                            parsed = urlparse(href)
                            if parsed.netloc.count('.') <= 2 and not any(p in parsed.netloc for p in ['wixsite', 'squarespace', 'wordpress']):
                                website = f"{parsed.scheme}://{parsed.netloc}"
                            else:
                                website = href
                            footprint.append(f"Official Website: {website}")

                    # Extract phone from URL path if present
                    if not phone and name_mentioned:
                        url_phone = extract_phone_from_text(href)
                        if url_phone:
                            phone = url_phone

                # Check phone in title and snippet body
                if not phone and name_mentioned:
                    found_ph = extract_phone_from_text(f"{title_str} {body_str}")
                    if found_ph:
                        phone = found_ph

            # Step 2: If we now have an official website, scrape homepage for phone/social/app links
            if website:
                try:
                    with httpx.Client(timeout=2.5, follow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'}) as client:
                        resp = client.get(website)
                        if resp.status_code == 200:
                            html = resp.text
                            html_low = html.lower()
                            if "apps.apple.com" in html_low or "play.google.com" in html_low:
                                has_app = True
                            if any(s in html_low for s in ("instagram.com/", "facebook.com/", "tiktok.com/")):
                                has_social = True
                            if not phone:
                                tel_match = re.search(r'href=["\']tel:([^"\'\s?]+)["\']', html)
                                if tel_match:
                                    raw_tel = tel_match.group(1).strip()
                                    if clean_phone_candidate(raw_tel):
                                        phone = raw_tel
                                if not phone:
                                    phone = extract_phone_from_text(html)
                except Exception as scrape_err:
                    logger.debug(f"Direct homepage scrape skipped for '{name}': {scrape_err}")

        except Exception as e:
            logger.debug(f"Enrichment search failed for '{name}': {e}")

        if not website:
            footprint.insert(0, "Web-Verified: 0 Official Websites Found")
        if not has_app:
            footprint.append("Web-Verified: 0 Mobile Apps Found")
        if not has_social:
            footprint.append("Web-Verified: 0 Social Media Campaigns Found")

        return phone, website, has_social, has_app, footprint

    async def enrich_batch(
        self,
        businesses: List[NormalizedBusiness],
        category: str,
        location: str,
        max_enrich: int = 12
    ) -> List[NormalizedBusiness]:
        """
        Enriches a list of businesses concurrently:
        1. Runs fast async direct brand domain probing across ALL candidates missing a website (~1.5s).
        2. Runs DDGS('lite') search verification across top candidates to discover websites, phones, and social footprints.
        """
        needy = [b for b in businesses if not b.phone or not b.website]
        if not needy:
            return businesses

        # Stage 1: Fast parallel brand domain probe across ALL candidates missing a website
        probe_sem = asyncio.Semaphore(20)

        async def _probe_one(biz: NormalizedBusiness):
            if not biz.website:
                async with probe_sem:
                    try:
                        await asyncio.wait_for(self._probe_brand_domain_async(biz, biz.city or location), timeout=4.0)
                    except Exception:
                        pass

        try:
            await asyncio.wait_for(
                asyncio.gather(*[_probe_one(b) for b in needy], return_exceptions=True),
                timeout=9.0,
            )
        except Exception as e:
            logger.debug(f"Brand domain probe batch note: {e}")

        if not DDGS:
            return businesses

        # Stage 2: Deep search engine verification on top candidates that still have no website
        still_needy = [b for b in businesses if not b.website or not b.phone]
        target_items = still_needy[:max_enrich]
        sem = asyncio.Semaphore(3)

        async def _enrich_item(biz: NormalizedBusiness):
            async with sem:
                try:
                    new_phone, new_website, has_soc, has_app, footprint = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.enrich_single_full_sync,
                            name=biz.name,
                            category=biz.category or category,
                            location=biz.city or location,
                            address=biz.address or "",
                            current_phone=biz.phone,
                            current_website=biz.website
                        ),
                        timeout=4.0
                    )
                    if new_phone:
                        biz.phone = new_phone
                    if new_website:
                        biz.website = new_website
                    if has_soc:
                        biz.has_social_media = True
                    if has_app:
                        biz.has_mobile_app = True
                    if footprint:
                        biz.digital_footprint = footprint
                except Exception as err:
                    logger.debug(f"Batch item enrichment error on '{biz.name}': {err}")

        try:
            await asyncio.wait_for(
                asyncio.gather(*[_enrich_item(b) for b in target_items], return_exceptions=True),
                timeout=9.0
            )
            logger.info(f"AutoContactEnricher: Verified digital footprint for {len(target_items)} leads.")
        except asyncio.TimeoutError:
            logger.info("AutoContactEnricher: Batch timeout reached, proceeding with verified contacts.")
        except Exception as e:
            logger.warning(f"AutoContactEnricher batch error: {e}")

        # Ensure remaining no-website leads also have clear digital_footprint tags
        for b in businesses:
            if not b.digital_footprint:
                fp = []
                if not b.website:
                    fp.append("Directory Verified: No Official Website Listed")
                if not b.has_mobile_app:
                    fp.append("No Mobile App Listed")
                if not b.has_social_media:
                    fp.append("No Social Media Listed")
                b.digital_footprint = fp

        return businesses

auto_contact_enricher = AutoContactEnricher()
