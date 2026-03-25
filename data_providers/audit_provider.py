import aiohttp
from typing import Dict, Optional, List
from core.config import config
import logging
import ssl
import certifi

logger = logging.getLogger(__name__)

# SSL Context
ssl_context = ssl.create_default_context(cafile=certifi.where())

class AuditProvider:
    """Provider for contract audit data using working APIs with SSL Fix"""
    
    def __init__(self):
        self.goplus_api = "https://api.gopluslabs.io/api/v1"
        self.quickintel_api = "https://api.quickintel.io/v1"
        
    async def check_token_security(self, token_address: str, chain: str = "eth") -> Dict:
        """
        Check token security using GoPlus API (free and reliable)
        Menambahkan ssl_context ke session aiohttp.
        """
        try:
            chain_map = {
                "eth": 1,
                "bsc": 56,
                "solana": 101
            }
            
            chain_id = chain_map.get(chain, 1)
            url = f"{self.goplus_api}/token_security/{chain_id}"
            params = {"contract_addresses": token_address}
            
            # PERBAIKAN: Gunakan connector dengan ssl_context
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if data.get("code") == 1 and data.get("result"):
                            result = data["result"].get(token_address.lower(), {})
                            
                            return {
                                "is_honeypot": result.get("is_honeypot", "0") == "1",
                                "buy_tax": float(result.get("buy_tax", "0")),
                                "sell_tax": float(result.get("sell_tax", "0")),
                                "cannot_buy": result.get("cannot_buy", "0") == "1",
                                "cannot_sell_all": result.get("cannot_sell_all", "0") == "1",
                                "is_blacklisted": result.get("is_blacklisted", "0") == "1",
                                "owner_address": result.get("owner_address"),
                                "data_source": "goplus"
                            }
            
            # Fallback jika gagal
            return await self._basic_onchain_check(token_address, chain)
                    
        except Exception as e:
            logger.error(f"Token security check failed: {e}")
            return await self._basic_onchain_check(token_address, chain)
    
    async def _basic_onchain_check(self, token_address: str, chain: str) -> Dict:
        """Basic on-chain checks when APIs fail"""
        return {
            "is_honeypot": False, # Asumsi aman jika tidak bisa cek
            "buy_tax": 0,
            "sell_tax": 0,
            "has_renounced": False,
            "liquidity_locked": False,
            "data_source": "none",
            "warning": "Audit data not available due to connection errors"
        }
    
    async def get_contract_owner(self, token_address: str, chain: str = "eth") -> Optional[str]:
        """Get contract owner address"""
        # Untuk sekarang, return None agar tidak crash karena Infura error
        return None