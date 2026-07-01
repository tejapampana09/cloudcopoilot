from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import analyzer, infrastructure

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "healthy"}
