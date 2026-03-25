from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ChainType(str, Enum):
    ETH = "eth"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVAX = "avax"
    SOLANA = "solana"  # ✅ TAMBAHKAN INI

class TokenAnalysisRequest(BaseModel):
    token_address: str = Field(..., description="Token contract address")
    token_symbol: Optional[str] = Field(None, description="Token symbol (optional)")
    chain: ChainType = Field(ChainType.ETH, description="Blockchain network")
    include_historical: bool = Field(False, description="Include historical data")
    
    @field_validator('token_address')
    def validate_address(cls, v: str, info: Dict) -> str:
        chain = info.data.get('chain')
        
        # ✅ Validasi khusus untuk Solana (base58)
        if chain == ChainType.SOLANA:
            # Solana address adalah base58, panjang 32-44 karakter
            import base58
            try:
                decoded = base58.b58decode(v)
                if len(decoded) != 32:  # Pubkey size
                    raise ValueError('Invalid Solana public key length')
                return v
            except:
                raise ValueError('Invalid Solana address format (must be base58)')
        
        # ✅ Validasi Ethereum (0x + 40 hex)
        elif chain in [ChainType.ETH, ChainType.BSC, ChainType.POLYGON]:
            if not v.startswith('0x') or len(v) != 42:
                raise ValueError('Invalid Ethereum address format')
            return v.lower()
        
        return v

class BatchAnalysisRequest(BaseModel):
    tokens: List[TokenAnalysisRequest] = Field(..., max_length=10)
    parallel: bool = Field(True, description="Run analyses in parallel")

# Response Models
class MarketData(BaseModel):
    price: float
    volume_24h: float
    liquidity: float
    market_cap: Optional[float] = None
    price_change_24h: Optional[float] = None
    volatility: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    source: str
    timestamp: datetime

class CommunityPlatform(BaseModel):
    name: str = Field(default="unknown")
    members: Optional[int] = Field(default=0)
    online: Optional[int] = Field(default=0)
    messages_per_hour: Optional[float] = Field(default=0.0)
    sentiment: Optional[float] = Field(default=0.0)
    engagement_rate: Optional[float] = Field(default=0.0)# Di dalam class CommunityPlatform, tambahkan method:
    def dict(self, *args, **kwargs):
        """Backward compatibility untuk Pydantic v1"""
        return self.model_dump(*args, **kwargs)
    
    class Config:
        extra = "allow"  # Allow extra fields

class CommunityStatus(BaseModel):
    active: bool = Field(default=False)
    score: float = Field(default=50.0, ge=0, le=100)
    platforms: Dict[str, CommunityPlatform] = Field(default_factory=dict)
    total_mentions: Optional[int] = Field(default=0)
    avg_sentiment: Optional[float] = Field(default=0.0)
    bot_percentage: Optional[float] = Field(default=0.0)
    warning_flags: List[str] = Field(default_factory=list)# Di dalam class CommunityStatus, tambahkan:
    def dict(self, *args, **kwargs):
        """Backward compatibility untuk Pydantic v1"""
        return self.model_dump(*args, **kwargs)
    
    class Config:
        extra = "allow"

        
class HolderDistribution(BaseModel):
    total_holders: int
    top_10_percentage: float
    top_50_percentage: float
    whale_count: int
    distribution_health: str
    gini_coefficient: Optional[float] = None

class WhaleActivity(BaseModel):
    whale_count: int
    total_volume_usd: float
    buy_volume_usd: float
    sell_volume_usd: float
    sentiment: str
    recent_transactions: List[Dict] = []

class ContractRisk(BaseModel):
    ownership_revoked: bool
    honeypot_risk: bool
    has_mint_function: bool
    liquidity_locked: bool
    can_pause: bool
    has_blacklist: bool
    risk_score: int
    risk_level: str

class LiquidityInfo(BaseModel):
    total_liquidity_usd: float
    locked_percentage: float
    number_of_pools: int
    main_pool: Optional[str] = None
    health: str

class PricePrediction(BaseModel):
    timeframe: str
    predicted_price: float
    predicted_change: float
    confidence: float
    direction: str

class RiskAssessment(BaseModel):
    overall_score: int
    overall_level: str
    contract_risk: ContractRisk
    liquidity_risk: Dict
    holder_risk: Dict
    social_risk: Dict
    market_risk: Dict
    risk_factors: List[Dict] = []

class Recommendation(BaseModel):
    action: str
    score: float
    position_size: str
    reasons: List[str]
    catalysts: List[Dict] = []
    risks: List[Dict] = []
    action_items: List[str] = []
    score_breakdown: Dict[str, float] = {}

class AnalysisResponse(BaseModel):
    token_address: str
    token_symbol: Optional[str] = None
    chain: str
    timestamp: datetime
    
    # Market Data
    market_data: MarketData
    
    # Community
    community_status: CommunityStatus
    
    # On-Chain
    holder_distribution: Optional[HolderDistribution] = None
    whale_activity: Optional[WhaleActivity] = None
    
    # Risk
    risk_assessment: RiskAssessment
    
    # Liquidity
    liquidity_info: Optional[LiquidityInfo] = None
    
    # Predictions
    predictions: Dict[str, PricePrediction] = {}
    
    # Final Recommendation
    recommendation: Recommendation
    
    # Metadata
    analysis_time_ms: Optional[int] = None
    data_source: str = "real"
    agents_run: Optional[int] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime

# WebSocket Models
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime

class AlertMessage(WebSocketMessage):
    type: str = "alert"
    severity: str
    message: str

# Health Check
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    agents: int
    database: str
    streaming: bool
    components: Optional[Dict[str, str]] = None