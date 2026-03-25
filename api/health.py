from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": "vercel",
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }