from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.db.session import init_db
from app.db.mongodb import connect_to_mongo, close_mongo_connection

# Import all API routers
from app.api.cases import router as cases_router
from app.api.evidence import router as evidence_router
from app.api.connectors import router as connectors_router
from app.api.analysis import router as analysis_router
from app.api.challenge import router as challenge_router
from app.api.decisions import router as decisions_router
from app.api.reviews import router as reviews_router
from app.api.demo import router as demo_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting VERDICT AI Backend...")
    # Initialize MongoDB connection & indexes
    await connect_to_mongo()
    # Initialize SQL fallback tables
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"SQL init bypassed (using MongoDB): {e}")
    yield
    logger.info("Shutting down VERDICT AI Backend...")
    await close_mongo_connection()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="VERDICT AI - Enterprise Multi-Source Evidence Ingestion, MongoDB, ML Anomaly, RAG, Contradiction Engine & Deterministic Decision Gate",
    lifespan=lifespan
)

# CORS configuration for Developer 1 React UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(cases_router)
app.include_router(evidence_router)
app.include_router(connectors_router)
app.include_router(analysis_router)
app.include_router(challenge_router)
app.include_router(decisions_router)
app.include_router(reviews_router)
app.include_router(demo_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "MongoDB",
        "mongodb_url": settings.MONGODB_URL,
        "decision_gate": "OPERATIONAL",
        "llm_provider": "Groq",
        "llm_model": settings.GROQ_MODEL
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "VERDICT AI Backend is active with MongoDB & Groq.",
        "docs_url": "/docs",
        "demo_seed_endpoint": "/api/demo/seed-tx92831"
    }
