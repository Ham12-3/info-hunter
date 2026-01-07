"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import include_routes

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Info Hunter - Aggregates and searches programming knowledge and code snippets"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
include_routes(app)


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {
        "status": "healthy",
        "service": "info-hunter-api",
        "version": settings.api_version
    }

