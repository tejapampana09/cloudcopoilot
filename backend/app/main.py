from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import logging

# Define structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "filename": record.filename,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging():
    root = logging.getLogger()
    # Clear existing handlers to avoid duplicates
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)

setup_logging()
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.routers import analyzer, infrastructure, auth
from app.utils.database import init_db
from app.utils.rate_limiter import RateLimitMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please contact administrator."}
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self' http://localhost:8000 http://localhost:5173 http://localhost:5174 http://localhost:3000; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.on_event("shutdown")
def on_shutdown():
    logger.info("Service shutting down. Initiating repository cleanup...")
    import shutil
    temp_dir = settings.TEMP_CLONE_DIR
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    logger.info("Cleanup completed on shutdown.")

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
            except Exception as e:
                logger.error(f"Error in repository cleanup worker loop: {e}")
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
    except Exception as e:
        logger.error(f"Database healthcheck failed: {e}")

    if not db_healthy:
        return {"status": "unhealthy", "reason": "Database connection failed."}

    return {
        "status": "healthy",
        "database": "connected",
        "openai_api_configured": openai_configured
    }

@app.get("/health/liveness")
async def liveness():
    return {"status": "alive"}

@app.get("/health/readiness")
async def readiness():
    # Observability check: Check database writeability
    db_healthy = False
    try:
        from app.utils.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_healthy = True
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")

    if not db_healthy:
        return JSONResponse(
            status_code=503,
            content={"status": "unready", "reason": "Database connection offline"}
        )
    return {"status": "ready"}
