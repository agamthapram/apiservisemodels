"""
DEX Provider - Mengambil data real dari berbagai DEX via DexScreener
Support: Solana (Pump.fun, Raydium, Orca, Meteora) dan Ethereum (Uniswap)
FITUR:
- Auto cache untuk mengurangi request
- Error handling lengkap
- Support harga sangat kecil (hingga 10 desimal)
- Data real-time dari DexScreener
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import ssl
import certifi
import time

logger = logging.getLogger(__name__)

ssl_context = ssl.create_default_context(cafile=certifi.where())

class DEXProvider:
    """Provider untuk mengambil data REAL dari DEX via DexScreener"""
    
    def __init__(self):
        # DexScreener API (GRATIS, TANPA API KEY)
        self.dexscreener_api = "https://api.dexscreener.com/latest/dex"
        
        # Cache untuk mengurangi request
        self.cache = {}
        self.cache_ttl = 60  # detik
        
        # Chain mapping
        self.chain_map = {
            "eth": "ethereum",
            "solana": "solana",
            "bsc": "bsc",
            "polygon": "polygon",
            "arbitrum": "arbitrum",
            "avax": "avalanche",
            "base": "base"
        }
        
        logger.info("DEXProvider initialized with DexScreener API")

    async def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request dengan error handling"""
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(url, params=params, timeout=15) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        logger.warning(f"Rate limited by DexScreener. Waiting...")
                        await asyncio.sleep(2)
                        return None
                    else:
                        logger.debug(f"HTTP {resp.status} from {url}")
                        return None
        except asyncio.TimeoutError:
            logger.debug(f"Timeout for {url}")
            return None
        except Exception as e:
            logger.debug(f"Request failed: {e}")
            return None

    async def get_token_info(self, token_address: str, chain: str = "solana") -> Optional[Dict]:
        """
        Get complete token information from DexScreener
        Returns: {
            'price_usd': float,
            'price_native': float,
            'liquidity_usd': float,
            'volume_24h': float,
            'fdv': float,
            'market_cap': float,
            'dex': str,
            'pair_address': str,
            'created_at': int,
            'price_change_24h': float,
            'txns_24h': dict,
            'info': dict
        }
        """
        cache_key = f"token_info_{chain}_{token_address}"
        
        # Cek cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                return cached['data']
        
        try:
            # Panggil DexScreener API
            url = f"{self.dexscreener_api}/tokens/{token_address}"
            data = await self._make_request(url)
            
            if not data or 'pairs' not in data or not data['pairs']:
                logger.debug(f"No data found for token {token_address}")
                return None
            
            # Filter pairs berdasarkan chain
            chain_name = self.chain_map.get(chain, chain)
            pairs = [p for p in data['pairs'] if p['chainId'] == chain_name]
            
            if not pairs:
                logger.debug(f"No pairs found on {chain} for token {token_address}")
                return None
            
            # Ambil pair dengan liquidity tertinggi
            best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))
            
            # Parse response
            result = {
                'price_usd': float(best_pair.get('priceUsd', 0)),
                'price_native': float(best_pair.get('priceNative', 0)),
                'liquidity_usd': float(best_pair.get('liquidity', {}).get('usd', 0)),
                'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                'fdv': float(best_pair.get('fdv', 0)),
                'market_cap': float(best_pair.get('marketCap', 0)),
                'dex': best_pair.get('dexId', 'unknown'),
                'pair_address': best_pair.get('pairAddress', ''),
                'pair_url': best_pair.get('url', ''),
                'created_at': best_pair.get('pairCreatedAt', 0),
                'price_change_24h': float(best_pair.get('priceChange', {}).get('h24', 0)),
                'txns_24h': best_pair.get('txns', {}).get('h24', {}),
                'base_token': {
                    'address': best_pair.get('baseToken', {}).get('address', ''),
                    'name': best_pair.get('baseToken', {}).get('name', ''),
                    'symbol': best_pair.get('baseToken', {}).get('symbol', '')
                },
                'quote_token': {
                    'address': best_pair.get('quoteToken', {}).get('address', ''),
                    'name': best_pair.get('quoteToken', {}).get('name', ''),
                    'symbol': best_pair.get('quoteToken', {}).get('symbol', '')
                },
                'info': best_pair.get('info', {}),
                'data_source': 'dexscreener'
            }
            
            # Simpan ke cache
            self.cache[cache_key] = {
                'timestamp': time.time(),
                'data': result
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get token info from DexScreener: {e}")
            return None

    async def get_token_price(self, token_address: str, chain: str = "solana") -> Optional[float]:
        """Get current token price in USD"""
        info = await self.get_token_info(token_address, chain)
        return info['price_usd'] if info else None

    async def get_new_pairs(self, chain: str = "solana", limit: int = 50) -> List[Dict]:
        """
        Get newly created pairs from DexScreener
        Returns list of tokens with their info
        """
        cache_key = f"new_pairs_{chain}"
        
        # Cek cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < 120:  # 2 menit cache
                return cached['data']
        
        try:
            chain_name = self.chain_map.get(chain, chain)
            
            # DexScreener tidak punya endpoint khusus new pairs,
            # jadi kita cari berdasarkan keyword
            url = f"{self.dexscreener_api}/search"
            params = {"q": chain_name}
            
            data = await self._make_request(url, params)
            
            if not data or 'pairs' not in data:
                return []
            
            # Filter dan sort by creation time
            pairs = []
            now = time.time() * 1000  # milliseconds
            
            for pair in data['pairs']:
                if pair['chainId'] != chain_name:
                    continue
                    
                created_at = pair.get('pairCreatedAt', 0)
                age_hours = (now - created_at) / (1000 * 3600) if created_at else 999
                
                # Hanya ambil yang dibuat dalam 7 hari terakhir
                if age_hours <= 168:  # 7 hari
                    pairs.append({
                        'address': pair['baseToken']['address'],
                        'symbol': pair['baseToken']['symbol'],
                        'name': pair['baseToken']['name'],
                        'chain': chain,
                        'dex': pair.get('dexId', 'unknown'),
                        'created_at': created_at,
                        'age_hours': age_hours,
                        'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0)),
                        'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                        'price_usd': float(pair.get('priceUsd', 0)),
                        'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                        'fdv': float(pair.get('fdv', 0)),
                        'market_cap': float(pair.get('marketCap', 0)),
                        'data_source': 'dexscreener'
                    })
            
            # Sort by creation time (newest first)
            pairs.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Simpan ke cache
            self.cache[cache_key] = {
                'timestamp': time.time(),
                'data': pairs[:limit]
            }
            
            logger.info(f"Found {len(pairs[:limit])} new pairs on {chain}")
            return pairs[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get new pairs: {e}")
            return []

    async def search_tokens(self, query: str, chain: str = None) -> List[Dict]:
        """
        Search tokens by name or symbol
        """
        try:
            url = f"{self.dexscreener_api}/search"
            params = {"q": query}
            
            data = await self._make_request(url, params)
            
            if not data or 'pairs' not in data:
                return []
            
            results = []
            for pair in data['pairs']:
                # Filter by chain if specified
                if chain and pair['chainId'] != self.chain_map.get(chain, chain):
                    continue
                    
                results.append({
                    'address': pair['baseToken']['address'],
                    'symbol': pair['baseToken']['symbol'],
                    'name': pair['baseToken']['name'],
                    'chain': pair['chainId'],
                    'price_usd': float(pair.get('priceUsd', 0)),
                    'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0)),
                    'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                    'dex': pair.get('dexId', 'unknown'),
                    'created_at': pair.get('pairCreatedAt', 0)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def close(self):
        """Cleanup"""
        self.cache.clear()
        logger.info("DEXProvider closed")