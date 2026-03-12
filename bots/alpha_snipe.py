#!/usr/bin/env python3
"""
New Crypto Listing & Protocol Snipe Bot
Scans for new token listings, airdrops, and protocols
"""

import asyncio
import aiohttp
import os
import re
from datetime import datetime, timedelta
from collections import deque

# Config
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Keywords to monitor
KEYWORDS = {
    'listing': ['list', 'listing', 'launch', 'launches', 'ido', 'ieo'],
    'airdrop': ['airdrop', 'drops', 'claim', 'free tokens', 'distribution'],
    'new_protocol': ['new protocol', 'announcing', 'introducing', 'mainnet', 'testnet'],
    'trending': ['viral', 'trending', 'moon', 'pump', '100x'],
}

# Data sources to monitor
SOURCES = {
    'twitter': 'https://api.twitter.com/2/tweets/search/recent',  # Requires API key
    'coingecko_new': 'https://api.coingecko.com/api/v3/coins/list',
    'defillama': 'https://api.llama.fi/protocols',
    'token_terminal': None,  # Placeholder
}

# Track seen items to avoid duplicates
seen_listings = deque(maxlen=1000)
ALERT_COOLDOWN = 1800  # 30 minutes between similar alerts
last_alerts = {}

# Protocol knowledge base
PROTOCOL_CATEGORIES = {
    'defi': ['dex', 'lending', 'yield', 'aggregator', 'perpetual', 'options'],
    'infrastructure': ['bridge', 'oracle', 'rpc', 'indexer', 'sequencer'],
    'gaming': ['gamefi', 'nft gaming', 'play to earn'],
    'ai': ['ai', 'ml', 'neural', 'gpt'],
    'depin': ['depin', 'compute', 'storage', 'bandwidth'],
}

async def send_message(text):
    """Send Telegram message"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BASE_URL}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
            async with session.post(url, json=payload) as resp:
                return resp.status == 200
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")
        return False

class DataFetcher:
    """Fetch data from various sources"""
    
    @staticmethod
    async def get_new_coingecko_listings():
        """Get newly listed coins on CoinGecko"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get all coins
                async with session.get('https://api.coingecko.com/api/v3/coins/list') as resp:
                    coins = await resp.json()
                
                # Get markets with recent data
                async with session.get(
                    'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250'
                ) as resp:
                    markets = await resp.json()
                
                new_listings = []
                for coin in markets:
                    # Check if coin is very new (low market cap, high volume)
                    if coin.get('market_cap_rank', 999) > 200 and coin.get('total_volume', 0) > 100000:
                        new_listings.append({
                            'name': coin['name'],
                            'symbol': coin['symbol'].upper(),
                            'price': coin['current_price'],
                            'change_24h': coin.get('price_change_percentage_24h', 0),
                            'volume': coin['total_volume'],
                            'market_cap': coin.get('market_cap', 0),
                            'source': 'coingecko'
                        })
                
                return new_listings
        except Exception as e:
            print(f"[ERROR] CoinGecko: {e}")
            return []
    
    @staticmethod
    async def get_defillama_protocols():
        """Get protocols from DeFiLlama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.llama.fi/protocols') as resp:
                    protocols = await resp.json()
                
                # Filter for new/trending protocols
                trending = []
                for p in protocols:
                    tvl = p.get('tvl', 0)
                    change_1d = p.get('change_1d', 0)
                    
                    # New protocols: low TVL but growing fast
                    if tvl > 1000000 and tvl < 50000000 and change_1d > 20:
                        trending.append({
                            'name': p['name'],
                            'category': p.get('category', 'unknown'),
                            'tvl': tvl,
                            'change_1d': change_1d,
                            'chains': p.get('chains', []),
                            'source': 'defillama'
                        })
                
                return sorted(trending, key=lambda x: x['change_1d'], reverse=True)[:10]
        except Exception as e:
            print(f"[ERROR] DeFiLlama: {e}")
            return []
    
    @staticmethod
    async def get_token_unlocks():
        """Get upcoming token unlocks"""
        # Placeholder for token unlock data
        return []

class AlphaAnalyzer:
    """Analyze opportunities and generate thesis"""
    
    @staticmethod
    def categorize_protocol(name, category=None):
        """Categorize protocol by type"""
        name_lower = name.lower()
        
        for cat, keywords in PROTOCOL_CATEGORIES.items():
            if any(kw in name_lower for kw in keywords):
                return cat
            if category and any(kw in category.lower() for kw in keywords):
                return cat
        
        return 'other'
    
    @staticmethod
    def generate_thesis(listing):
        """Generate investment thesis"""
        thesis_parts = []
        
        if listing.get('change_24h', 0) > 50:
            thesis_parts.append("🔥 High momentum: +" + str(round(listing['change_24h'], 1)) + "% in 24h")
        
        if listing.get('volume', 0) > 1000000:
            thesis_parts.append("💧 Strong liquidity: $" + f"{listing['volume']/1e6:.1f}" + "M volume")
        
        if listing.get('market_cap', 0) < 10000000:
            thesis_parts.append("🎯 Low market cap: Early entry opportunity")
        
        # Protocol-specific thesis
        category = listing.get('category', '')
        if 'dex' in category.lower():
            thesis_parts.append("📊 DEX play: Capture trading fee revenue")
        elif 'lending' in category.lower():
            thesis_parts.append("🏦 Lending: Interest rate arbitrage potential")
        elif 'ai' in category.lower():
            thesis_parts.append("🤖 AI narrative: Riding the AI wave")
        elif 'depin' in category.lower():
            thesis_parts.append("🌐 DePIN: Real-world utility thesis")
        
        return "\n".join(thesis_parts) if thesis_parts else "🆕 New listing - investigate further"
    
    @staticmethod
    def how_to_capture(listing):
        """Suggest how to capture alpha"""
        suggestions = []
        
        # Based on source/type
        if listing.get('source') == 'coingecko':
            suggestions.append("💎 Buy on DEX before CEX listing")
            suggestions.append("📊 Check if liquidity is on Uniswap/PancakeSwap")
        
        if listing.get('source') == 'defillama':
            suggestions.append("🌾 Yield farm: Provide liquidity for fees")
            suggestions.append("📈 Buy token if governance value exists")
        
        # Based on stage
        if 'testnet' in listing.get('name', '').lower():
            suggestions.append("🧪 Join testnet for potential airdrop")
        
        if listing.get('market_cap', 0) < 5000000:
            suggestions.append("⚠️ High risk: Small position size only")
            suggestions.append("🔒 Use limit orders (high slippage risk)")
        
        return suggestions

class SnipeBot:
    """Main bot"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.analyzer = AlphaAnalyzer()
    
    async def send_listing_alert(self, listing):
        """Send new listing alert with thesis"""
        symbol = listing.get('symbol', listing.get('name', 'Unknown'))
        
        # Generate thesis
        thesis = self.analyzer.generate_thesis(listing)
        how_to = self.analyzer.how_to_capture(listing)
        
        message = f"""🎯 <b>NEW ALPHA DETECTED: {symbol}</b>

<b>Basic Info:</b>
• Name: {listing.get('name', 'N/A')}
• Price: ${listing.get('price', 0):,.6f}
• 24h Change: {listing.get('change_24h', 0):+.2f}%
• Volume: ${listing.get('volume', 0)/1e6:.2f}M
• Market Cap: ${listing.get('market_cap', 0)/1e6:.2f}M

<b>Source:</b> {listing.get('source', 'unknown').upper()}

<b>Investment Thesis:</b>
{thesis}

<b>How to Capture Alpha:</b>
"""
        
        for suggestion in how_to[:4]:
            message += f"• {suggestion}\n"
        
        message += f"\n⚠️ DYOR - Not financial advice\n"
        message += f"<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>"
        
        await send_message(message)
        print(f"  🎯 NEW ALPHA: {symbol}")
    
    async def scan(self):
        """Run one scan cycle"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning for new alpha...")
        
        opportunities = []
        
        # Get new CoinGecko listings
        print("  Checking CoinGecko...")
        cg_listings = await self.fetcher.get_new_coingecko_listings()
        opportunities.extend(cg_listings)
        
        # Get trending DeFi protocols
        print("  Checking DeFiLlama...")
        defi_protocols = await self.fetcher.get_defillama_protocols()
        opportunities.extend(defi_protocols)
        
        print(f"  Found {len(opportunities)} opportunities")
        
        # Send alerts for new items
        new_count = 0
        for opp in opportunities[:5]:  # Top 5
            key = f"{opp.get('name', '')}_{opp.get('symbol', '')}"
            
            if key not in seen_listings:
                seen_listings.append(key)
                await self.send_listing_alert(opp)
                new_count += 1
        
        if new_count == 0:
            print(f"  No new listings (tracking {len(seen_listings)} seen)")
    
    async def run(self):
        """Main loop"""
        print("="*60)
        print("🎯 Crypto Alpha Snipe Bot")
        print("="*60)
        print("Monitoring:")
        print("• New CoinGecko listings")
        print("• Trending DeFi protocols")
        print("• High momentum plays\n")
        
        await send_message(
            "🟢 <b>Alpha Snipe Bot Started</b>\n\n"
            "Hunting for:\n"
            "• New token listings\n"
            "• High momentum protocols\n"
            "• Early opportunities\n\n"
            "Will analyze and send thesis for each find."
        )
        
        while True:
            try:
                await self.scan()
            except Exception as e:
                print(f"[ERROR] {e}")
            
            await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    bot = SnipeBot()
    asyncio.run(bot.run())
