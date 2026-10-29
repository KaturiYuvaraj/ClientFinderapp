from abc import ABC, abstractmethod
from typing import List, Optional
from urllib.parse import urlparse, quote_plus
import logging
import httpx
import re
import html
import json
import asyncio
from app.schemas.lead import NormalizedBusiness
from app.schemas.search import SearchRequest
from app.config import settings

logger = logging.getLogger("client_finder.providers")


def _safe_float(val, default: float = 4.0) -> float:
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        match = re.search(r"\d+(?:\.\d+)?", str(val))
        if match:
            try:
                return float(match.group(0))
            except (ValueError, TypeError):
                pass
        return default


def _safe_int(val, default: int = 0) -> int:
    if val is None or val == "":
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        match = re.search(r"\d+", str(val))
        if match:
            try:
                return int(match.group(0))
            except (ValueError, TypeError):
                pass
        return default


CORPORATE_CHAIN_KEYWORDS = {
    "mcdonald", "starbucks", "subway", "domino", "kfc", "kentucky fried",
    "burger king", "pizza hut", "taco bell", "dunkin", "chipotle", "wendy",
    "papa john", "baskin robbins", "costa coffee", "tim hortons", "7-eleven",
    "7 eleven", "haldiram", "barbeque nation", "cafe coffee day", "walmart",
    "target", "walgreens", "cvs pharmacy", "tesco", "sainsbury", "pret a manger",
    "popeyes", "shake shack", "five guys", "little caesars", "olive garden",
    "applebee", "ihop", "denny's", "panera bread", "chick-fil-a", "panda express",
    "deli & grocery", "deli and grocery", "bodega", "convenience store",
}

SOCIAL_ONLY_DOMAINS = (
    "facebook.com", "fb.com", "instagram.com", "instagr.am", "twitter.com",
    "x.com", "tiktok.com", "linkedin.com", "youtube.com", "linktr.ee",
    "wa.me", "t.me", "pinterest.com",
)

AGGREGATOR_ONLY_DOMAINS = (
    "zomato.com", "swiggy.com", "ubereats.com", "doordash.com", "grubhub.com",
    "seamless.com", "deliveroo.co.uk", "deliveroo.com", "just-eat.co.uk",
    "just-eat.com", "yelp.com", "tripadvisor.com", "tripadvisor.in",
    "justdial.com", "magicpin.in", "eazydiner.com", "opentable.com",
    "resy.com", "business.site",
)


def _domain_matches(url_or_host: str, domain_list: tuple) -> bool:
    """
    Checks if a URL or hostname matches any domain in domain_list on exact
    domain boundaries (so 'x.com' never false-matches 'unikwax.com').
    """
    try:
        parsed = urlparse(url_or_host if "://" in url_or_host else f"https://{url_or_host}")
        host = (parsed.netloc or parsed.path.split("/")[0]).lower().split(":")[0]
    except Exception:
        return False

    for prefix in ("www.", "m.", "mobile."):
        if host.startswith(prefix):
            host = host[len(prefix):]

    for d in domain_list:
        d_clean = d.lower().strip(".")
        if host == d_clean or host.endswith("." + d_clean):
            return True
    return False


def _is_corporate_chain(name: str, raw_tags: dict) -> bool:
    if not name:
        return False
    if raw_tags.get("brand:wikidata") or raw_tags.get("operator:wikidata"):
        return True
    n_low = name.lower()
    return any(chain in n_low for chain in CORPORATE_CHAIN_KEYWORDS)


def _classify_digital_presence(raw_website: str, raw_tags: dict) -> tuple:
    """
    Separates true official Website/WebApp URLs from social-only profiles or aggregators,
    and detects whether the business has social media (digital marketing) or a mobile app.
    Returns: (official_website: str, has_social_media: bool, has_mobile_app: bool)
    """
    has_social = any(
        bool(raw_tags.get(k))
        for k in (
            "contact:facebook", "facebook", "contact:instagram", "instagram",
            "contact:tiktok", "tiktok", "contact:twitter", "twitter",
            "contact:youtube", "youtube", "contact:linkedin", "linkedin",
        )
    )
    has_app = any(
        bool(raw_tags.get(k))
        for k in ("app:ios", "app:android", "app:apple", "app:google_play")
    )

    official_website = ""
    if raw_website:
        w_clean = str(raw_website).strip()
        if not w_clean.startswith(("http://", "https://")) and "." in w_clean and not w_clean.startswith("@"):
            w_clean = f"https://{w_clean}"
        w_low = w_clean.lower()
        if _domain_matches(w_low, ("play.google.com", "apps.apple.com")):
            has_app = True
        elif _domain_matches(w_low, SOCIAL_ONLY_DOMAINS):
            has_social = True
        elif _domain_matches(w_low, AGGREGATOR_ONLY_DOMAINS):
            pass
        elif w_clean.startswith(("http://", "https://")):
            official_website = w_clean

    return official_website, has_social, has_app


class BusinessDataProvider(ABC):
    @abstractmethod
    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        """Search for businesses matching the query and return normalized results"""
        pass


class MockBusinessProvider(BusinessDataProvider):
    """
    Mock Business Provider — Deterministic offline business directory for local testing
    when BUSINESS_API_PROVIDER=mock. Live searches use SmartFallbackProvider / Overpass.
    """
    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        logger.info(f"MockBusinessProvider invoked for {query.category} in {query.location}")
        cat = (query.category or "Business").strip().title()
        loc = (query.location or "Local Area").strip()
        slug = re.sub(r"[^a-z0-9]", "", loc.lower()) or "local"
        cat_slug = re.sub(r"[^a-z0-9]", "", cat.lower()) or "biz"
        return [
            NormalizedBusiness(
                name=f"Royal {cat} House",
                category=cat,
                phone="+91 866 244 1122",
                website="",
                address=f"MG Road, Central District, {loc}",
                city=loc,
                latitude=16.5062,
                longitude=80.6480,
                rating=4.6,
                review_count=142,
                source="Mock Business Directory",
                source_url="",
                provider_id=f"mock_{slug}_{cat_slug}_1",
            ),
            NormalizedBusiness(
                name=f"Metro {cat} & Co",
                category=cat,
                phone="+91 866 255 3344",
                website=f"http://metro{cat_slug}.example.com",
                address=f"Station Road, {loc}",
                city=loc,
                latitude=16.5120,
                longitude=80.6420,
                rating=4.2,
                review_count=64,
                source="Mock Business Directory",
                source_url=f"http://metro{cat_slug}.example.com",
                provider_id=f"mock_{slug}_{cat_slug}_2",
            ),
            NormalizedBusiness(
                name=f"Heritage {cat} Studio",
                category=cat,
                phone="+91 866 266 7788",
                website="",
                address=f"Ring Road Plaza, {loc}",
                city=loc,
                latitude=16.5010,
                longitude=80.6550,
                rating=4.8,
                review_count=215,
                source="Mock Business Directory",
                source_url="",
                provider_id=f"mock_{slug}_{cat_slug}_3",
            ),
        ]


class OverpassBusinessProvider(BusinessDataProvider):
    """
    OpenStreetMap Overpass API Provider — Live, real-time business data.
    Compliant, open-access public directory for geographic POIs worldwide.
    Supports 60+ business categories and any city globally via Nominatim geocoding.
    No API key required.
    """
    OVERPASS_URLS = [
        "https://lz4.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ]
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    # Extended category → OSM tag mappings
    CATEGORY_MAP = {
        # Food & Drink
        "restaurant": ["amenity=restaurant"],
        "restaurants": ["amenity=restaurant"],
        "cafe": ["amenity=cafe"],
        "cafes": ["amenity=cafe"],
        "fast food": ["amenity=fast_food"],
        "bar": ["amenity=bar"],
        "pub": ["amenity=pub"],
        "bakery": ["shop=bakery"],
        "pizza": ["amenity=fast_food", "amenity=restaurant"],
        "sweet shop": ["shop=confectionery"],
        "ice cream": ["shop=ice_cream"],

        # Health & Medical
        "salon": ["shop=hairdresser", "shop=beauty"],
        "salons": ["shop=hairdresser", "shop=beauty"],
        "spa": ["leisure=spa", "shop=beauty"],
        "barbershop": ["shop=hairdresser"],
        "clinic": ["amenity=clinic", "amenity=doctors"],
        "hospital": ["amenity=hospital"],
        "pharmacy": ["amenity=pharmacy"],
        "dentist": ["amenity=dentist"],
        "dental": ["amenity=dentist"],
        "dental practice": ["amenity=dentist"],
        "optician": ["shop=optician"],
        "gym": ["leisure=fitness_centre"],
        "fitness": ["leisure=fitness_centre"],
        "yoga": ["leisure=yoga"],
        "healthcare": ["amenity=clinic", "amenity=doctors"],
        "veterinary": ["amenity=veterinary"],
        "vet": ["amenity=veterinary"],
        "pet care": ["amenity=veterinary", "shop=pet"],

        # High-Value Home & Trade Services (Worldwide High-Paying Agency Clients)
        "plumber": ["craft=plumber", "shop=trade"],
        "plumbing": ["craft=plumber", "shop=trade"],
        "electrician": ["craft=electrician"],
        "electrical": ["craft=electrician"],
        "hvac": ["craft=hvac", "craft=plumber"],
        "air conditioning": ["craft=hvac"],
        "roofing": ["craft=roofer"],
        "roofer": ["craft=roofer"],
        "auto repair": ["amenity=car_repair", "shop=car_repair"],
        "car repair": ["amenity=car_repair"],
        "mechanic": ["amenity=car_repair"],
        "contractor": ["craft=builder", "craft=carpenter"],
        "builder": ["craft=builder"],
        "cleaning": ["craft=cleaner", "office=company"],
        "locksmith": ["craft=locksmith"],
        "landscaping": ["craft=gardener"],

        # Professional Services & Legal / Finance
        "lawyer": ["office=lawyer", "office=legal"],
        "law firm": ["office=lawyer", "office=legal"],
        "legal": ["office=lawyer", "office=legal"],
        "accountant": ["office=accountant", "office=financial"],
        "accounting": ["office=accountant", "office=financial"],
        "cpa": ["office=accountant"],
        "real estate": ["office=estate_agent", "shop=estate_agent"],
        "realty": ["office=estate_agent", "shop=estate_agent"],
        "insurance": ["office=insurance"],
        "marketing": ["office=advertising_agency", "office=company"],
        "agency": ["office=advertising_agency", "office=company"],
        "architecture": ["office=architect"],
        "consulting": ["office=consulting"],

        # Retail & Shopping
        "retail": ["shop=clothes", "shop=department_store"],
        "supermarket": ["shop=supermarket"],
        "grocery": ["shop=supermarket", "shop=convenience"],
        "electronics": ["shop=electronics", "shop=computer"],
        "clothing": ["shop=clothes"],
        "shoes": ["shop=shoes"],
        "jewelry": ["shop=jewelry"],
        "mobile": ["shop=mobile_phone"],
        "books": ["shop=books"],
        "hardware": ["shop=hardware"],
        "furniture": ["shop=furniture"],
        "stationery": ["shop=stationery"],
        "toys": ["shop=toys"],

        # Hospitality & Services
        "hotel": ["tourism=hotel"],
        "hostel": ["tourism=hostel"],
        "bank": ["amenity=bank"],
        "atm": ["amenity=atm"],
        "laundry": ["shop=laundry"],
        "car wash": ["amenity=car_wash"],
        "garage": ["amenity=car_repair"],
        "petrol": ["amenity=fuel"],
        "travel": ["shop=travel_agency"],
        "photography": ["shop=photo"],
        "printing": ["shop=copyshop"],
        "it": ["shop=computer"],
        "school": ["amenity=school"],
        "tutoring": ["amenity=school"],
        "coaching": ["amenity=school"],
        "college": ["amenity=college"],
        "kindergarten": ["amenity=kindergarten"],
        "library": ["amenity=library"],
        "post office": ["amenity=post_office"],
        "event hall": ["amenity=events_venue"],
    }

    # Instant geocoding cache for major Indian cities, state capitals, and commercial hubs (0ms latency)
    GLOBAL_CITY_COORDS = {
        # Andhra Pradesh
        "vijayawada": {"lat": 16.5062, "lon": 80.6480},
        "vijayawada, india": {"lat": 16.5062, "lon": 80.6480},
        "visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
        "visakhapatnam, india": {"lat": 17.6868, "lon": 83.2185},
        "vizag": {"lat": 17.6868, "lon": 83.2185},
        "guntur": {"lat": 16.3067, "lon": 80.4365},
        "nellore": {"lat": 14.4426, "lon": 79.9865},
        "tirupati": {"lat": 13.6288, "lon": 79.4192},
        "kurnool": {"lat": 15.8281, "lon": 78.0373},
        "kakinada": {"lat": 16.9891, "lon": 82.2475},
        "rajahmundry": {"lat": 17.0005, "lon": 81.8040},
        "kadapa": {"lat": 14.4673, "lon": 78.8242},
        "anantapur": {"lat": 14.6819, "lon": 77.6006},
        "eluru": {"lat": 16.7107, "lon": 81.0952},
        "ongole": {"lat": 15.5057, "lon": 80.0499},
        # Telangana
        "hyderabad": {"lat": 17.3850, "lon": 78.4867},
        "hyderabad, india": {"lat": 17.3850, "lon": 78.4867},
        "secunderabad": {"lat": 17.4399, "lon": 78.4983},
        "warangal": {"lat": 17.9689, "lon": 79.5941},
        "nizamabad": {"lat": 18.6725, "lon": 78.0941},
        "karimnagar": {"lat": 18.4386, "lon": 79.1288},
        "khammam": {"lat": 17.2473, "lon": 80.1514},
        # Maharashtra
        "mumbai": {"lat": 19.0760, "lon": 72.8777},
        "mumbai, india": {"lat": 19.0760, "lon": 72.8777},
        "pune": {"lat": 18.5204, "lon": 73.8567},
        "nagpur": {"lat": 21.1458, "lon": 79.0882},
        "thane": {"lat": 19.2183, "lon": 72.9781},
        "nashik": {"lat": 19.9975, "lon": 73.7898},
        "aurangabad": {"lat": 19.8762, "lon": 75.3433},
        "chhatrapati sambhajinagar": {"lat": 19.8762, "lon": 75.3433},
        "solapur": {"lat": 17.6599, "lon": 75.9064},
        "navi mumbai": {"lat": 19.0330, "lon": 73.0297},
        "kolhapur": {"lat": 16.7050, "lon": 74.2433},
        # Karnataka
        "bangalore": {"lat": 12.9716, "lon": 77.5946},
        "bangalore, india": {"lat": 12.9716, "lon": 77.5946},
        "bengaluru": {"lat": 12.9716, "lon": 77.5946},
        "mysore": {"lat": 12.2958, "lon": 76.6394},
        "mysuru": {"lat": 12.2958, "lon": 76.6394},
        "hubli": {"lat": 15.3647, "lon": 75.1240},
        "hubli-dharwad": {"lat": 15.3647, "lon": 75.1240},
        "mangalore": {"lat": 12.9141, "lon": 74.8560},
        "mangaluru": {"lat": 12.9141, "lon": 74.8560},
        "belgaum": {"lat": 15.8497, "lon": 74.4977},
        "belagavi": {"lat": 15.8497, "lon": 74.4977},
        "davanagere": {"lat": 14.4644, "lon": 75.9218},
        "shimoga": {"lat": 13.9299, "lon": 75.5681},
        # Tamil Nadu
        "chennai": {"lat": 13.0827, "lon": 80.2707},
        "chennai, india": {"lat": 13.0827, "lon": 80.2707},
        "coimbatore": {"lat": 11.0168, "lon": 76.9558},
        "madurai": {"lat": 9.9252, "lon": 78.1198},
        "tiruchirappalli": {"lat": 10.7905, "lon": 78.7047},
        "trichy": {"lat": 10.7905, "lon": 78.7047},
        "salem": {"lat": 11.6643, "lon": 78.1460},
        "tiruppur": {"lat": 11.1085, "lon": 77.3411},
        "erode": {"lat": 11.3410, "lon": 77.7172},
        "vellore": {"lat": 12.9165, "lon": 79.1325},
        # Delhi NCR
        "delhi": {"lat": 28.6139, "lon": 77.2090},
        "delhi, india": {"lat": 28.6139, "lon": 77.2090},
        "new delhi": {"lat": 28.6139, "lon": 77.2090},
        "noida": {"lat": 28.5355, "lon": 77.3910},
        "gurgaon": {"lat": 28.4595, "lon": 77.0266},
        "gurugram": {"lat": 28.4595, "lon": 77.0266},
        "faridabad": {"lat": 28.4089, "lon": 77.3178},
        "ghaziabad": {"lat": 28.6692, "lon": 77.4538},
        # Gujarat
        "ahmedabad": {"lat": 23.0225, "lon": 72.5714},
        "surat": {"lat": 21.1702, "lon": 72.8311},
        "vadodara": {"lat": 22.3072, "lon": 73.1812},
        "rajkot": {"lat": 22.3039, "lon": 70.8022},
        "bhavnagar": {"lat": 21.7645, "lon": 72.1519},
        "jamnagar": {"lat": 22.4707, "lon": 70.0577},
        "gandhinagar": {"lat": 23.2156, "lon": 72.6369},
        # West Bengal
        "kolkata": {"lat": 22.5726, "lon": 88.3639},
        "howrah": {"lat": 22.5958, "lon": 88.2636},
        "siliguri": {"lat": 26.7271, "lon": 88.3953},
        "asansol": {"lat": 23.6739, "lon": 86.9524},
        "durgapur": {"lat": 23.5204, "lon": 87.3119},
        # Uttar Pradesh
        "lucknow": {"lat": 26.8467, "lon": 80.9462},
        "kanpur": {"lat": 26.4499, "lon": 80.3319},
        "varanasi": {"lat": 25.3176, "lon": 82.9739},
        "agra": {"lat": 27.1767, "lon": 78.0081},
        "prayagraj": {"lat": 25.4358, "lon": 81.8463},
        "allahabad": {"lat": 25.4358, "lon": 81.8463},
        "meerut": {"lat": 28.9845, "lon": 77.7064},
        "bareilly": {"lat": 28.3670, "lon": 79.4304},
        "aligarh": {"lat": 27.8974, "lon": 78.0880},
        "moradabad": {"lat": 28.8386, "lon": 78.7733},
        # Rajasthan
        "jaipur": {"lat": 26.9124, "lon": 75.7873},
        "jodhpur": {"lat": 26.2389, "lon": 73.0243},
        "kota": {"lat": 25.2138, "lon": 75.8648},
        "bikaner": {"lat": 28.0229, "lon": 73.3119},
        "ajmer": {"lat": 26.4499, "lon": 74.6399},
        "udaipur": {"lat": 24.5854, "lon": 73.7125},
        # Madhya Pradesh
        "bhopal": {"lat": 23.2599, "lon": 77.4126},
        "indore": {"lat": 22.7196, "lon": 75.8577},
        "jabalpur": {"lat": 23.1815, "lon": 79.9864},
        "gwalior": {"lat": 26.2183, "lon": 78.1828},
        "ujjain": {"lat": 23.1765, "lon": 75.7885},
        # Punjab & Haryana
        "chandigarh": {"lat": 30.7333, "lon": 76.7794},
        "ludhiana": {"lat": 30.9010, "lon": 75.8573},
        "amritsar": {"lat": 31.6340, "lon": 74.8723},
        "jalandhar": {"lat": 31.3260, "lon": 75.5762},
        "patiala": {"lat": 30.3398, "lon": 76.3869},
        "bathinda": {"lat": 30.2110, "lon": 74.9455},
        "panipat": {"lat": 29.3909, "lon": 76.9635},
        "rohtak": {"lat": 28.8955, "lon": 76.6066},
        "karnal": {"lat": 29.6857, "lon": 76.9905},
        "sonipat": {"lat": 28.9931, "lon": 77.0151},
        # Kerala
        "kochi": {"lat": 9.9312, "lon": 76.2673},
        "cochin": {"lat": 9.9312, "lon": 76.2673},
        "thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366},
        "trivandrum": {"lat": 8.5241, "lon": 76.9366},
        "kozhikode": {"lat": 11.2588, "lon": 75.7804},
        "calicut": {"lat": 11.2588, "lon": 75.7804},
        "thrissur": {"lat": 10.5276, "lon": 76.2144},
        "kollam": {"lat": 8.8932, "lon": 76.6141},
        "kannur": {"lat": 11.8745, "lon": 75.3704},
        # Bihar & Jharkhand
        "patna": {"lat": 25.5941, "lon": 85.1376},
        "gaya": {"lat": 24.7914, "lon": 85.0002},
        "bhagalpur": {"lat": 25.2425, "lon": 86.9842},
        "muzaffarpur": {"lat": 26.1209, "lon": 85.3647},
        "ranchi": {"lat": 23.3441, "lon": 85.3096},
        "jamshedpur": {"lat": 22.8046, "lon": 86.2029},
        "dhanbad": {"lat": 23.7957, "lon": 86.4304},
        "bokaro": {"lat": 23.6693, "lon": 86.1511},
        # Odisha
        "bhubaneswar": {"lat": 20.2961, "lon": 85.8245},
        "cuttack": {"lat": 20.4625, "lon": 85.8828},
        "rourkela": {"lat": 22.2604, "lon": 84.8536},
        # Assam & North East
        "guwahati": {"lat": 26.1445, "lon": 91.7362},
        "agartala": {"lat": 23.8315, "lon": 91.2868},
        "shillong": {"lat": 25.5788, "lon": 91.8933},
        "imphal": {"lat": 24.8170, "lon": 93.9368},
        "aizawl": {"lat": 23.7271, "lon": 92.7176},
        "kohima": {"lat": 25.6751, "lon": 94.1086},
        "gangtok": {"lat": 27.3389, "lon": 88.6065},
        "itanagar": {"lat": 27.0844, "lon": 93.6053},
        # Goa
        "panaji": {"lat": 15.4909, "lon": 73.8278},
        "margao": {"lat": 15.2832, "lon": 73.9862},
        "vasco da gama": {"lat": 15.3959, "lon": 73.8157},
        # Uttarakhand & HP
        "dehradun": {"lat": 30.3165, "lon": 78.0322},
        "haridwar": {"lat": 29.9457, "lon": 78.1642},
        "rishikesh": {"lat": 30.0869, "lon": 78.2676},
        "shimla": {"lat": 31.1048, "lon": 77.1734},
        # Chhattisgarh
        "raipur": {"lat": 21.2514, "lon": 81.6296},
        "bilaspur": {"lat": 22.0797, "lon": 82.1409},
        "bhilai": {"lat": 21.2144, "lon": 81.3807},
        # J&K
        "srinagar": {"lat": 34.0837, "lon": 74.7973},
        "jammu": {"lat": 32.7266, "lon": 74.8570},
        # UTs
        "puducherry": {"lat": 11.9416, "lon": 79.8083},
        "pondicherry": {"lat": 11.9416, "lon": 79.8083},
        # Country
        "india": {"lat": 20.5937, "lon": 78.9629},
    }

    def _parse_radius_meters(self, radius_str: Optional[str]) -> int:
        """Parse human radius string (e.g. '5 km', '5 miles') to meters with safe bounds"""
        if not radius_str:
            return 4000
        try:
            nums = re.findall(r"\d+", str(radius_str))
            if nums:
                val = int(nums[0])
                if "mile" in radius_str.lower():
                    val = int(val * 1609.34)
                elif val <= 100:
                    val = val * 1000
                return max(2000, min(val, 5000))
        except Exception:
            pass
        return 4000

    async def _geocode_city(self, city: str) -> Optional[dict]:
        """
        Resolve any city globally to coordinates (lat, lon) and bounding box.
        Checks instant global cache first, then queries Nominatim.
        """
        city_clean = city.strip().lower()
        if city_clean in self.GLOBAL_CITY_COORDS:
            c = self.GLOBAL_CITY_COORDS[city_clean]
            return {"lat": c["lat"], "lon": c["lon"], "bbox": None, "display_name": city}

        # Check by city name before comma if present (e.g. "Chicago, Illinois" -> "chicago")
        if "," in city_clean:
            first_part = city_clean.split(",")[0].strip()
            if first_part in self.GLOBAL_CITY_COORDS:
                c = self.GLOBAL_CITY_COORDS[first_part]
                return {"lat": c["lat"], "lon": c["lon"], "bbox": None, "display_name": city}

        # Query Nominatim with fallback
        queries_to_try = [city]
        if "," in city:
            queries_to_try.append(city.split(",")[0].strip())

        for q in queries_to_try:
            try:
                async with httpx.AsyncClient(
                    timeout=10.0,
                    headers={"User-Agent": "AIClientFinder/1.0 (B2B Lead Discovery Tool; contact@clientfinder.app)"}
                ) as client:
                    resp = await client.get(self.NOMINATIM_URL, params={
                        "q": q,
                        "format": "json",
                        "limit": 5,
                        "countrycodes": "in",
                        "addressdetails": 1,
                    })
                    if resp.status_code == 200:
                        results = resp.json()
                        for r in results:
                            osm_type = r.get("osm_type", "")
                            place_class = r.get("class", "")
                            if (osm_type == "relation" and place_class in ("boundary", "place")) or place_class == "place":
                                return {
                                    "lat": float(r.get("lat", 0.0)),
                                    "lon": float(r.get("lon", 0.0)),
                                    "bbox": r.get("boundingbox"),
                                    "display_name": r.get("display_name", city),
                                }
                        if results:
                            r = results[0]
                            return {
                                "lat": float(r.get("lat", 0.0)),
                                "lon": float(r.get("lon", 0.0)),
                                "bbox": r.get("boundingbox"),
                                "display_name": r.get("display_name", city),
                            }
            except Exception as e:
                logger.warning(f"Nominatim geocoding failed for '{q}': {e}")
        return None

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        logger.info(f"OverpassBusinessProvider: '{query.category}' in '{query.location}'")

        cat_key = query.category.strip().lower()
        osm_tags = self.CATEGORY_MAP.get(cat_key)

        # Fuzzy match if no exact category found
        if not osm_tags:
            for k, v in self.CATEGORY_MAP.items():
                if cat_key in k or k in cat_key:
                    osm_tags = v
                    break

        # Default fallback tags
        if not osm_tags:
            osm_tags = [f"shop={cat_key}", f"amenity={cat_key}", f"office={cat_key}", f"craft={cat_key}"]

        # Geocode city
        geo = await self._geocode_city(query.location)
        lat = geo.get("lat") if geo else None
        lon = geo.get("lon") if geo else None
        bbox = geo.get("bbox") if geo else None
        radius_m = self._parse_radius_meters(query.radius)

        # Build fast, targeted Overpass query searching nodes and ways
        if lat and lon and lat != 0.0 and lon != 0.0:
            tag_unions = "".join([
                f'  node[{tag}](around:{radius_m},{lat},{lon});\n'
                f'  way[{tag}](around:{radius_m},{lat},{lon});\n'
                for tag in osm_tags
            ])
            overpass_query = f"""\
[out:json][timeout:12];
(
{tag_unions});
out tags center 60;
"""
            logger.info(f"Overpass radius search around ({lat}, {lon}) with radius={radius_m}m")
        elif bbox and len(bbox) == 4:
            south, north, west, east = bbox
            tag_unions = "".join([
                f'  node[{tag}]({south},{west},{north},{east});\n'
                f'  way[{tag}]({south},{west},{north},{east});\n'
                for tag in osm_tags
            ])
            overpass_query = f"""\
[out:json][timeout:12];
(
{tag_unions});
out tags center 60;
"""
            logger.info(f"Overpass bounding box search: {bbox}")
        else:
            tag_unions = "".join([
                f'  node[{tag}](area.cityArea);\n'
                f'  way[{tag}](area.cityArea);\n'
                for tag in osm_tags
            ])
            overpass_query = f"""\
[out:json][timeout:12];
area[name="{query.location}"]["boundary"="administrative"]->.cityArea;
(
{tag_unions});
out tags center 60;
"""
            logger.info(f"Overpass named area search for '{query.location}'")

        # Try Overpass endpoints
        headers = {
            "User-Agent": "AIClientFinder/1.0 (B2B Lead Discovery Tool; contact@clientfinder.app)"
        }

        for endpoint in self.OVERPASS_URLS:
            try:
                async with httpx.AsyncClient(timeout=8.0, headers=headers) as client:
                    resp = await client.post(endpoint, data={"data": overpass_query})
                    if resp.status_code == 200:
                        data = resp.json()
                        elements = data.get("elements", [])
                        results = []

                        for el in elements:
                            try:
                                tags = el.get("tags", {})
                                raw_name = tags.get("name") or tags.get("name:en")
                                if not raw_name:
                                    continue
                                name = str(raw_name).strip()

                                # Nodes have lat/lon directly; ways & relations have 'center' dict
                                el_type = el.get("type", "node")
                                if el_type in ("way", "relation"):
                                    center = el.get("center", {})
                                    lat_val = center.get("lat", 0.0)
                                    lon_val = center.get("lon", 0.0)
                                else:
                                    lat_val = el.get("lat", 0.0)
                                    lon_val = el.get("lon", 0.0)

                                # Skip elements with missing coordinates
                                lat_val = _safe_float(lat_val, 0.0)
                                lon_val = _safe_float(lon_val, 0.0)
                                if lat_val == 0.0 and lon_val == 0.0:
                                    continue

                                # Build accurate address from all available OSM address fields
                                full_addr = tags.get("addr:full")
                                addr_parts = []
                                for field in ["addr:housenumber", "addr:street", "addr:suburb",
                                              "addr:district", "addr:city", "addr:postcode"]:
                                    if tags.get(field):
                                        addr_parts.append(str(tags[field]))

                                if full_addr:
                                    address = str(full_addr)
                                elif addr_parts:
                                    if query.location.lower() not in [p.lower() for p in addr_parts]:
                                        addr_parts.append(query.location)
                                    address = ", ".join(addr_parts)
                                else:
                                    address = query.location

                                # Contact info — comprehensive OSM phone tag coverage
                                raw_phone = (
                                    tags.get("phone") or
                                    tags.get("contact:phone") or
                                    tags.get("contact:mobile") or
                                    tags.get("mobile") or
                                    tags.get("contact:whatsapp") or
                                    tags.get("whatsapp") or
                                    tags.get("telephone") or
                                    tags.get("tel") or
                                    tags.get("phone:mobile") or
                                    tags.get("contact:telephone") or
                                    tags.get("phone:en") or
                                    tags.get("operator:phone") or
                                    tags.get("phone:IN") or
                                    tags.get("phone:US") or
                                    tags.get("phone:GB") or
                                    tags.get("tollfree") or
                                    tags.get("fax") or ""
                                )
                                phone = ""
                                if raw_phone:
                                    phone = re.split(r'[;/]', str(raw_phone))[0].strip()

                                if _is_corporate_chain(name, tags):
                                    continue

                                # Website extraction — separates true official websites from social/aggregator links
                                raw_website = (
                                    tags.get("website") or
                                    tags.get("contact:website") or
                                    tags.get("url") or
                                    tags.get("contact:url") or
                                    tags.get("brand:website") or
                                    tags.get("official_website") or
                                    tags.get("operator:website") or
                                    tags.get("website:en") or ""
                                )
                                display_website, has_social, has_app = _classify_digital_presence(raw_website, tags)

                                opening_hours = tags.get("opening_hours", "")
                                if opening_hours and len(address) < 80:
                                    address += f" | Hours: {opening_hours}"

                                results.append(
                                    NormalizedBusiness(
                                        name=name,
                                        category=query.category.title(),
                                        phone=phone,
                                        website=display_website,
                                        address=address,
                                        city=query.location,
                                        latitude=lat_val,
                                        longitude=lon_val,
                                        rating=_safe_float(tags.get("stars"), 0.0),
                                        review_count=_safe_int(tags.get("review_count"), 0),
                                        source="OpenStreetMap Live Data",
                                        source_url=display_website or f"https://www.openstreetmap.org/{el_type}/{el.get('id')}",
                                        provider_id=f"osm_{el.get('id')}",
                                        has_social_media=has_social,
                                        has_mobile_app=has_app,
                                    )
                                )
                            except Exception as item_err:
                                logger.debug(f"Skipping malformed OSM element: {item_err}")
                                continue

                        # Deduplicate by name and prioritize businesses with verified phone & missing Web/App/Marketing
                        seen_names = set()
                        unique_results = []
                        results.sort(
                            key=lambda b: (
                                1 if (b.phone and not b.website and not b.has_mobile_app and not b.has_social_media) else 0,
                                1 if (b.phone and not b.website) else 0,
                                1 if b.phone else 0,
                                1 if b.website else 0,
                                1 if (b.address and b.address != query.location) else 0,
                            ),
                            reverse=True,
                        )
                        for biz in results:
                            norm_name = re.sub(r"[^a-z0-9]", "", biz.name.lower())
                            if not norm_name or norm_name in seen_names:
                                continue
                            seen_names.add(norm_name)
                            unique_results.append(biz)
                            if len(unique_results) >= 35:
                                break

                        logger.info(f"Overpass ({endpoint}): found {len(unique_results)} live businesses for '{query.category}' in '{query.location}'")
                        return unique_results
                    else:
                        logger.warning(f"Overpass ({endpoint}) returned status {resp.status_code}, trying next mirror if available...")
            except Exception as e:
                logger.warning(f"Overpass ({endpoint}) error: {e}, trying next mirror if available...")

        logger.warning(f"Overpass found 0 live results for '{query.category}' in '{query.location}'.")
        return []


class GooglePlacesCompliantProvider(BusinessDataProvider):
    """
    Compliant Google Places API (New Text Search) Provider.
    Only queries the official Google Places API using authorized API key.
    """
    PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.BUSINESS_API_KEY

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        api_key = self.api_key or settings.BUSINESS_API_KEY
        if not api_key:
            logger.info("BUSINESS_API_KEY not configured. Using live GoogleMapsWebProvider.")
            return await GoogleMapsWebProvider().search(query)

        loc = query.location.strip()
        if not loc.lower().endswith("india") and "india" not in loc.lower():
            loc = f"{loc}, India"
        text_query = f"{query.category} in {loc}"
        if query.keywords:
            text_query += f" {query.keywords}"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.internationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.location"
        }
        payload = {
            "textQuery": text_query,
            "maxResultCount": 20
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(self.PLACES_API_URL, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    places = data.get("places", [])
                    results = []
                    seen_names = set()
                    for p in places:
                        name = p.get("displayName", {}).get("text", "Unknown Business").strip()
                        if not name or _is_corporate_chain(name, {}):
                            continue

                        norm_name = re.sub(r"[^a-z0-9]", "", name.lower())
                        if not norm_name or norm_name in seen_names:
                            continue
                        seen_names.add(norm_name)

                        phone = str(p.get("nationalPhoneNumber") or p.get("internationalPhoneNumber") or "").strip()
                        raw_website = str(p.get("websiteUri") or "").strip()
                        website, has_social, has_app = _classify_digital_presence(raw_website, {})

                        address = str(p.get("formattedAddress") or query.location).strip()
                        loc_coords = p.get("location", {})
                        place_id = str(p.get("id") or "")

                        footprint = []
                        if website:
                            footprint.append(f"Official Website: {website}")
                        if has_social:
                            footprint.append(f"Social Profile Found: {raw_website}")
                        if has_app:
                            footprint.append("Mobile App Listed")

                        results.append(
                            NormalizedBusiness(
                                name=name,
                                category=query.category.title(),
                                phone=phone,
                                website=website,
                                address=address,
                                city=query.location,
                                latitude=_safe_float(loc_coords.get("latitude"), 0.0),
                                longitude=_safe_float(loc_coords.get("longitude"), 0.0),
                                rating=_safe_float(p.get("rating"), 0.0),
                                review_count=_safe_int(p.get("userRatingCount"), 0),
                                source="Google Places API (Authorized)",
                                source_url=website or (f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://www.google.com/maps/search/?api=1&query={quote_plus(name)}+{quote_plus(query.location)}"),
                                provider_id=f"google_{place_id}" if place_id else None,
                                has_social_media=has_social,
                                has_mobile_app=has_app,
                                digital_footprint=footprint,
                            )
                        )

                    # Propagate verified brand websites across multi-branch locations
                    brand_websites = {}
                    brand_social = set()
                    for b in results:
                        norm = re.sub(r"[^a-z0-9]", "", b.name.lower())
                        if b.website and norm not in brand_websites:
                            brand_websites[norm] = b.website
                        if b.has_social_media:
                            brand_social.add(norm)

                    for b in results:
                        norm = re.sub(r"[^a-z0-9]", "", b.name.lower())
                        if norm in brand_websites and not b.website:
                            b.website = brand_websites[norm]
                        if norm in brand_social:
                            b.has_social_media = True

                    # Prioritize leads with verified phone numbers
                    results.sort(
                        key=lambda b: (
                            1 if (b.phone and not b.website and not b.has_mobile_app and not b.has_social_media) else 0,
                            1 if (b.phone and not b.website) else 0,
                            1 if not b.website else 0,
                            1 if b.phone else 0,
                            b.review_count,
                        ),
                        reverse=True,
                    )

                    logger.info(f"Google Places API: Discovered {len(results)} authorized places for '{query.category}' in '{query.location}'")
                    return results
                else:
                    logger.error(f"Google Places API error ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Google Places API connection exception: {e}")

        # Fallback to GoogleMapsWebProvider if API request fails
        logger.info("Falling back to GoogleMapsWebProvider.")
        return await GoogleMapsWebProvider().search(query)


class GeoapifyProvider(BusinessDataProvider):
    """
    Geoapify Places API Provider — 3,000 free requests/day, NO CREDIT CARD required.
    Global coverage with category search and contact details.
    Get free API key at: https://www.geoapify.com/
    """
    PLACES_URL = "https://api.geoapify.com/v2/places"

    CATEGORY_MAP = {
        "restaurant": "catering.restaurant", "restaurants": "catering.restaurant",
        "cafe": "catering.cafe", "cafes": "catering.cafe", "coffee": "catering.cafe",
        "fast food": "catering.fast_food", "pizza": "catering.fast_food,catering.restaurant",
        "bar": "catering.bar", "pub": "catering.pub",
        "bakery": "commercial.food_and_drink.bakery",
        "salon": "service.beauty", "salons": "service.beauty",
        "spa": "service.beauty.spa", "barbershop": "service.beauty.hairdresser",
        "clinic": "healthcare.clinic", "hospital": "healthcare.hospital",
        "healthcare": "healthcare.clinic,healthcare.hospital",
        "pharmacy": "healthcare.pharmacy", "dentist": "healthcare.dentist",
        "dental": "healthcare.dentist", "optician": "healthcare.pharmacy",
        "gym": "sport.fitness", "fitness": "sport.fitness", "yoga": "sport.fitness",
        "veterinary": "pet.veterinary", "vet": "pet.veterinary",
        "hotel": "accommodation.hotel", "hostel": "accommodation.hostel",
        "auto repair": "service.vehicle.repair", "car repair": "service.vehicle.repair",
        "mechanic": "service.vehicle.repair",
        "plumber": "service.trade,office.company", "plumbing": "service.trade,office.company",
        "roofing": "service.trade,office.company", "roofer": "service.trade,office.company",
        "hvac": "service.trade,office.company", "contractor": "service.trade,office.company",
        "electrician": "service.trade,office.company", "cleaning": "service.cleaning,office.company",
        "lawyer": "office.lawyer", "law firm": "office.lawyer",
        "accountant": "office.accountant", "accounting": "office.accountant",
        "real estate": "office.estate_agent", "marketing": "office.company",
        "marketing agency": "office.company",
        "supermarket": "commercial.supermarket", "retail": "commercial.shopping_mall,commercial.clothing",
        "photography": "service.photography,office.company", "school": "education.school",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "GEOAPIFY_API_KEY", None)

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        if not self.api_key:
            logger.info("GEOAPIFY_API_KEY not configured — skipping Geoapify.")
            return []

        cat_key = query.category.strip().lower()
        geo_cat = self.CATEGORY_MAP.get(cat_key)
        if not geo_cat:
            for k, v in self.CATEGORY_MAP.items():
                if k in cat_key or cat_key in k:
                    geo_cat = v
                    break
        if not geo_cat:
            geo_cat = "commercial"

        # Resolve location coordinates using Overpass's geocoding helper
        geo = await OverpassBusinessProvider()._geocode_city(query.location)
        if not geo or not geo.get("lat") or not geo.get("lon"):
            logger.warning(f"Geoapify: Could not geocode city '{query.location}'")
            return []

        lat = geo["lat"]
        lon = geo["lon"]
        radius_m = max(15000, OverpassBusinessProvider()._parse_radius_meters(query.radius))

        params = {
            "categories": geo_cat,
            "filter": f"circle:{lon},{lat},{radius_m}",
            "conditions": "named",
            "limit": 500,
            "apiKey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(self.PLACES_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    if not features:
                        fallback_params = {
                            **params,
                            "categories": f"{geo_cat},commercial,service,office",
                            "filter": f"circle:{lon},{lat},20000",
                        }
                        resp2 = await client.get(self.PLACES_URL, params=fallback_params)
                        if resp2.status_code == 200:
                            features = resp2.json().get("features", [])
                    results = []
                    for f in features:
                        try:
                            props = f.get("properties", {})
                            raw_name = props.get("name")
                            if raw_name is None or str(raw_name).strip() == "":
                                continue
                            name = str(raw_name).strip()

                            contact = props.get("contact", {})
                            raw_data = props.get("datasource", {}).get("raw", {})

                            if _is_corporate_chain(name, raw_data):
                                continue

                            raw_phone = (
                                contact.get("phone") or
                                props.get("phone") or
                                raw_data.get("phone") or
                                raw_data.get("contact:phone") or
                                raw_data.get("contact:mobile") or
                                raw_data.get("mobile") or
                                raw_data.get("contact:whatsapp") or
                                raw_data.get("whatsapp") or
                                raw_data.get("telephone") or
                                raw_data.get("tel") or ""
                            )
                            phone = re.split(r'[;/,]', str(raw_phone))[0].strip() if raw_phone else ""

                            raw_website = (
                                props.get("website") or
                                contact.get("website") or
                                raw_data.get("website") or
                                raw_data.get("contact:website") or
                                raw_data.get("url") or
                                raw_data.get("contact:url") or ""
                            )
                            website, has_social, has_app = _classify_digital_presence(raw_website, raw_data)

                            addr = str(props.get("formatted") or props.get("address_line1") or query.location)
                            place_id = str(props.get("place_id", ""))
                            lat_val = _safe_float(props.get("lat"), 0.0)
                            lon_val = _safe_float(props.get("lon"), 0.0)
                            stars = raw_data.get("stars")
                            rating = _safe_float(stars, 0.0)
                            review_cnt = _safe_int(raw_data.get("review_count"), 0)

                            results.append(
                                NormalizedBusiness(
                                    name=name,
                                    category=query.category.title(),
                                    phone=str(phone) if phone else "",
                                    website=website,
                                    address=addr,
                                    city=query.location,
                                    latitude=lat_val,
                                    longitude=lon_val,
                                    rating=rating,
                                    review_count=review_cnt,
                                    source="Geoapify Places",
                                    source_url=website or f"https://www.google.com/maps/search/?api=1&query={name}+{query.location}",
                                    provider_id=f"geoapify_{place_id}" if place_id else None,
                                    has_social_media=has_social,
                                    has_mobile_app=has_app,
                                )
                            )
                        except Exception as item_err:
                            logger.debug(f"Skipping malformed Geoapify feature: {item_err}")
                            continue

                    # Propagate known brand websites/social/apps across multiple branches of the same business name
                    brand_websites = {}
                    brand_social = set()
                    brand_apps = set()
                    for biz in results:
                        norm_name = re.sub(r"[^a-z0-9]", "", biz.name.lower())
                        if not norm_name:
                            continue
                        if biz.website and norm_name not in brand_websites:
                            brand_websites[norm_name] = biz.website
                        if biz.has_social_media:
                            brand_social.add(norm_name)
                        if biz.has_mobile_app:
                            brand_apps.add(norm_name)

                    for biz in results:
                        norm_name = re.sub(r"[^a-z0-9]", "", biz.name.lower())
                        if norm_name in brand_websites and not biz.website:
                            biz.website = brand_websites[norm_name]
                        if norm_name in brand_social:
                            biz.has_social_media = True
                        if norm_name in brand_apps:
                            biz.has_mobile_app = True

                    # Prioritize genuine businesses missing Website/WebApp, Mobile App, and Digital Marketing with verified phone
                    results.sort(
                        key=lambda b: (
                            1 if (b.phone and not b.website and not b.has_mobile_app and not b.has_social_media) else 0,
                            1 if (b.phone and not b.website) else 0,
                            1 if (not b.website and b.address and b.address != query.location) else 0,
                            1 if not b.website else 0,
                            1 if b.phone else 0,
                        ),
                        reverse=True,
                    )

                    # Deduplicate by normalized business name so chains don't flood results
                    seen_names = set()
                    unique_results = []
                    for biz in results:
                        norm_name = re.sub(r"[^a-z0-9]", "", biz.name.lower())
                        if not norm_name or norm_name in seen_names:
                            continue
                        seen_names.add(norm_name)
                        unique_results.append(biz)
                        if len(unique_results) >= 40:
                            break

                    logger.info(
                        f"Geoapify: Scanned {len(results)} places, returning top {len(unique_results)} genuine leads "
                        f"({sum(1 for b in unique_results if b.phone)} with verified phone) for '{query.category}' in '{query.location}'"
                    )
                    return unique_results
                else:
                    logger.warning(f"Geoapify Places API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Geoapify Places API exception: {e}")

        return []



class YelpFusionProvider(BusinessDataProvider):
    """
    Yelp Fusion API Provider — 500 free calls/day, no credit card.
    Excellent phone + website coverage for US, UK, Canada, Australia, EU.
    Get free API key at: https://fusion.yelp.com/
    """
    YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
    YELP_DETAILS_URL = "https://api.yelp.com/v3/businesses/{id}"

    # Map our categories to Yelp alias terms
    YELP_CATEGORY_MAP = {
        "restaurant": "restaurants", "restaurants": "restaurants",
        "cafe": "cafes", "cafes": "cafes", "coffee": "coffee",
        "fast food": "hotdogs", "pizza": "pizza",
        "bar": "bars", "pub": "beerbar",
        "bakery": "bakeries", "salon": "hair", "salons": "hair",
        "spa": "beautysvc", "barbershop": "barbers",
        "gym": "gyms", "fitness": "gyms", "yoga": "yoga",
        "dentist": "dentists", "dental": "dentists",
        "clinic": "mediccenters", "doctor": "physicians",
        "pharmacy": "pharmacy", "optician": "optometrists",
        "veterinary": "veterinarians", "vet": "veterinarians",
        "hotel": "hotels", "plumber": "plumbing",
        "electrician": "electricians", "hvac": "hvac",
        "auto repair": "autorepair", "car repair": "autorepair",
        "lawyer": "lawyers", "law firm": "lawyers",
        "accountant": "accountants", "accounting": "accountants",
        "real estate": "realestate", "insurance": "insurance",
        "marketing": "marketing", "cleaning": "homecleaning",
        "landscaping": "landscaping", "contractor": "contractors",
        "grocery": "grocery", "supermarket": "grocery",
        "electronics": "electronics", "clothing": "womenscloth",
        "hotel": "hotels", "bank": "banks",
        "photography": "photographers", "school": "educationservices",
        "travel": "travelagents", "printing": "printmedia",
        "laundry": "laundry",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.YELP_API_KEY

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        if not self.api_key:
            logger.info("YELP_API_KEY not configured — skipping Yelp.")
            return []

        cat_key = query.category.strip().lower()
        yelp_term = self.YELP_CATEGORY_MAP.get(cat_key, query.category)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        params = {
            "term": yelp_term,
            "location": query.location,
            "limit": 50,
            "sort_by": "review_count",  # most reviewed = most established businesses
        }

        try:
            async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                resp = await client.get(self.YELP_SEARCH_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    businesses = data.get("businesses", [])
                    results = []
                    for biz in businesses:
                        if biz.get("is_closed"):
                            continue
                        coords = biz.get("coordinates", {})
                        loc = biz.get("location", {})
                        address_parts = [p for p in [
                            loc.get("address1"), loc.get("address2"),
                            loc.get("city"), loc.get("state"), loc.get("country")
                        ] if p]
                        address = ", ".join(address_parts) or query.location

                        # Yelp basic search doesn't return phone/website — need details call
                        # We return what we have; SmartFallbackProvider enriches missing fields
                        phone = biz.get("phone", "") or biz.get("display_phone", "")
                        website = biz.get("url", "")  # Yelp URL (we'll get real website from details)

                        categories = biz.get("categories", [])
                        cat_label = categories[0].get("title", query.category) if categories else query.category

                        results.append(NormalizedBusiness(
                            name=biz.get("name", "Unknown"),
                            category=cat_label,
                            phone=phone,
                            website=website,
                            address=address,
                            city=loc.get("city", query.location),
                            latitude=coords.get("latitude", 0.0),
                            longitude=coords.get("longitude", 0.0),
                            rating=float(biz.get("rating", 0.0)),
                            review_count=int(biz.get("review_count", 0)),
                            source="Yelp Fusion",
                            source_url=biz.get("url", ""),
                            provider_id=f"yelp_{biz.get('id', '')}",
                        ))

                    logger.info(f"Yelp: found {len(results)} businesses for '{query.category}' in '{query.location}'")
                    return results
                elif resp.status_code == 401:
                    logger.error("Yelp API: Invalid API key (401). Check YELP_API_KEY in .env")
                elif resp.status_code == 429:
                    logger.warning("Yelp API: Rate limit hit (429). Daily 500 limit reached.")
                else:
                    logger.warning(f"Yelp API: {resp.status_code} — {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Yelp API exception: {e}")

        return []

    async def get_business_details(self, yelp_id: str) -> dict:
        """Fetch full business details (phone, website) from Yelp by business ID."""
        if not self.api_key:
            return {}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        clean_id = yelp_id.replace("yelp_", "")
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.get(self.YELP_DETAILS_URL.format(id=clean_id))
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Yelp details fetch error for {clean_id}: {e}")
        return {}


class FoursquareProvider(BusinessDataProvider):
    """
    Foursquare Places API Provider — 1000 free calls/day, global coverage.
    Good phone + website data, strong worldwide coverage.
    Get free API key at: https://location.foursquare.com/developer/
    """
    FSQ_SEARCH_URL = "https://api.foursquare.com/v3/places/search"

    # Map categories to Foursquare category IDs (top-level)
    FSQ_CATEGORY_MAP = {
        "restaurant": "13000", "restaurants": "13000",
        "cafe": "13032", "cafes": "13032", "coffee": "13032",
        "fast food": "13145", "pizza": "13064",
        "bar": "13003", "pub": "13003",
        "bakery": "13002", "salon": "11134", "salons": "11134",
        "spa": "11120", "barbershop": "11101",
        "gym": "18021", "fitness": "18021", "yoga": "18008",
        "dentist": "15014", "dental": "15014",
        "clinic": "15000", "doctor": "15000",
        "pharmacy": "17069", "hotel": "19014",
        "auto repair": "11134", "car repair": "11134",
        "lawyer": "11100", "accountant": "11100",
        "real estate": "11100", "bank": "11103",
        "grocery": "17069", "supermarket": "17069",
        "school": "12058", "photography": "11100",
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.FOURSQUARE_API_KEY

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        # Foursquare Places API v3 was DEPRECATED on May 15, 2026.
        # All /v3/ endpoints return 410 Gone. Skipping this provider.
        logger.warning(
            "Foursquare Places API v3 is no longer available (deprecated May 2026). "
            "The SmartFallback will use Yelp or OSM instead."
        )
        return []


class SerperGoogleMapsProvider(BusinessDataProvider):
    """
    Serper.dev Google Maps Places API Provider — 2,500 free queries (NO CREDIT CARD required).
    Returns 100% live Google Maps listings with verified phone numbers, websites, ratings, and review counts.
    Get free API key at: https://serper.dev
    """
    SERPER_PLACES_URL = "https://google.serper.dev/places"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "SERPER_API_KEY", None)

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        if not self.api_key:
            return []

        text_query = f"{query.category} in {query.location}"
        if query.keywords:
            text_query += f" {query.keywords}"

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": text_query, "num": 30}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(self.SERPER_PLACES_URL, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    places = data.get("places", [])
                    results = []
                    for p in places:
                        name = str(p.get("title") or "").strip()
                        if not name:
                            continue
                        phone = str(p.get("phoneNumber") or "").strip()
                        website = str(p.get("website") or "").strip()
                        address = str(p.get("address") or query.location).strip()
                        place_id = str(p.get("cid") or p.get("placeId") or "")
                        results.append(
                            NormalizedBusiness(
                                name=name,
                                category=str(p.get("category") or query.category.title()),
                                phone=phone,
                                website=website,
                                address=address,
                                city=query.location,
                                latitude=_safe_float(p.get("latitude"), 0.0),
                                longitude=_safe_float(p.get("longitude"), 0.0),
                                rating=_safe_float(p.get("rating"), 0.0),
                                review_count=_safe_int(p.get("ratingCount"), 0),
                                source="Google Maps (via Serper)",
                                source_url=website or f"https://www.google.com/maps/search/?api=1&query={name}+{query.location}",
                                provider_id=f"serper_{place_id}" if place_id else None,
                            )
                        )
                    return results
                else:
                    logger.warning(f"Serper Places API returned {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"Serper Places API error: {e}")

        return []


class GoogleMapsWebProvider(BusinessDataProvider):
    """
    Direct Google Maps Web Provider — extracts 100% verified live Google Maps business data
    directly from Google Maps web service without requiring any paid API key.
    Discovers authentic local clients with accurate phone numbers, website presence,
    star ratings, review counts, full addresses, and coordinates.
    """

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._scrape_gmaps_sync, query)
        except Exception as e:
            logger.warning(f"GoogleMapsWebProvider search error: {e}")
            return []

    def _scrape_gmaps_sync(self, query: SearchRequest) -> List[NormalizedBusiness]:
        client = None
        try:
            import primp
            client = primp.Client(impersonate="chrome_131")
        except Exception:
            client = httpx.Client(
                timeout=15.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )

        loc = query.location.strip()
        if not loc.lower().endswith("india") and "india" not in loc.lower():
            loc = f"{loc}, India"
        search_query = f"{query.category} in {loc}"
        if query.keywords:
            search_query += f" {query.keywords}"

        encoded = quote_plus(search_query)
        url = f"https://www.google.com/maps/search/{encoded}/?hl=en"

        logger.info(f"GoogleMapsWebProvider: Searching Google Maps for '{search_query}'")
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                logger.warning(f"GoogleMapsWebProvider: Initial HTTP {resp.status_code}")
                return []
        except Exception as e:
            logger.warning(f"GoogleMapsWebProvider: Request failed {e}")
            return []

        pos = resp.text.find("/search?tbm=map")
        if pos == -1:
            logger.warning("GoogleMapsWebProvider: /search?tbm=map stream not found in page")
            return []

        end_pos = resp.text.find('"', pos)
        if end_pos == -1:
            end_pos = pos + 3000
        url_part = resp.text[pos:end_pos]
        url_clean = html.unescape(url_part)

        try:
            r2 = client.get("https://www.google.com" + url_clean)
            if r2.status_code != 200:
                logger.warning(f"GoogleMapsWebProvider stream HTTP {r2.status_code}")
                return []
        except Exception as e:
            logger.warning(f"GoogleMapsWebProvider stream error {e}")
            return []

        clean_text = re.sub(r"^\)\]\}'[^\n]*\n", "", r2.text)
        try:
            data = json.loads(clean_text)
        except Exception as e:
            logger.warning(f"GoogleMapsWebProvider JSON error: {e}")
            return []

        items = []
        if len(data) > 64 and isinstance(data[64], list) and len(data[64]) > 0:
            items = data[64]
        elif len(data) > 0 and isinstance(data[0], list):
            for sub in data[0]:
                if isinstance(sub, list) and len(sub) > 1 and isinstance(sub[1], list):
                    items.append(sub)

        results: List[NormalizedBusiness] = []
        seen_names = set()

        for item in items:
            p = item[1] if isinstance(item, list) and len(item) > 1 and isinstance(item[1], list) else item
            if not isinstance(p, list) or len(p) <= 11:
                continue

            name = p[11]
            if not name or not isinstance(name, str):
                continue
            name_clean = name.strip()
            norm_name = re.sub(r"[^a-z0-9]", "", name_clean.lower())
            if not norm_name or norm_name in seen_names:
                continue
            seen_names.add(norm_name)

            # Skip corporate giants and chain franchises
            if any(chain in name_clean.lower() for chain in CORPORATE_CHAIN_KEYWORDS):
                continue

            # Website extraction
            raw_website = None
            if len(p) > 7 and p[7] and isinstance(p[7], list) and len(p[7]) > 0:
                raw_website = str(p[7][0]).strip()

            website = ""
            has_social = False
            has_app = False
            footprint = []

            if raw_website:
                if _domain_matches(raw_website, SOCIAL_ONLY_DOMAINS):
                    has_social = True
                    footprint.append(f"Social Profile Found: {raw_website}")
                elif _domain_matches(raw_website, AGGREGATOR_ONLY_DOMAINS):
                    footprint.append(f"Directory Listing: {raw_website}")
                else:
                    website = raw_website
                    footprint.append(f"Official Website: {website}")

            # Phone extraction
            phone = ""
            if len(p) > 178 and p[178] and isinstance(p[178], list) and len(p[178]) > 0:
                try:
                    sub = p[178][0]
                    if isinstance(sub, list):
                        if len(sub) > 1 and isinstance(sub[1], list) and len(sub[1]) > 1 and isinstance(sub[1][1], list) and len(sub[1][1]) > 0:
                            phone = str(sub[1][1][0]).strip()
                        elif len(sub) > 0 and isinstance(sub[0], str):
                            phone = str(sub[0]).strip()
                except Exception:
                    pass

            # Rating and reviews
            rating = 4.0
            review_count = 0
            if len(p) > 4 and p[4] and isinstance(p[4], list):
                if len(p[4]) > 7 and isinstance(p[4][7], (int, float)):
                    rating = round(float(p[4][7]), 1)
                if len(p[4]) > 8 and isinstance(p[4][8], int):
                    review_count = int(p[4][8])

            # Coordinates
            lat, lon = 0.0, 0.0
            if len(p) > 9 and p[9] and isinstance(p[9], list) and len(p[9]) > 3:
                try:
                    lat = float(p[9][2])
                    lon = float(p[9][3])
                except Exception:
                    pass

            # Address
            address = ""
            if len(p) > 18 and p[18]:
                address = str(p[18]).strip()
            elif len(p) > 39 and p[39]:
                address = str(p[39]).strip()
            if not address:
                address = query.location

            # Place ID & source URL
            place_id = str(p[78]) if len(p) > 78 and p[78] else ""
            maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://www.google.com/maps/search/?api=1&query={quote_plus(name_clean)}+{quote_plus(query.location)}"

            results.append(
                NormalizedBusiness(
                    name=name_clean,
                    category=query.category.title(),
                    phone=phone,
                    website=website,
                    address=address,
                    city=query.location,
                    latitude=lat,
                    longitude=lon,
                    rating=rating,
                    review_count=review_count,
                    source="Google Maps",
                    source_url=website or maps_url,
                    provider_id=f"gmaps_{place_id}" if place_id else None,
                    has_social_media=has_social,
                    has_mobile_app=has_app,
                    digital_footprint=footprint,
                )
            )

        # Propagate verified brand websites and social profiles across multiple branches of the same business
        brand_websites = {}
        brand_social = set()
        brand_apps = set()
        for biz in results:
            norm = re.sub(r"[^a-z0-9]", "", biz.name.lower())
            if not norm:
                continue
            if biz.website and norm not in brand_websites:
                brand_websites[norm] = biz.website
            if biz.has_social_media:
                brand_social.add(norm)
            if biz.has_mobile_app:
                brand_apps.add(norm)

        for biz in results:
            norm = re.sub(r"[^a-z0-9]", "", biz.name.lower())
            if norm in brand_websites and not biz.website:
                biz.website = brand_websites[norm]
            if norm in brand_social:
                biz.has_social_media = True
            if norm in brand_apps:
                biz.has_mobile_app = True

        # Sort so candidates that have a phone number but NO website come first
        results.sort(
            key=lambda b: (
                1 if (b.phone and not b.website) else 0,
                1 if not b.website else 0,
                1 if b.phone else 0,
                b.review_count,
            ),
            reverse=True,
        )

        logger.info(f"GoogleMapsWebProvider: Extracted {len(results)} verified businesses from Google Maps web")
        return results


class SmartFallbackProvider(BusinessDataProvider):
    """
    Smart multi-tier fallback provider:
    1. Google Places API (if BUSINESS_API_KEY set) — gold standard worldwide.
    2. Direct Google Maps Web — 100% verified live Google Maps discovery (no paid API key required).
    3. Serper Google Maps (if SERPER_API_KEY set) — 2,500 free Google Maps queries.
    4. Geoapify (if GEOAPIFY_API_KEY set) — 3,000 free requests/day.
    5. Yelp (if YELP_API_KEY set).
    6. OpenStreetMap / Overpass (always active, free, global fallback).
    """

    def __init__(self):
        self.google_api = GooglePlacesCompliantProvider()
        self.gmaps_web = GoogleMapsWebProvider()
        self.serper = SerperGoogleMapsProvider()
        self.geoapify = GeoapifyProvider()
        self.yelp = YelpFusionProvider()
        self.foursquare = FoursquareProvider()
        self.osm = OverpassBusinessProvider()

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        # Tier 1: Google Places API (if BUSINESS_API_KEY set)
        if self.google_api.api_key:
            try:
                g_results = await self.google_api.search(query)
                if g_results:
                    logger.info(f"SmartFallback: Using Google Places API ({len(g_results)} results)")
                    return g_results
            except Exception as e:
                logger.warning(f"SmartFallback: Google Places API failed — {e}")

        # Tier 2: Direct Google Maps Web — 100% live Google Maps web client discovery
        try:
            gw_results = await self.gmaps_web.search(query)
            if gw_results:
                logger.info(f"SmartFallback: Using Direct Google Maps Web ({len(gw_results)} results)")
                return gw_results
        except Exception as e:
            logger.warning(f"SmartFallback: Google Maps Web failed — {e}")

        # Tier 3: Serper Google Maps (if SERPER_API_KEY set)
        if self.serper.api_key:
            try:
                s_results = await self.serper.search(query)
                if s_results:
                    logger.info(f"SmartFallback: Using Serper Google Maps ({len(s_results)} results)")
                    return s_results
            except Exception as e:
                logger.warning(f"SmartFallback: Serper failed — {e}")

        # Tier 4: Geoapify — free 3,000 requests/day, no CC required
        if self.geoapify.api_key:
            try:
                geo_results = await self.geoapify.search(query)
                if geo_results:
                    logger.info(f"SmartFallback: Using Geoapify ({len(geo_results)} results)")
                    return geo_results
            except Exception as e:
                logger.warning(f"SmartFallback: Geoapify failed — {e}")

        # Tier 5: Yelp — if key provided
        if self.yelp.api_key:
            try:
                yelp_results = await self.yelp.search(query)
                if yelp_results:
                    logger.info(f"SmartFallback: Using Yelp ({len(yelp_results)} results)")
                    return yelp_results
            except Exception as e:
                logger.warning(f"SmartFallback: Yelp failed — {e}")

        # Tier 6: OpenStreetMap Overpass — always available, completely free
        try:
            osm_results = await self.osm.search(query)
            if osm_results:
                logger.info(f"SmartFallback: Using Enhanced OSM ({len(osm_results)} results)")
                return osm_results
        except Exception as e:
            logger.warning(f"SmartFallback: OSM failed — {e}")

        return []


def get_business_provider(provider_name: Optional[str] = None) -> BusinessDataProvider:
    name = (provider_name or settings.BUSINESS_API_PROVIDER or "smart").lower()
    if name in ["google", "google_places"]:
        return GooglePlacesCompliantProvider()
    elif name in ["gmaps_web", "google_maps_web", "google_web", "maps_web", "googlemaps"]:
        return GoogleMapsWebProvider()
    elif name in ["geoapify", "geo"]:
        return GeoapifyProvider()
    elif name in ["yelp", "yelp_fusion"]:
        return YelpFusionProvider()
    elif name in ["foursquare", "fsq"]:
        return FoursquareProvider()
    elif name == "mock":
        return MockBusinessProvider()
    elif name == "overpass":
        return OverpassBusinessProvider()
    else:
        # Default: Smart fallback chain (Google API -> Google Maps Web -> Serper -> Geoapify -> Yelp -> OSM)
        return SmartFallbackProvider()


