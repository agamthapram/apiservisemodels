from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Numeric, JSON, BigInteger, Text, Index
from sqlalchemy.ext.declarative import declarative_base  # <-- Ini yang hilang
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from core.config import config

# Database connection
DATABASE_URL = config.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()  # <-- Ini sekarang sudah terdefinisi

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(255), unique=True, index=True, nullable=False)
    symbol = Column(String(50))
    name = Column(String(255))
    chain = Column(String(50), default="eth")
    decimals = Column(Integer)
    total_supply = Column(Numeric(78, 0))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Contract info
    owner_address = Column(String(255))
    is_verified = Column(Boolean, default=False)
    has_source_code = Column(Boolean, default=False)
    
    # Social links
    website = Column(String(255))
    twitter = Column(String(255))
    telegram = Column(String(255))
    discord = Column(String(255))
    github = Column(String(255))

class TokenPrice(Base):
    __tablename__ = "token_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    price = Column(Numeric(38, 18))
    volume_24h = Column(Numeric(38, 2))
    market_cap = Column(Numeric(38, 2))
    liquidity = Column(Numeric(38, 2))
    source = Column(String(50))  # exchange name
    
    __table_args__ = (
        Index('idx_token_time', 'token_id', 'timestamp'),
    )

class TokenMetric(Base):
    __tablename__ = "token_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Holder metrics
    holder_count = Column(Integer)
    top_10_percentage = Column(Numeric(5, 2))
    top_50_percentage = Column(Numeric(5, 2))
    whale_count = Column(Integer)
    
    # Transaction metrics
    tx_count_24h = Column(Integer)
    unique_senders_24h = Column(Integer)
    unique_receivers_24h = Column(Integer)
    
    # Social metrics
    twitter_mentions_24h = Column(Integer)
    twitter_sentiment = Column(Numeric(5, 2))
    discord_messages_24h = Column(Integer)
    telegram_messages_24h = Column(Integer)
    
    # Technical metrics
    rsi = Column(Numeric(5, 2))
    macd = Column(Numeric(38, 8))
    volatility_24h = Column(Numeric(10, 4))

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    prediction_type = Column(String(20))  # '1h', '24h', '7d', '30d'
    predicted_price = Column(Numeric(38, 18))
    predicted_change = Column(Numeric(10, 4))
    confidence = Column(Numeric(5, 2))
    model_version = Column(String(50))
    features_used = Column(JSON)

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Scores
    final_score = Column(Integer)
    technical_score = Column(Integer)
    sentiment_score = Column(Integer)
    community_score = Column(Integer)
    onchain_score = Column(Integer)
    risk_score = Column(Integer)
    
    # Recommendation
    action = Column(String(20))
    position_size = Column(String(50))
    
    # Full results (JSON)
    agent_results = Column(JSON)
    recommendation = Column(JSON)
    
    # Metadata
    analysis_time_ms = Column(Integer)
    data_source = Column(String(50))

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    alert_type = Column(String(50))  # 'whale', 'new_token', 'price_spike', 'risk'
    severity = Column(String(20))  # 'low', 'medium', 'high', 'critical'
    token_id = Column(Integer, index=True)
    token_symbol = Column(String(50))
    message = Column(Text)
    data = Column(JSON)
    is_read = Column(Boolean, default=False)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()