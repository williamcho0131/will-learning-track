#!/usr/bin/env python3
"""
Ultimate Big Move Alert Bot - FIXED VERSION
50+ cryptos + 30+ stocks with better error handling
"""

import asyncio
import aiohttp
import os
from datetime import datetime
import json

# Config
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', '')
DATA_DIR = "/opt/will-learning-track/data"

# Thresholds
THRESHOLDS = {
    'crypto': {
        'major': 0.05,      # BTC, ETH
        'mid': 0.08,        # SOL, BNB, etc
        'alt': 0.12,        # Mid-cap alts
        'meme': 0.20,       # Meme coins
    },
    'stock': {
        'index': 0.02,      # SPY, QQQ
        'mega': 0.03,       # AAPL, MSFT
        'growth': 0.05,     # NVDA, TSLA
        'meme': 0.10,       # GME, AMC
        'china': 0.06,      # BABA, TCEHY
    }
}

# SIMPLIFIED: 20 Top Cryptos (for reliability)
CRYPTO_ASSETS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'SOL': 'solana',
    'BNB': 'binancecoin',
    'XRP': 'ripple',
    'ADA': 'cardano',
    'AVAX': 'avalanche-2',
    'DOGE': 'dogecoin',
    'DOT': 'polkadot',
    'MATIC': 'matic-network',
    'LINK': 'chainlink',
    'UNI': 'uniswap',
    'ATOM': 'cosmos',
    'LTC': 'litecoin',
    'BCH': 'bitcoin-cash',
    'ETC': 'ethereum-classic',
    'XLM': 'stellar',
    'ALGO': 'algorand',
    'VET': 'vechain',
    'ICP': 'internet-computer',
}

# SIMPLIFIED: 20 Top Stocks
STOCK_ASSETS = {
    'SPY': 'SPDR S&P 500',
    'QQQ': 'Invesco QQQ',
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft',
    'GOOGL': 'Alphabet',
    'AMZN': 'Amazon',
    'META': 'Meta Platforms',
    'NVDA': 'NVIDIA',
    'TSLA': 'Tesla',
    'NFLX': 'Netflix',
    'AMD': 'Advanced Micro Devices',
    'COIN': 'Coinbase',
    'GME': 'GameStop',
    'AMC': 'AMC Entertainment',
    'PLTR': 'Palantir',
    'HOOD': 'Robinhood',
    'SMCI': 'Super Micro Computer',
    'MSTR': 'MicroStrategy',
    'JPM': 'JPMorgan Chase',
    'DIS': 'Disney',
}

price_history = {}
ALERT_COOLDOWN = 3600
last_alerts = {}

async def send_message(text):
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{BASE_URL}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    print(f"[ERROR] Telegram API: {error}")
                return resp.status == 200
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")
        return False

async def get_crypto_prices():
    """Fetch crypto prices from CoinGecko - single batch for reliability"""
    try:
        ids = ','.join(CRYPTO_ASSETS.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        
        print(f"  [DEBUG] CoinGecko URL: {url[:100]}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"  [ERROR] CoinGecko HTTP {resp.status}: {text[:200]}")
                    return {}
                
                data = await resp.json()
                print(f"  [DEBUG] CoinGecko response keys: {list(data.keys())[:5]}")
        
        prices = {}
        missing = []
        for symbol, cid in CRYPTO_ASSETS.items():
            if cid in data:
                coin_data = data[cid]
                if 'usd' in coin_data:
                    prices[symbol] = {
                        'price': coin_data['usd'],
                        'change_24h': coin_data.get('usd_24h_change', 0) or 0,
                        'type': 'crypto'
                    }
                else:
                    missing.append(f"{symbol} (no usd key)")
            else:
                missing.append(symbol)
        
        if missing:
            print(f"  [WARN] Missing cryptos: {missing[:5]}...")
        
        return prices
    except Exception as e:
        print(f"[ERROR] CoinGecko: {e}")
        import traceback
        traceback.print_exc()
        return {}

async def get_stock_prices():
    """Fetch stock prices from Yahoo Finance"""
    prices = {}
    errors = []
    
    async with aiohttp.ClientSession() as session:
        for symbol in STOCK_ASSETS.keys():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {"interval": "1d", "range": "2d"}
                
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if 'chart' not in data or not data['chart']['result']:
                            errors.append(f"{symbol}: no data")
                            continue
                        
                        result = data['chart']['result'][0]
                        meta = result['meta']
                        
                        current = meta.get('regularMarketPrice', 0)
                        previous = meta.get('previousClose', 0)
                        change_pct = ((current - previous) / previous * 100) if previous else 0
                        
                        if current > 0:
                            prices[symbol] = {
                                'price': current,
                                'change_24h': change_pct,
                                'type': 'stock'
                            }
                    else:
                        errors.append(f"{symbol}: HTTP {resp.status}")
                        
            except Exception as e:
                errors.append(f"{symbol}: {str(e)[:30]}")
                continue
            
            await asyncio.sleep(0.3)  # Be nice to Yahoo
    
    if errors:
        print(f"  [WARN] Stock errors: {len(errors)}")
    
    return prices

def check_big_move(symbol, data):
    change = abs(data['change_24h'])
    
    if data['type'] == 'crypto':
        if symbol in ['BTC', 'ETH']:
            threshold = THRESHOLDS['crypto']['major']
        elif symbol in ['SOL', 'BNB', 'XRP', 'AVAX', 'ADA', 'DOT']:
            threshold = THRESHOLDS['crypto']['mid']
        elif symbol in ['DOGE', 'SHIB']:
            threshold = THRESHOLDS['crypto']['meme']
        else:
            threshold = THRESHOLDS['crypto']['alt']
    else:  # stock
        if symbol in ['GME', 'AMC']:
            threshold = THRESHOLDS['stock']['meme']
        elif symbol in ['TSLA', 'NVDA', 'COIN', 'HOOD', 'PLTR', 'SMCI', 'MSTR']:
            threshold = THRESHOLDS['stock']['growth']
        elif symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']:
            threshold = THRESHOLDS['stock']['mega']
        elif symbol in ['SPY', 'QQQ']:
            threshold = THRESHOLDS['stock']['index']
        else:
            threshold = THRESHOLDS['stock']['mega']
    
    return change >= threshold, change, threshold

def check_cooldown(symbol):
    now = datetime.now()
    if symbol in last_alerts:
        time_since = (now - last_alerts[symbol]).total_seconds()
        if time_since < ALERT_COOLDOWN:
            return False
    last_alerts[symbol] = now
    return True

async def send_big_move_alert(symbol, data):
    direction = "🚀" if data['change_24h'] > 0 else "📉"
    asset_type = "CRYPTO" if data['type'] == 'crypto' else "STOCK"
    
    if data['price'] > 1000:
        price_str = f"${data['price']:,.2f}"
    else:
        price_str = f"${data['price']:.4f}"
    
    message = f"""{direction} <b>BIG MOVE: {symbol}</b>

<b>Type:</b> {asset_type}
<b>Price:</b> {price_str}
<b>24h Change:</b> {data['change_24h']:+.2f}% 📊

<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>"""
    
    await send_message(message)
    print(f"  🚨 {symbol} {data['change_24h']:+.2f}%")

async def send_hourly_summary(crypto_prices, stock_prices):
    """Send hourly summary with better error handling"""
    try:
        all_assets = {}
        
        # Add crypto data
        for sym, data in crypto_prices.items():
            all_assets[sym] = data
        
        # Add stock data
        for sym, data in stock_prices.items():
            all_assets[sym] = data
        
        print(f"  [DEBUG] Hourly summary: {len(all_assets)} total assets")
        
        if len(all_assets) == 0:
            print("  [WARN] No asset data for hourly summary")
            return
        
        # Sort by absolute change
        sorted_assets = sorted(all_assets.items(), 
                              key=lambda x: abs(x[1].get('change_24h', 0)), 
                              reverse=True)
        
        summary = "📊 <b>Hourly Top Movers</b>\n\n"
        
        for i, (sym, d) in enumerate(sorted_assets[:5], 1):
            change = d.get('change_24h', 0)
            emoji = "🟢" if change > 0 else "🔴"
            summary += f"{i}. {sym}: {change:+.2f}% {emoji}\n"
        
        # Add separator and more movers
        if len(sorted_assets) > 5:
            summary += "\n<b>More movers:</b>\n"
            for i, (sym, d) in enumerate(sorted_assets[5:10], 6):
                change = d.get('change_24h', 0)
                summary += f"{i}. {sym}: {change:+.2f}%\n"
        
        # Add counts
        crypto_up = sum(1 for d in crypto_prices.values() if d.get('change_24h', 0) > 0)
        stock_up = sum(1 for d in stock_prices.values() if d.get('change_24h', 0) > 0)
        
        summary += f"\n<b>Market Summary:</b>\n"
        summary += f"• Crypto: {crypto_up}/{len(crypto_prices)} up 📈\n"
        summary += f"• Stocks: {stock_up}/{len(stock_prices)} up 📈"
        
        await send_message(summary)
        print(f"  📊 Hourly summary sent ({len(all_assets)} assets)")
        
    except Exception as e:
        print(f"[ERROR] Hourly summary failed: {e}")
        import traceback
        traceback.print_exc()

async def save_dashboard_data(crypto_prices, stock_prices):
    """Save data for unified dashboard"""
    try:
        all_assets = {**crypto_prices, **stock_prices}
        sorted_assets = sorted(all_assets.items(), 
                              key=lambda x: abs(x[1].get('change_24h', 0)), 
                              reverse=True)
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'crypto_count': len(crypto_prices),
            'stock_count': len(stock_prices),
            'top_movers': [
                {'symbol': s, 'change': d.get('change_24h', 0), 'price': d.get('price', 0), 'type': d.get('type', 'unknown')}
                for s, d in sorted_assets[:10]
            ]
        }
        
        with open(f"{DATA_DIR}/big_move_data.json", 'w') as f:
            json.dump(dashboard_data, f, indent=2)
            
    except Exception as e:
        print(f"[ERROR] Saving dashboard data: {e}")

async def run_scanner():
    print("="*60)
    print("🚀 ULTIMATE BIG MOVE ALERT BOT - FIXED")
    print("="*60)
    print(f"Crypto: {len(CRYPTO_ASSETS)} assets")
    print(f"Stocks: {len(STOCK_ASSETS)} assets")
    print(f"Total: {len(CRYPTO_ASSETS) + len(STOCK_ASSETS)} assets\n")
    
    await send_message(
        "🟢 <b>Big Move Bot v2.0 Started</b>\n\n"
        f"Monitoring {len(CRYPTO_ASSETS) + len(STOCK_ASSETS)} assets:\n"
        f"• {len(CRYPTO_ASSETS)} cryptocurrencies\n"
        f"• {len(STOCK_ASSETS)} stocks\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    check_count = 0
    while True:
        try:
            check_count += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{timestamp}] Check #{check_count}")
            
            # Get prices
            crypto_prices = await get_crypto_prices()
            await asyncio.sleep(2)  # Brief pause between APIs
            stock_prices = await get_stock_prices()
            
            print(f"  Crypto: {len(crypto_prices)}/{len(CRYPTO_ASSETS)} assets")
            print(f"  Stocks: {len(stock_prices)}/{len(STOCK_ASSETS)} assets")
            
            # Save for dashboard
            await save_dashboard_data(crypto_prices, stock_prices)
            
            # Check for big moves
            all_assets = {**crypto_prices, **stock_prices}
            alerts_sent = 0
            
            for symbol, data in all_assets.items():
                is_big_move, change_pct, threshold = check_big_move(symbol, data)
                if is_big_move and check_cooldown(symbol):
                    await send_big_move_alert(symbol, data)
                    alerts_sent += 1
            
            # Hourly summary (every 60 checks = ~1 hour)
            if check_count % 60 == 0:
                print(f"  [DEBUG] Sending hourly summary...")
                await send_hourly_summary(crypto_prices, stock_prices)
            
            print(f"  Alerts: {alerts_sent}")
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_scanner())
