import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.db.mongodb import db_manager, connect_mongodb
from backend.app.api import review_router, sandbox_router, explain_router

# Configure application-level logging to appear in the terminal
# force=True ensures our config takes effect even if uvicorn already set up handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:     %(name)s - %(message)s",
    force=True
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Handles application startup database connection initialization and graceful shutdown cleanup.
    """
    print("INFO:     Connecting to MongoDB...")
    try:
        conn_res = await connect_mongodb()
        print(f"INFO:     ✅ MongoDB connected (Database: '{conn_res['database']}', Status: '{conn_res['status']}')")
    except Exception as e:
        print(f"WARNING:  ⚠️ MongoDB connection failed on startup: {e}")
    
    yield
    
    logger.info("Application Shutdown: Closing database connection...")
    await db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FastAPI Backend for AI Code Review & Refactoring Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

from backend.app.middleware import SecurityHeadersMiddleware, RateLimiterMiddleware

# Security Headers & Rate Limiter Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimiterMiddleware, rate_limit_per_minute=settings.RATE_LIMIT_PER_MINUTE)

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
app.include_router(sandbox_router, prefix="/api", tags=["Code Sandbox"])
app.include_router(explain_router, prefix="/api", tags=["Code Explanation"])


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
