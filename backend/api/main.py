"""
FastAPI Backend for LLM Anonymization Visualization
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.configs import AnonymizationConfig
from .routes.anonymization import router as anon_router

# Initialize app
app = FastAPI(
    title="LLM Anonymization Visualizer",
    description="Visualization API for LLM-based text anonymization",
    version="1.0.0"
)

# Include routers - This adds routes from anonymization.py
app.include_router(anon_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
profiles_cache = {}


@app.on_event("startup")
async def startup_event():
    """Load initial data on startup"""
    print("🚀 Starting LLM Anonymization API...")


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "healthy",
        "message": "LLM Anonymization Visualizer API",
        "endpoints": {
            "profiles": "/api/profiles",
            "profile_detail": "/api/profiles/{profile_id}",
            "anonymization": "/api/anonymization/{profile_id}",
            "quality": "/api/quality/{profile_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
