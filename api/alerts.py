from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.supabase_client import get_supabase
from core.models import AlertResponse

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)

@router.get("/history")
async def get_alert_history(
    limit: int = Query(100, ge=1, le=500),
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$")
):
    """Get historical alerts from Supabase"""
    try:
        supabase = get_supabase()
        alerts = await supabase.get_alerts(limit=limit, severity=severity)
        
        return {
            "count": len(alerts),
            "alerts": [
                {
                    "id": a["id"],
                    "type": a["alert_type"],
                    "severity": a["severity"],
                    "token_symbol": a.get("token_symbol"),
                    "message": a["message"],
                    "timestamp": a["timestamp"],
                    "is_read": a.get("is_read", False)
                }
                for a in alerts
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save")
async def save_alert(
    alert_type: str,
    severity: str,
    token_symbol: Optional[str] = None,
    message: str = "",
    data: dict = {}
):
    """Save alert to Supabase (internal use)"""
    try:
        supabase = get_supabase()
        alert_data = {
            "alert_type": alert_type,
            "severity": severity,
            "token_symbol": token_symbol,
            "message": message,
            "data": data,
            "timestamp": "now()"
        }
        result = await supabase.save_alert(alert_data)
        
        if result:
            return {"status": "success", "alert_id": result["id"]}
        else:
            raise HTTPException(status_code=500, detail="Failed to save alert")
    except Exception as e:
        logger.error(f"Failed to save alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))