#!/usr/bin/env python3
"""
Big Move Alert Bot
Detects significant price movements in stocks and crypto
with supporting evidence from news and social media
"""

import asyncio
import aiohttp
import os
from datetime import datetime, timedelta
import json

# Config
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Alert thresholds
THRESHOLDS = {
    'crypto': {
        'major': 0.05,      # 5% for BTC, ETH
        'mid': 0.08,        # 8% for mid-caps
        'alt': 0.15,        # 15% for alts
    },
    'stock': {
        'blue_chip': 0.03,  # 3% for SPY, QQQ, AAPL, etc
        'growth': 0.05,     # 5% for high-beta
        'meme': 0.10,       # 10% for meme stocks
    }
}

# Assets to monitor
ASSETS = {
    'crypto': {
        'BTC': 'bitcoin',
        'ETH': 'ethereum', 
        'SOL': 'solana',
        'BNB': 'binancecoin',
        'XRP': 'ripple',
        'DOGE': 'dogecoin',
        'ADA': 'cardano',
        'AVAX': 'avalanche-2',
        'LINK': 'chainlink',
        'PEPE': 'pepe',
    },
    'stocks': {
        'SPY': 'SPDR S&P 500 ETF',
        'QQQ': 'Invesco QQQ Trust',
        'AAPL': 'Apple Inc.',
        'TSLA': 'Tesla Inc.',
        'NVDA': 'NVIDIA Corporation',
        'MSFT': 'Microsoft Corporation',
        'AMZN': 'Amazon.com Inc.',
        'GOOGL': 'Alphabet Inc.',
        'META': 'Meta Platforms Inc.',
        'GME': 'GameStop Corp.',
        'AMC': 'AMC Entertainment',
    }
}

# Price tracking
price_history = {}
ALERT_COOLDOWN = 3600  # 1 hour between alerts for same asset
last_alerts = {}

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

async def get_crypto_prices():
    """Fetch crypto prices from CoinGecko"""
    try:
        ids = ','.join(ASSETS['crypto'].values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                
        prices = {}
        for symbol, cid in ASSETS['crypto'].items():
            if cid in data:
                prices[symbol] = {
                    'price': data[cid]['usd'],
                    'change_24h': data[cid].get('usd_24h_change', 0),
                    'type': 'crypto'
                }
        return prices
    except Exception as e:
        print(f"[ERROR] Crypto fetch: {e}")
        return {}

async def get_stock_prices():
    """Fetch stock prices (using Yahoo Finance proxy or similar)"""
    # Note: In production, use a proper stock API like Alpha Vantage, Finnhub, or Polygon
    # This is a placeholder implementation
    stocks = {}
    for symbol in ASSETS['stocks'].keys():
        # Mock data for now - replace with real API
        stocks[symbol] = {
            'price': 0,  # Would fetch real price
            'change_24h': 0,  # Would fetch real change
            'type': 'stock'
        }
    return stocks

async def search_news(query):
    """Search for news related to asset"""
    # Placeholder for news API integration
    # Could use: NewsAPI, GDELT, or web scraping
    return []

def check_big_move(symbol, data):
    """Check if price movement exceeds threshold"""
    change = abs(data['change_24h'])
    
    # Determine threshold based on asset type
    if data['type'] == 'crypto':
        if symbol in ['BTC', 'ETH']:
            threshold = THRESHOLDS['crypto']['major']
        elif symbol in ['SOL', 'BNB', 'XRP']:
            threshold = THRESHOLDS['crypto']['mid']
        else:
            threshold = THRESHOLDS['crypto']['alt']
    else:  # stock
        if symbol in ['GME', 'AMC']:
            threshold = THRESHOLDS['stock']['meme']
        elif symbol in ['TSLA', 'NVDA']:
            threshold = THRESHOLDS['stock']['growth']
        else:
            threshold = THRESHOLDS['stock']['blue_chip']
    
    return change >= threshold, change, threshold

def check_cooldown(symbol):
    """Check if asset is in cooldown"""
    now = datetime.now()
    if symbol in last_alerts:
        time_since = (now - last_alerts[symbol]).total_seconds()
        if time_since < ALERT_COOLDOWN:
            return False
    last_alerts[symbol] = now
    return True

async def send_big_move_alert(symbol, data, change_pct, evidence=None):
    """Send big move alert with evidence"""
    direction = "🚀" if data['change_24h'] > 0 else "📉"
    
    message = f"""{direction} <b>BIG MOVE ALERT: {symbol}</b>

<b>Price Action:</b>
• Current: ${data['price']:,.2f}
• 24h Change: {data['change_24h']:+.2f}%

<b>Market:</b> {data['type'].upper()}

"""
    
    if evidence:
        message += "\n<b>Evidence:</b>\n"
        for item in evidence[:3]:
            message += f"• {item}\n"
    else:
        message += "\n🔍 Searching for catalyst...\n"
    
    message += f"\n<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>"
    
    await send_message(message)
    print(f"  🚨 BIG MOVE: {symbol} {data['change_24h']:+.2f}%")

async def run_scanner():
    """Main scanner loop"""
    print("="*60)
    print("🚀 Big Move Alert Bot")
    print("="*60)
    print(f"Monitoring: {len(ASSETS['crypto'])} crypto, {len(ASSETS['stocks'])} stocks")
    print(f"Check interval: 60 seconds\n")
    
    await send_message(
        "🟢 <b>Big Move Alert Bot Started</b>\n\n"
        f"Monitoring:\n"
        f"• {len(ASSETS['crypto'])} cryptocurrencies\n"
        f"• {len(ASSETS['stocks'])} stocks\n\n"
        f"Alert thresholds:\n"
        f"• Crypto majors: ±5%\n"
        f"• Crypto alts: ±15%\n"
        f"• Stocks: ±3-10%\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scanning...")
            
            # Get prices
            crypto_prices = await get_crypto_prices()
            # stock_prices = await get_stock_prices()  # Enable when API ready
            
            all_assets = {**crypto_prices}  # Add stocks when ready
            
            print(f"  Fetched {len(all_assets)} assets")
            
            # Check for big moves
            for symbol, data in all_assets.items():
                is_big_move, change_pct, threshold = check_big_move(symbol, data)
                
                if is_big_move and check_cooldown(symbol):
                    # Search for evidence
                    evidence = await search_news(symbol)
                    await send_big_move_alert(symbol, data, change_pct, evidence)
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
        
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    asyncio.run(run_scanner())
