from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.routers import analyzer, infrastructure, auth
from app.utils.database import init_db
from app.utils.rate_limiter import RateLimitMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

def start_cleanup_scheduler():
    import threading
    import time
    import shutil
    def cleanup_worker():
        while True:
            try:
                temp_dir = settings.TEMP_CLONE_DIR
                if os.path.exists(temp_dir):
                    now = time.time()
                    for item in os.listdir(temp_dir):
                        item_path = os.path.join(temp_dir, item)
                        if os.path.isdir(item_path):
                            mtime = os.path.getmtime(item_path)
                            if now - mtime > 3600:
                                shutil.rmtree(item_path, ignore_errors=True)
            except Exception:
                pass
            time.sleep(300)
            
    t = threading.Thread(target=cleanup_worker, daemon=True)
    t.start()

# Initialize SQLite database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()
    start_cleanup_scheduler()

# Restrict CORS origins: browsers reject allow_origins=["*"] when allow_credentials=True
origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
if "*" in origins:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

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
    auth.router,
    prefix=settings.API_V1_STR,
    tags=["auth"]
)

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
        from app.utils.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_healthy = True
    except Exception:
        pass

    if not db_healthy:
        return {"status": "unhealthy", "reason": "PostgreSQL database connection failed."}

    return {
        "status": "healthy",
        "database": "connected",
        "openai_api_configured": openai_configured
    }
