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
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "environment": settings.environment,
            "version": "1.0.0"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )

