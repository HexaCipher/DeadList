"""
DeadList — Memory Forensics & Malware Detection Platform
FastAPI Application Entry Point

The process that's dead to the system. Found alive by DeadList.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.database import init_db
from routers.upload import router as upload_router
from routers.analysis import router as analysis_router
from routers.ws import router as ws_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize DB on startup."""
    logger.info("☠ DeadList starting up...")
    logger.info(f"  Mock mode: {settings.MOCK_MODE}")
    logger.info(f"  Upload dir: {settings.UPLOAD_DIR}")
    logger.info(f"  Database: {settings.DATABASE_URL}")

    # Initialize database tables
    await init_db()
    logger.info("  Database initialized ✓")

    logger.info("☠ DeadList is ready — The process that's dead to the system. Found alive by DeadList.")
    yield
    logger.info("☠ DeadList shutting down...")


# Create FastAPI app
app = FastAPI(
    title="DeadList",
    description="Memory Forensics & Malware Detection Platform powered by Volatility 3",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(ws_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "DeadList",
        "tagline": "The process that's dead to the system. Found alive by DeadList.",
        "version": "1.0.0",
        "docs": "/docs",
    }
