#!/usr/bin/env python3
"""
15-Minute Top 10 Movers Alert Bot
Scans every 1 second, reports top 10 movers every 15 minutes
Tracks price changes in 15-minute windows
"""

import asyncio
import aiohttp
import os
from datetime import datetime, timedelta
from collections import deque

# Config
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Assets to monitor (30 total)
ASSETS = {
    # Crypto (20)
    'BTC': 'crypto',
    'ETH': 'crypto',
    'SOL': 'crypto',
    'BNB': 'crypto',
    'XRP': 'crypto',
    'ADA': 'crypto',
    'AVAX': 'crypto',
    'DOGE': 'crypto',
    'DOT': 'crypto',
    'MATIC': 'crypto',
    'LINK': 'crypto',
    'UNI': 'crypto',
    'ATOM': 'crypto',
    'LTC': 'crypto',
    'BCH': 'crypto',
    'ETC': 'crypto',
    'XLM': 'crypto',
    'ALGO': 'crypto',
    'VET': 'crypto',
    'ICP': 'crypto',
    
    # Stocks (10)
    'SPY': 'stock',
    'QQQ': 'stock',
    'AAPL': 'stock',
    'MSFT': 'stock',
    'NVDA': 'stock',
    'TSLA': 'stock',
    'GOOGL': 'stock',
    'AMZN': 'stock',
    'META': 'stock',
    'GME': 'stock',
}

# Price history - stores (timestamp, price) for each asset
# Keeps 15 minutes of data (900 seconds / 1 second scan = 900 data points)
price_history = {symbol: deque(maxlen=1000) for symbol in ASSETS}

# Crypto ID mapping for CoinGecko
CRYPTO_IDS = {
    'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'BNB': 'binancecoin',
    'XRP': 'ripple', 'ADA': 'cardano', 'AVAX': 'avalanche-2', 'DOGE': 'dogecoin',
    'DOT': 'polkadot', 'MATIC': 'matic-network', 'LINK': 'chainlink', 'UNI': 'uniswap',
    'ATOM': 'cosmos', 'LTC': 'litecoin', 'BCH': 'bitcoin-cash', 'ETC': 'ethereum-classic',
    'XLM': 'stellar', 'ALGO': 'algorand', 'VET': 'vechain', 'ICP': 'internet-computer'
}

async def send_message(text):
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
    """Fetch all crypto prices in one call"""
    try:
        ids = ','.join(CRYPTO_IDS.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
        
        prices = {}
        for symbol, cid in CRYPTO_IDS.items():
            if cid in data and 'usd' in data[cid]:
                prices[symbol] = data[cid]['usd']
        return prices
    except Exception as e:
        return {}

async def get_stock_prices():
    """Fetch stock prices"""
    prices = {}
    stock_symbols = [s for s, t in ASSETS.items() if t == 'stock']
    
    async with aiohttp.ClientSession() as session:
        for symbol in stock_symbols:
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {"interval": "1m", "range": "1d"}  # 1 minute intervals
                
                async with session.get(url, params=params, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if 'chart' in data and data['chart']['result']:
                            result = data['chart']['result'][0]
                            meta = result['meta']
                            price = meta.get('regularMarketPrice', 0)
                            if price > 0:
                                prices[symbol] = price
            except:
                pass
            await asyncio.sleep(0.2)
    
    return prices

def calculate_15min_change(symbol):
    """Calculate price change over last 15 minutes"""
    history = price_history[symbol]
    
    if len(history) < 2:
        return None
    
    now = datetime.now()
    cutoff = now - timedelta(minutes=15)
    
    # Find price from 15 minutes ago
    old_price = None
    for ts, price in reversed(history):
        if ts <= cutoff:
            old_price = price
            break
    
    if old_price is None:
        # Not enough history, use earliest point
        old_price = history[0][1]
    
    current_price = history[-1][1]
    change_pct = ((current_price - old_price) / old_price) * 100
    
    return {
        'symbol': symbol,
        'type': ASSETS[symbol],
        'old_price': old_price,
        'current_price': current_price,
        'change_pct': change_pct,
        'abs_change': abs(change_pct)
    }

async def send_15min_report():
    """Send top 10 movers report"""
    # Calculate changes for all assets
    changes = []
    for symbol in ASSETS:
        change_data = calculate_15min_change(symbol)
        if change_data:
            changes.append(change_data)
    
    if not changes:
        print("  [WARN] No change data available yet")
        return
    
    # Sort by absolute change
    changes.sort(key=lambda x: x['abs_change'], reverse=True)
    
    # Build report
    message = "📊 <b>15-Minute Top 10 Movers</b>\n"
    message += f"⏰ {datetime.now().strftime('%H:%M')} UTC\n\n"
    
    for i, data in enumerate(changes[:10], 1):
        symbol = data['symbol']
        change = data['change_pct']
        current = data['current_price']
        
        emoji = "🟢" if change > 0 else "🔴"
        arrow = "↑" if change > 0 else "↓"
        
        # Format price
        if current > 1000:
            price_str = f"${current:,.0f}"
        elif current > 1:
            price_str = f"${current:.2f}"
        else:
            price_str = f"${current:.4f}"
        
        message += f"{i}. <b>{symbol}</b> {emoji}\n"
        message += f"   {arrow} {abs(change):.2f}% | {price_str}\n\n"
    
    # Add summary
    crypto_up = sum(1 for c in changes if c['type'] == 'crypto' and c['change_pct'] > 0)
    crypto_total = sum(1 for c in changes if c['type'] == 'crypto')
    stock_up = sum(1 for c in changes if c['type'] == 'stock' and c['change_pct'] > 0)
    stock_total = sum(1 for c in changes if c['type'] == 'stock')
    
    message += f"\n<b>Market Summary:</b>\n"
    message += f"• Crypto: {crypto_up}/{crypto_total} up\n"
    message += f"• Stocks: {stock_up}/{stock_total} up"
    
    await send_message(message)
    print(f"  📊 15-min report sent ({len(changes)} assets tracked)")

async def run_scanner():
    """Main loop - scan every 1 second, report every 15 minutes"""
    print("="*60)
    print("🚀 15-MINUTE TOP 10 MOVERS BOT")
    print("="*60)
    print(f"Assets: {len(ASSETS)} (20 crypto + 10 stocks)")
    print(f"Scan frequency: Every 1 second")
    print(f"Report frequency: Every 15 minutes")
    print(f"Tracking: 15-minute price windows\n")
    
    await send_message(
        "🟢 <b>15-Minute Movers Bot Started</b>\n\n"
        f"Monitoring {len(ASSETS)} assets:\n"
        f"• 20 cryptocurrencies\n"
        f"• 10 stocks\n\n"
        f"• Scanning every 1 second\n"
        f"• Reporting top 10 movers every 15 minutes\n"
        f"• Tracking 15-minute price windows\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    scan_count = 0
    last_report_time = datetime.now()
    
    while True:
        try:
            scan_count += 1
            start_time = datetime.now()
            
            # Fetch prices
            crypto_prices = await get_crypto_prices()
            stock_prices = await get_stock_prices()
            
            # Update price history
            for symbol, price in crypto_prices.items():
                price_history[symbol].append((start_time, price))
            
            for symbol, price in stock_prices.items():
                price_history[symbol].append((start_time, price))
            
            # Check if 15 minutes passed
            time_since_report = (start_time - last_report_time).total_seconds()
            
            if time_since_report >= 15 * 60:  # 15 minutes
                await send_15min_report()
                last_report_time = start_time
                print(f"[{start_time.strftime('%H:%M:%S')}] Report #{scan_count // 900} sent")
            
            # Status every 60 seconds
            if scan_count % 60 == 0:
                total_tracked = sum(len(h) for h in price_history.values())
                print(f"[{start_time.strftime('%H:%M:%S')}] Scan #{scan_count} | Tracked: {total_tracked} points | Next report in {((15*60) - time_since_report)/60:.0f}min")
            
            # Ensure 1 second between scans
            elapsed = (datetime.now() - start_time).total_seconds()
            sleep_time = max(0, 1.0 - elapsed)
            await asyncio.sleep(sleep_time)
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_scanner())
