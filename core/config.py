from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class ChainType(str, Enum):
    ETH = "eth"
    SOLANA = "solana"

class TokenAnalysisRequest(BaseModel):
    token_address: str
    token_symbol: Optional[str] = None
    chain: ChainType = ChainType.ETH

class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    token_symbol: Optional[str]
    message: str
    timestamp: datetime
    is_read: bool

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: str