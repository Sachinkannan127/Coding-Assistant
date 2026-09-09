from datetime import datetime, timezone
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FastAPI Backend for AI Code Review & Refactoring Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    Returns system status, environment mode, and current ISO timestamp.
    """
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
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
