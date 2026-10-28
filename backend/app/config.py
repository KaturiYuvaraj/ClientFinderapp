from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/client_finder"
    DATABASE_FALLBACK_SQLITE: bool = True

    # JWT Authentication
    JWT_SECRET: str = "client_finder_jwt_secret_dev_key_2026_production_ready"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = "HS256"

    # AI Configuration
    AI_PROVIDER: str = "rule_based"  # gemini, openai, rule_based, mock
    AI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gemini-1.5-flash"

    # Business Data Provider Configuration
    # Provider options: smart (recommended), yelp, foursquare, google_places, overpass, mock
    # 'smart' = automatic Yelp → Foursquare → OSM fallback chain
    BUSINESS_API_PROVIDER: str = "smart"
    BUSINESS_API_KEY: Optional[str] = None   # Google Places API key (optional — best worldwide data)
    GEOAPIFY_API_KEY: Optional[str] = None   # Geoapify API key — free 3,000/day at geoapify.com (no credit card)
    YELP_API_KEY: Optional[str] = None        # Yelp Fusion API key (optional)
    FOURSQUARE_API_KEY: Optional[str] = None  # Foursquare API key (deprecated)

    # Security & CORS
    FRONTEND_URL: str = "http://localhost:5173"
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
