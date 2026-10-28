import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database.connection import init_db
from app.routers import auth_router, leads_router, ai_router, dashboard_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("client_finder.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info("Initializing AI Client Finder database tables...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    yield
    # Shutdown
    logger.info("AI Client Finder backend shutting down...")

app = FastAPI(
    title="AI Client Finder API",
    description="Authorized B2B Lead Discovery, AI Opportunity Analysis, and Lead Management Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
# Allow local dev servers and Chrome extension origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_origin_regex=r"^(chrome-extension://.*|http://localhost:\d+|http://127\.0\.0\.1:\d+|http://192\.168\.\d+\.\d+(:\d+)?|http://10\.0\.2\.2(:\d+)?)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please try again later."}
    )

# Include Routers
app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(ai_router)
app.include_router(dashboard_router)

@app.get("/", tags=["General"])
def root():
    return {
        "name": "AI Client Finder API",
        "status": "operational",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health", tags=["General"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "business_provider": settings.BUSINESS_API_PROVIDER,
        "ai_provider": settings.AI_PROVIDER
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

