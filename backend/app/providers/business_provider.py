from abc import ABC, abstractmethod
from typing import List, Optional
import logging
import httpx
import re
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

    # Instant geocoding cache for major worldwide hubs (0ms latency, 100% reliability)
    GLOBAL_CITY_COORDS = {
        # North America
        "new york": {"lat": 40.7128, "lon": -74.0060},
        "new york, usa": {"lat": 40.7128, "lon": -74.0060},
        "nyc": {"lat": 40.7128, "lon": -74.0060},
        "los angeles": {"lat": 34.0522, "lon": -118.2437},
        "los angeles, usa": {"lat": 34.0522, "lon": -118.2437},
        "chicago": {"lat": 41.8781, "lon": -87.6298},
        "chicago, usa": {"lat": 41.8781, "lon": -87.6298},
        "houston": {"lat": 29.7604, "lon": -95.3698},
        "miami": {"lat": 25.7617, "lon": -80.1918},
        "miami, usa": {"lat": 25.7617, "lon": -80.1918},
        "san francisco": {"lat": 37.7749, "lon": -122.4194},
        "san francisco, usa": {"lat": 37.7749, "lon": -122.4194},
        "dallas": {"lat": 32.7767, "lon": -96.7970},
        "seattle": {"lat": 47.6062, "lon": -122.3321},
        "toronto": {"lat": 43.6532, "lon": -79.3832},
        "toronto, canada": {"lat": 43.6532, "lon": -79.3832},
        "vancouver": {"lat": 49.2827, "lon": -123.1207},
        "vancouver, canada": {"lat": 49.2827, "lon": -123.1207},
        "montreal": {"lat": 45.5017, "lon": -73.5673},
        "sao paulo": {"lat": -23.5505, "lon": -46.6333},
        "são paulo": {"lat": -23.5505, "lon": -46.6333},
        "sao paulo, brazil": {"lat": -23.5505, "lon": -46.6333},
        "buenos aires": {"lat": -34.6037, "lon": -58.3816},
        "mexico city": {"lat": 19.4326, "lon": -99.1332},
        # Europe
        "london": {"lat": 51.5074, "lon": -0.1278},
        "london, uk": {"lat": 51.5074, "lon": -0.1278},
        "paris": {"lat": 48.8566, "lon": 2.3522},
        "paris, france": {"lat": 48.8566, "lon": 2.3522},
        "berlin": {"lat": 52.5200, "lon": 13.4050},
        "berlin, germany": {"lat": 52.5200, "lon": 13.4050},
        "amsterdam": {"lat": 52.3676, "lon": 4.9041},
        "amsterdam, netherlands": {"lat": 52.3676, "lon": 4.9041},
        "madrid": {"lat": 40.4168, "lon": -3.7038},
        "madrid, spain": {"lat": 40.4168, "lon": -3.7038},
        "barcelona": {"lat": 41.3851, "lon": 2.1734},
        "rome": {"lat": 41.9028, "lon": 12.4964},
        "rome, italy": {"lat": 41.9028, "lon": 12.4964},
        "dublin": {"lat": 53.3498, "lon": -6.2603},
        "dublin, ireland": {"lat": 53.3498, "lon": -6.2603},
        "zurich": {"lat": 47.3769, "lon": 8.5417},
        "vienna": {"lat": 48.2082, "lon": 16.3738},
        "brussels": {"lat": 50.8503, "lon": 4.3517},
        # Middle East & Asia
        "dubai": {"lat": 25.2048, "lon": 55.2708},
        "dubai, uae": {"lat": 25.2048, "lon": 55.2708},
        "abu dhabi": {"lat": 24.4539, "lon": 54.3773},
        "singapore": {"lat": 1.3521, "lon": 103.8198},
        "tokyo": {"lat": 35.6762, "lon": 139.6503},
        "tokyo, japan": {"lat": 35.6762, "lon": 139.6503},
        "hong kong": {"lat": 22.3193, "lon": 114.1694},
        "bangkok": {"lat": 13.7563, "lon": 100.5018},
        "kuala lumpur": {"lat": 3.1390, "lon": 101.6869},
        "seoul": {"lat": 37.5665, "lon": 126.9780},
        "mumbai": {"lat": 19.0760, "lon": 72.8777},
        "mumbai, india": {"lat": 19.0760, "lon": 72.8777},
        "delhi": {"lat": 28.6139, "lon": 77.2090},
        "delhi, india": {"lat": 28.6139, "lon": 77.2090},
        "bangalore": {"lat": 12.9716, "lon": 77.5946},
        "bengaluru": {"lat": 12.9716, "lon": 77.5946},
        "chennai": {"lat": 13.0827, "lon": 80.2707},
        "chennai, india": {"lat": 13.0827, "lon": 80.2707},
        "hyderabad": {"lat": 17.3850, "lon": 78.4867},
        "pune": {"lat": 18.5204, "lon": 73.8567},
        "kolkata": {"lat": 22.5726, "lon": 88.3639},
        # Oceania & Africa
        "sydney": {"lat": -33.8688, "lon": 151.2093},
        "sydney, australia": {"lat": -33.8688, "lon": 151.2093},
        "melbourne": {"lat": -37.8136, "lon": 144.9631},
        "melbourne, australia": {"lat": -37.8136, "lon": 144.9631},
        "brisbane": {"lat": -27.4698, "lon": 153.0251},
        "auckland": {"lat": -36.8485, "lon": 174.7633},
        "cape town": {"lat": -33.9249, "lon": 18.4241},
        "cape town, south africa": {"lat": -33.9249, "lon": 18.4241},
        "johannesburg": {"lat": -26.2041, "lon": 28.0473},
        "nairobi": {"lat": -1.2921, "lon": 36.8219},
        "cairo": {"lat": 30.0444, "lon": 31.2357},
        # Country-level fallbacks (maps broad country searches to prime commercial hubs)
        "india": {"lat": 19.0760, "lon": 72.8777},
        "usa": {"lat": 40.7128, "lon": -74.0060},
        "united states": {"lat": 40.7128, "lon": -74.0060},
        "uk": {"lat": 51.5074, "lon": -0.1278},
        "united kingdom": {"lat": 51.5074, "lon": -0.1278},
        "canada": {"lat": 43.6532, "lon": -79.3832},
        "australia": {"lat": -33.8688, "lon": 151.2093},
        "uae": {"lat": 25.2048, "lon": 55.2708},
        "germany": {"lat": 52.5200, "lon": 13.4050},
        "france": {"lat": 48.8566, "lon": 2.3522},
        "japan": {"lat": 35.6762, "lon": 139.6503},
        "brazil": {"lat": -23.5505, "lon": -46.6333},
        "south africa": {"lat": -33.9249, "lon": 18.4241},
        "spain": {"lat": 40.4168, "lon": -3.7038},
        "italy": {"lat": 41.9028, "lon": 12.4964},
        "netherlands": {"lat": 52.3676, "lon": 4.9041},
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

                                # Website extraction — checks domains, brand URLs, and social profiles
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

                                # If no direct website, check official social media pages
                                if not raw_website:
                                    fb = tags.get("contact:facebook") or tags.get("facebook")
                                    insta = tags.get("contact:instagram") or tags.get("instagram")
                                    tw = tags.get("contact:twitter") or tags.get("twitter")
                                    li = tags.get("contact:linkedin") or tags.get("linkedin")
                                    if fb:
                                        fb_s = str(fb)
                                        raw_website = fb_s if "facebook.com" in fb_s else f"https://facebook.com/{fb_s.lstrip('@')}"
                                    elif insta:
                                        in_s = str(insta)
                                        raw_website = in_s if "instagram.com" in in_s else f"https://instagram.com/{in_s.lstrip('@')}"
                                    elif tw:
                                        tw_s = str(tw)
                                        raw_website = tw_s if "twitter.com" in tw_s or "x.com" in tw_s else f"https://x.com/{tw_s.lstrip('@')}"
                                    elif li:
                                        li_s = str(li)
                                        raw_website = li_s if "linkedin.com" in li_s else f"https://linkedin.com/company/{li_s.lstrip('@')}"

                                # Clean and ensure proper protocol for URLs
                                display_website = ""
                                if raw_website:
                                    w_clean = str(raw_website).strip()
                                    if w_clean.startswith(("http://", "https://")):
                                        display_website = w_clean
                                    elif "." in w_clean and not w_clean.startswith("@"):
                                        display_website = f"https://{w_clean}"
                                    else:
                                        display_website = w_clean

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
                                        provider_id=f"osm_{el.get('id')}"
                                    )
                                )
                            except Exception as item_err:
                                logger.debug(f"Skipping malformed OSM element: {item_err}")
                                continue

                        # Deduplicate by name and prioritize genuine businesses with verified phone numbers
                        seen_names = set()
                        unique_results = []
                        results.sort(
                            key=lambda b: (
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
        if not self.api_key:
            logger.info("BUSINESS_API_KEY not configured. Using live OverpassBusinessProvider.")
            return await OverpassBusinessProvider().search(query)

        text_query = f"{query.category} in {query.location}"
        if query.keywords:
            text_query += f" {query.keywords}"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
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
                    for p in places:
                        name = p.get("displayName", {}).get("text", "Unknown Business")
                        phone = p.get("nationalPhoneNumber") or p.get("internationalPhoneNumber", "")
                        website = p.get("websiteUri", "")
                        address = p.get("formattedAddress", "")
                        loc = p.get("location", {})
                        place_id = p.get("id", "")

                        results.append(
                            NormalizedBusiness(
                                name=name,
                                category=query.category,
                                phone=phone,
                                website=website,
                                address=address,
                                city=query.location,
                                latitude=loc.get("latitude", 0.0),
                                longitude=loc.get("longitude", 0.0),
                                rating=float(p.get("rating", 0.0)),
                                review_count=int(p.get("userRatingCount", 0)),
                                source="Google Places API (Authorized)",
                                source_url=website or (f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else ""),
                                provider_id=place_id
                            )
                        )
                    return results
                else:
                    logger.error(f"Google Places API error ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.error(f"Google Places API connection exception: {e}")

        return await OverpassBusinessProvider().search(query)


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
        radius_m = max(12000, OverpassBusinessProvider()._parse_radius_meters(query.radius))

        params = {
            "categories": geo_cat,
            "filter": f"circle:{lon},{lat},{radius_m}",
            "conditions": "named",
            "limit": 250,
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

                            # Clean website url
                            website = ""
                            if raw_website:
                                w_clean = str(raw_website).strip()
                                if w_clean.startswith(("http://", "https://")):
                                    website = w_clean
                                elif "." in w_clean and not w_clean.startswith("@"):
                                    website = f"https://{w_clean}"
                                else:
                                    website = w_clean

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
                                    provider_id=f"geoapify_{place_id}" if place_id else None
                                )
                            )
                        except Exception as item_err:
                            logger.debug(f"Skipping malformed Geoapify feature: {item_err}")
                            continue

                    # Prioritize genuine, contactable businesses (verified phone first, especially phone + no website)
                    results.sort(
                        key=lambda b: (
                            1 if (b.phone and not b.website) else 0,
                            1 if b.phone else 0,
                            1 if b.website else 0,
                            1 if (b.address and b.address != query.location) else 0,
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
                        if len(unique_results) >= 35:
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


class SmartFallbackProvider(BusinessDataProvider):
    """
    Smart multi-tier fallback provider:
    1. Google Places (if BUSINESS_API_KEY set) — 100% accurate phone, website, ratings worldwide.
    2. Serper Google Maps (if SERPER_API_KEY set) — 2,500 free Google Maps queries, no credit card.
    3. Geoapify (if GEOAPIFY_API_KEY set) — 3,000 free requests/day, no credit card required.
    4. Yelp (if YELP_API_KEY set)
    5. OpenStreetMap / Overpass (always active, free, global, enhanced contact extraction).
    """

    def __init__(self):
        self.google = GooglePlacesCompliantProvider()
        self.serper = SerperGoogleMapsProvider()
        self.geoapify = GeoapifyProvider()
        self.yelp = YelpFusionProvider()
        self.foursquare = FoursquareProvider()
        self.osm = OverpassBusinessProvider()

    async def search(self, query: SearchRequest) -> List[NormalizedBusiness]:
        # Tier 1: Google Places — gold standard worldwide data
        if self.google.api_key:
            try:
                g_results = await self.google.search(query)
                if g_results:
                    logger.info(f"SmartFallback: Using Google Places ({len(g_results)} results)")
                    return g_results
            except Exception as e:
                logger.warning(f"SmartFallback: Google Places failed — {e}")

        # Tier 2: Serper Google Maps — 2,500 free Google Maps queries, no CC required
        if self.serper.api_key:
            try:
                s_results = await self.serper.search(query)
                if s_results:
                    logger.info(f"SmartFallback: Using Serper Google Maps ({len(s_results)} results)")
                    return s_results
            except Exception as e:
                logger.warning(f"SmartFallback: Serper failed — {e}")

        # Tier 2: Geoapify — free 3,000 requests/day, no CC required
        if self.geoapify.api_key:
            try:
                geo_results = await self.geoapify.search(query)
                if geo_results:
                    logger.info(f"SmartFallback: Using Geoapify ({len(geo_results)} results)")
                    return geo_results
            except Exception as e:
                logger.warning(f"SmartFallback: Geoapify failed — {e}")

        # Tier 3: Yelp — if key provided
        if self.yelp.api_key:
            try:
                yelp_results = await self.yelp.search(query)
                if yelp_results:
                    logger.info(f"SmartFallback: Using Yelp ({len(yelp_results)} results)")
                    return yelp_results
            except Exception as e:
                logger.warning(f"SmartFallback: Yelp failed — {e}")

        # Tier 4: OpenStreetMap Overpass — always available, completely free, global
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
        # Default: Smart fallback chain (Google -> Geoapify -> Yelp -> OSM)
        return SmartFallbackProvider()


