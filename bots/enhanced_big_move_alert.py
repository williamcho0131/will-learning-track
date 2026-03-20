#!/usr/bin/env python3
"""
Enhanced Big Move Alert Bot
Now with Yahoo Finance (stocks) + CoinGecko (crypto) + NewsAPI context
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
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')  # Optional - enhances alerts

# Alert thresholds
THRESHOLDS = {
    'crypto': {
        'major': 0.05,      # 5% for BTC, ETH
        'mid': 0.08,        # 8% for mid-caps
        'alt': 0.15,        # 15% for alts
    },
    'stock': {
        'blue_chip': 0.03,  # 3% for SPY, QQQ, AAPL
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
        print(f"[ERROR] CoinGecko: {e}")
        return {}

async def get_stock_prices():
    """Fetch stock prices from Yahoo Finance (unofficial)"""
    prices = {}
    
    async with aiohttp.ClientSession() as session:
        for symbol in ASSETS['stocks'].keys():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {"interval": "1d", "range": "2d"}  # 2 days to get previous close
                
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data['chart']['result'][0]
                        meta = result['meta']
                        
                        current = meta.get('regularMarketPrice', 0)
                        previous = meta.get('previousClose', 0)
                        change_pct = ((current - previous) / previous * 100) if previous else 0
                        
                        prices[symbol] = {
                            'price': current,
                            'change_24h': change_pct,
                            'type': 'stock'
                        }
            except Exception as e:
                print(f"[ERROR] Yahoo Finance {symbol}: {e}")
                continue
    
    return prices

async def search_news(query, category=None):
    """Search for news using NewsAPI (optional)"""
    if not NEWSAPI_KEY:
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'sortBy': 'publishedAt',
            'language': 'en',
            'pageSize': 3,
            'apiKey': NEWSAPI_KEY
        }
        
        # If too many results, narrow with date
        if category == 'crypto':
            params['q'] += ' cryptocurrency'
        elif category == 'stock':
            params['q'] += ' stock market'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                
        if data.get('status') == 'ok':
            return [{
                'title': article['title'],
                'source': article['source']['name'],
                'url': article['url']
            } for article in data['articles'][:3]]
    except Exception as e:
        print(f"[ERROR] NewsAPI: {e}")
    
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
    """Send big move alert with news context"""
    direction = "🚀" if data['change_24h'] > 0 else "📉"
    asset_type = "CRYPTO" if data['type'] == 'crypto' else "STOCK"
    
    # Format price
    if data['price'] > 1000:
        price_str = f"${data['price']:,.2f}"
    else:
        price_str = f"${data['price']:.4f}"
    
    message = f"""{direction} <b>BIG MOVE ALERT: {symbol}</b>

<b>Asset Type:</b> {asset_type}
<b>Price:</b> {price_str}
<b>24h Change:</b> {data['change_24h']:+.2f}% 📊

"""
    
    if evidence:
        message += "<b>📰 Related News:\u003c/b>\n"
        for item in evidence:
            message += f"• {item['title'][:80]}...\n  ({item['source']})\n\n"
    else:
        # Add context about typical moves
        if data['type'] == 'crypto':
            message += "💡 <i>Crypto markets are volatile. This move is significant but not unusual.\u003c/i>\n"
        else:
            message += "💡 <i>Stock move exceeds typical daily range. Check for earnings/news.\u003c/i>\n"
    
    message += f"\n<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>"
    
    await send_message(message)
    print(f"  🚨 BIG MOVE: {symbol} {data['change_24h']:+.2f}%")

async def send_daily_summary(crypto_data, stock_data):
    """Send daily market summary"""
    # Top movers
    all_assets = {**crypto_data, **stock_data}
    sorted_by_change = sorted(all_assets.items(), 
                              key=lambda x: abs(x[1]['change_24h']), 
                              reverse=True)
    
    message = "📊 <b>Daily Market Summary</b>\n\n"
    
    message += "<b>Top 5 Movers:\u003c/b>\n"
    for i, (symbol, data) in enumerate(sorted_by_change[:5], 1):
        emoji = "🟢" if data['change_24h'] > 0 else "🔴"
        message += f"{i}. {symbol}: {data['change_24h']:+.2f}% {emoji}\n"
    
    # Market mood
    crypto_up = sum(1 for d in crypto_data.values() if d['change_24h'] > 0)
    stock_up = sum(1 for d in stock_data.values() if d['change_24h'] > 0)
    
    message += f"\n<b>Market Mood:\u003c/b>\n"
    message += f"• Crypto: {crypto_up}/{len(crypto_data)} up 📈\n"
    message += f"• Stocks: {stock_up}/{len(stock_data)} up 📈\n"
    
    await send_message(message)

async def run_scanner():
    """Main scanner loop"""
    print("="*60)
    print("🚀 Big Move Alert Bot - Enhanced Edition")
    print("="*60)
    print(f"Crypto: {len(ASSETS['crypto'])} assets (CoinGecko)")
    print(f"Stocks: {len(ASSETS['stocks'])} assets (Yahoo Finance)")
    if NEWSAPI_KEY:
        print("News: Enabled (NewsAPI)")
    else:
        print("News: Disabled (set NEWSAPI_KEY for news context)")
    print(f"Check interval: 60 seconds\n")
    
    await send_message(
        "🟢 <b>Big Move Alert Bot Started</b>\n\n"
        f"Monitoring:\n"
        f"• {len(ASSETS['crypto'])} cryptocurrencies (CoinGecko)\n"
        f"• {len(ASSETS['stocks'])} stocks (Yahoo Finance)\n\n"
        f"Alert thresholds:\n"
        f"• Crypto majors: ±5%\n"
        f"• Crypto alts: ±15%\n"
        f"• Stocks: ±3-10%\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    check_count = 0
    while True:
        try:
            check_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Check #{check_count}")
            
            # Get prices (parallel)
            crypto_task = get_crypto_prices()
            stock_task = get_stock_prices()
            crypto_prices, stock_prices = await asyncio.gather(crypto_task, stock_task)
            
            print(f"  Crypto: {len(crypto_prices)} assets")
            print(f"  Stocks: {len(stock_prices)} assets")
            
            all_assets = {**crypto_prices, **stock_prices}
            alerts_sent = 0
            
            # Check for big moves
            for symbol, data in all_assets.items():
                is_big_move, change_pct, threshold = check_big_move(symbol, data)
                
                if is_big_move and check_cooldown(symbol):
                    # Get news context
                    evidence = None
                    if NEWSAPI_KEY:
                        evidence = await search_news(symbol, data['type'])
                    
                    await send_big_move_alert(symbol, data, change_pct, evidence)
                    alerts_sent += 1
            
            # Send summary every 60 checks (hourly)
            if check_count % 60 == 0:
                await send_daily_summary(crypto_prices, stock_prices)
            
            print(f"  Alerts sent: {alerts_sent}")
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
        
        await asyncio.sleep(60)  # Check every minute

if __name__ == "__main__":
    asyncio.run(run_scanner())
