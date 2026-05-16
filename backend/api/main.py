"""
FastAPI Backend for LLM Anonymization Visualization
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
from dotenv import load_dotenv

# Load .env file before any other imports that may need API keys
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.configs import AnonymizationConfig
from .routes.anonymization import router as anon_router
from .routes import unified  # Import unified routes
from .routes import deepseek_training  # Import deepseek training routes

# Initialize app
app = FastAPI(
    title="LLM Anonymization Visualizer",
    description="Visualization API for LLM-based text anonymization",
    version="1.0.0"
)

# Include routers - This adds routes from anonymization.py
app.include_router(anon_router)
app.include_router(unified.router)  # Add unified routes
app.include_router(deepseek_training.router)  # Add deepseek training routes

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173"
    ],
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
        "version": "1.0.0",
        "endpoints": {
            "profiles": "/api/profiles",
            "profile_detail": "/api/profiles/{profile_id}",
            "anonymization": "/api/anonymization/{profile_id}",
            "quality": "/api/quality/{profile_id}",
            "unified": {
                "sync": "/api/unified/anonymize/sync",
                "async": "/api/unified/anonymize/async",
                "task_status": "/api/unified/task/{task_id}",
                "websocket": "/api/unified/progress/{task_id}",
                "methods": "/api/unified/methods",
                "attributes": "/api/unified/attributes",
                "health": "/api/unified/health"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
