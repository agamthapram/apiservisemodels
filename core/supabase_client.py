"""
Supabase Client untuk Vercel
Menggantikan PostgreSQL lokal dengan Supabase
"""

import os
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Client untuk interaksi dengan Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Supabase client initialized")
    
    # ========== TOKENS ==========
    
    async def get_token_by_address(self, address: str, chain: str = "eth") -> Optional[Dict]:
        """Get token by address"""
        try:
            result = self.client.table("tokens") \
                .select("*") \
                .eq("address", address) \
                .eq("chain", chain) \
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get token: {e}")
            return None
    
    async def create_token(self, token_data: Dict) -> Optional[Dict]:
        """Create new token"""
        try:
            result = self.client.table("tokens").insert(token_data).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to create token: {e}")
            return None
    
    async def get_or_create_token(self, address: str, symbol: str, name: str, chain: str) -> Dict:
        """Get existing token or create new one"""
        token = await self.get_token_by_address(address, chain)
        if token:
            return token
        
        token_data = {
            "address": address,
            "symbol": symbol,
            "name": name,
            "chain": chain,
            "created_at": "now()"
        }
        return await self.create_token(token_data)
    
    # ========== ANALYSIS RESULTS ==========
    
    async def save_analysis(self, analysis_data: Dict) -> Optional[Dict]:
        """Save analysis result to Supabase"""
        try:
            result = self.client.table("analysis_results").insert(analysis_data).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to save analysis: {e}")
            return None
    
    async def get_analysis_history(self, token_id: int, limit: int = 10) -> List[Dict]:
        """Get analysis history for a token"""
        try:
            result = self.client.table("analysis_results") \
                .select("*") \
                .eq("token_id", token_id) \
                .order("timestamp", desc=True) \
                .limit(limit) \
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []
    
    # ========== ALERTS ==========
    
    async def save_alert(self, alert_data: Dict) -> Optional[Dict]:
        """Save alert to Supabase"""
        try:
            result = self.client.table("alerts").insert(alert_data).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to save alert: {e}")
            return None
    
    async def get_alerts(self, limit: int = 100, severity: Optional[str] = None) -> List[Dict]:
        """Get recent alerts"""
        try:
            query = self.client.table("alerts") \
                .select("*") \
                .order("timestamp", desc=True) \
                .limit(limit)
            
            if severity:
                query = query.eq("severity", severity)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []
    
    async def mark_alert_read(self, alert_id: int) -> bool:
        """Mark alert as read"""
        try:
            result = self.client.table("alerts") \
                .update({"is_read": True}) \
                .eq("id", alert_id) \
                .execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Failed to mark alert read: {e}")
            return False

# Singleton instance
_supabase = None

def get_supabase() -> SupabaseClient:
    """Get Supabase client instance"""
    global _supabase
    if _supabase is None:
        _supabase = SupabaseClient()
    return _supabase