from fastapi import APIRouter, Request, HTTPException
import httpx
import os
import logging

router = APIRouter(prefix="/api/v1/token", tags=["analysis"])
logger = logging.getLogger(__name__)

RAILWAY_API_URL = os.getenv("RAILWAY_API_URL", "https://crypto-ai.up.railway.app")

@router.post("/analyze")
async def proxy_analyze(request: Request):
    """Proxy to Railway for heavy analysis"""
    try:
        body = await request.body()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{RAILWAY_API_URL}/api/v1/token/analyze",
                content=body,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"Railway returned {response.status_code}: {response.text[:200]}")
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()
            
    except httpx.TimeoutException:
        logger.error("Timeout connecting to Railway")
        raise HTTPException(status_code=504, detail="Analysis timeout")
    except Exception as e:
        logger.error(f"Proxy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))