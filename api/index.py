from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging
from mangum import Mangum

from . import health, alerts, scanner, analyze

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Crypto AI Light API",
    description="Lightweight API for crypto analysis (proxy to Railway)",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(alerts.router)
app.include_router(scanner.router)
app.include_router(analyze.router)

@app.get("/")
async def root():
    return {
        "name": "Crypto AI Light API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "alerts": "GET /api/v1/alerts/history",
            "new_tokens": "GET /api/v1/discover/new-tokens?chain=solana",
            "analyze": "POST /api/v1/token/analyze (proxy to Railway)"
        }
    }

# Handler untuk Vercel
handler = Mangum(app)