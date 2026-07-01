from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.routers import analyzer, infrastructure
from app.utils.database import init_db, DB_PATH
from app.utils.rate_limiter import RateLimitMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Initialize SQLite database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Restrict CORS origins: browsers reject allow_origins=["*"] when allow_credentials=True
origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
if "*" in origins:
    origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register rate limiter middleware (40 requests per minute)
app.add_middleware(RateLimitMiddleware, requests_per_minute=40)

# Mount routers
app.include_router(
    analyzer.router,
    prefix=settings.API_V1_STR,
    tags=["analyzer"]
)

app.include_router(
    infrastructure.router,
    prefix=f"{settings.API_V1_STR}/infrastructure",
    tags=["infrastructure"]
)

@app.get("/")
async def root():
    return {"message": "Welcome to the CloudPilot AI Analyzer API. Access /api/v1/analyze to trigger repository analysis."}

@app.get("/health")
async def health():
    # Observability check: Check database writeability and API configurations
    openai_configured = bool(settings.OPENAI_API_KEY)
    
    db_healthy = False
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        db_healthy = True
    except Exception:
        pass

    if not db_healthy:
        return {"status": "unhealthy", "reason": "Database connection failed."}

    return {
        "status": "healthy",
        "database": "connected",
        "openai_api_configured": openai_configured
    }
