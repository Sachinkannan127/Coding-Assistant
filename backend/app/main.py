import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.db.mongodb import db_manager
from backend.app.api import review_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Handles startup database connection initialization and graceful shutdown cleanup.
    """
    logger.info("Initializing application resources...")
    try:
        await db_manager.connect()
    except Exception as e:
        logger.warning(f"Could not connect to MongoDB on startup: {e}")
    
    yield
    
    logger.info("Shutting down application resources...")
    await db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FastAPI Backend for AI Code Review & Refactoring Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(review_router, prefix="/api", tags=["Code Reviews"])


@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["System"]
)
async def root():
    """
    Landing Page Endpoint
    Returns welcome message, API name, version, and links to API documentation and health check.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["System"]
)
async def health_check():
    """
    System Health Check Endpoint
    Returns system status, environment mode, current ISO timestamp, and MongoDB connectivity.
    """
    db_connected = await db_manager.ping()
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_connected else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
