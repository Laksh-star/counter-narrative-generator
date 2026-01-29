"""
FastAPI application for Counter-Narrative Generator

This service exposes the Counter-Narrative Generator as a REST API
with WebSocket support for streaming progress updates.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

from api.routes import router
from src.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("🚀 Starting Counter-Narrative Generator API")
    print(f"📊 Loading vector store from: {config.chunks_path}")

    # Verify API key
    if not config.models.api_key:
        print("⚠️  WARNING: OPENROUTER_API_KEY not configured!")
    else:
        print("✅ OpenRouter API key configured")

    # Initialize vector store (lazy loading handled in routes)
    print("✅ API ready to accept requests")

    yield

    # Shutdown
    print("👋 Shutting down Counter-Narrative Generator API")


# Create FastAPI app
app = FastAPI(
    title="Counter-Narrative Generator API",
    description="API for mining contrarian perspectives from Lenny's Podcast",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Counter-Narrative Generator API",
        "version": "1.0.0",
        "description": "Mine contrarian perspectives from Lenny's Podcast",
        "docs": "/docs",
        "health": "/api/health",
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
        },
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🌐 Starting server on {host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level="info",
    )
