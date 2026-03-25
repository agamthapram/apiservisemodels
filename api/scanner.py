from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_providers.dex_provider import DEXProvider
from data_providers.audit_provider import AuditProvider

router = APIRouter(prefix="/api/v1/discover", tags=["scanner"])
logger = logging.getLogger(__name__)

dex = DEXProvider()
audit = AuditProvider()

@router.get("/new-tokens")
async def discover_new_tokens(
    chain: str = Query("solana", regex="^(eth|solana)$"),
    min_liquidity: float = Query(10000, ge=0),
    limit: int = Query(20, ge=1, le=50)
):
    """Scan for new tokens (lightweight, no ML)"""
    try:
        # Get new pairs from DexScreener
        raw_tokens = await dex.get_new_pairs(chain, limit=limit * 2)
        
        # Filter and enrich
        tokens = []
        for token in raw_tokens[:limit]:
            # Filter liquidity
            liquidity = token.get("liquidity_usd", 0)
            if liquidity < min_liquidity:
                continue
            
            # Add quality score (lightweight calculation)
            quality_score = _calculate_quality_score(token)
            token["quality_score"] = quality_score
            
            # Quick security check (optional, can be slow)
            # if quality_score > 60:
            #     audit_result = await audit.check_token_security(token["address"], chain)
            #     token["security"] = audit_result
            
            tokens.append(token)
        
        # Sort by quality score
        tokens.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        
        return {
            "chain": chain,
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(tokens),
            "tokens": tokens[:limit]
        }
        
    except Exception as e:
        logger.error(f"Scanner failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_quality_score(token: dict) -> int:
    """Calculate simple quality score (0-100)"""
    score = 50
    
    # Liquidity score
    liquidity = token.get("liquidity_usd", 0)
    if liquidity > 1_000_000:
        score += 25
    elif liquidity > 500_000:
        score += 20
    elif liquidity > 100_000:
        score += 15
    elif liquidity > 50_000:
        score += 10
    elif liquidity < 10_000:
        score -= 20
    
    # Volume score
    volume = token.get("volume_24h", 0)
    if volume > 500_000:
        score += 15
    elif volume > 100_000:
        score += 10
    elif volume > 50_000:
        score += 5
    elif volume < 10_000:
        score -= 10
    
    # Age score (newer is better)
    age = token.get("age_hours", 48)
    if age < 6:
        score += 15
    elif age < 24:
        score += 5
    elif age > 72:
        score -= 10
    
    return max(0, min(100, score))