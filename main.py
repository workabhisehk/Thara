"""
FastAPI application entry point.
Provides REST API endpoints for webhooks and health checks.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from config import settings

app = FastAPI(
    title="AI Productivity Agent API",
    description="API for AI Productivity Agent with Telegram and Calendar integration",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Productivity Agent API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity check."""
    from database.connection import check_connection_health
    
    health_status = {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0",
        "checks": {
            "api": "ok",
            "database": "unknown"
        }
    }
    
    # Check database connectivity with retry logic
    is_healthy = await check_connection_health()
    if is_healthy:
        health_status["checks"]["database"] = "ok"
    else:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = "error: connection failed"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=health_status)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )

