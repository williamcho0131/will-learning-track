#!/usr/bin/env python3
"""
Ultimate Big Move Alert Bot
50+ cryptos + 30+ stocks + News context
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

# 50+ CRYPTOCURRENCIES
CRYPTO_ASSETS = {
    # Major
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    
    # Layer 1s
    'SOL': 'solana',
    'BNB': 'binancecoin',
    'AVAX': 'avalanche-2',
    'ADA': 'cardano',
    'DOT': 'polkadot',
    'MATIC': 'matic-network',
    'ARB': 'arbitrum',
    'OP': 'optimism',
    'NEAR': 'near',
    'APT': 'aptos',
    'SUI': 'sui',
    'SEI': 'sei-network',
    'INJ': 'injective-protocol',
    'TIA': 'celestia',
    
    # DeFi
    'LINK': 'chainlink',
    'UNI': 'uniswap',
    'AAVE': 'aave',
    'MKR': 'maker',
    'LDO': 'lido-dao',
    'CRV': 'curve-dao-token',
    'SNX': 'havven',
    'COMP': 'compound-governance-token',
    'YFI': 'yearn-finance',
    'SUSHI': 'sushi',
    '1INCH': '1inch',
    
    # Memes
    'DOGE': 'dogecoin',
    'SHIB': 'shiba-inu',
    'PEPE': 'pepe',
    'WIF': 'dogwifhat',
    'BONK': 'bonk',
    'FLOKI': 'floki',
    
    # Others
    'XRP': 'ripple',
    'TON': 'the-open-network',
    'TRX': 'tron',
    'ICP': 'internet-computer',
    'FIL': 'filecoin',
    'ATOM': 'cosmos',
    'ALGO': 'algorand',
    'VET': 'vechain',
    'XLM': 'stellar',
    'HBAR': 'hedera-hashgraph',
    'SAND': 'the-sandbox',
    'MANA': 'decentraland',
    'AXS': 'axie-infinity',
    'GRT': 'the-graph',
    'RNDR': 'render-token',
    'FET': 'fetch-ai',
    'AGIX': 'singularitynet',
    'WLD': 'worldcoin-wld',
    'PYTH': 'pyth-network',
    'JUP': 'jupiter-exchange-solana',
    'JTO': 'jito-governance-token',
    'HYPE': 'hyperliquid',
    'BERA': 'berachain-bera',
}

# 30+ STOCKS
STOCK_ASSETS = {
    # Indexes
    'SPY': 'SPDR S&P 500',
    'QQQ': 'Invesco QQQ',
    'IWM': 'iShares Russell 2000',
    'DIA': 'SPDR Dow Jones',
    'VIX': 'CBOE Volatility Index',
    
    # Mega Cap Tech
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft',
    'GOOGL': 'Alphabet',
    'AMZN': 'Amazon',
    'META': 'Meta Platforms',
    'NVDA': 'NVIDIA',
    'TSLA': 'Tesla',
    'NFLX': 'Netflix',
    'AMD': 'Advanced Micro Devices',
    'INTC': 'Intel',
    'CRM': 'Salesforce',
    'ADBE': 'Adobe',
    'ORCL': 'Oracle',
    'IBM': 'IBM',
    'CSCO': 'Cisco',
    
    # Finance
    'JPM': 'JPMorgan Chase',
    'BAC': 'Bank of America',
    'GS': 'Goldman Sachs',
    'MS': 'Morgan Stanley',
    'V': 'Visa',
    'MA': 'Mastercard',
    'COIN': 'Coinbase',
    'HOOD': 'Robinhood',
    
    # Other
    'DIS': 'Disney',
    'NKE': 'Nike',
    'SBUX': 'Starbucks',
    'MCD': 'McDonald',
    'WMT': 'Walmart',
    'COST': 'Costco',
    'GME': 'GameStop',
    'AMC': 'AMC Entertainment',
    'PLTR': 'Palantir',
    'RKLB': 'Rocket Lab',
    'SMCI': 'Super Micro Computer',
    'MSTR': 'MicroStrategy',
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
                return resp.status == 200
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")
        return False

async def get_crypto_prices():
    try:
        # Batch requests to avoid rate limits
        all_prices = {}
        ids_list = list(CRYPTO_ASSETS.values())
        
        # Process in batches of 50
        for i in range(0, len(ids_list), 50):
            batch = ids_list[i:i+50]
            ids = ','.join(batch)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
            
            for symbol, cid in CRYPTO_ASSETS.items():
                if cid in data:
                    all_prices[symbol] = {
                        'price': data[cid]['usd'],
                        'change_24h': data[cid].get('usd_24h_change', 0),
                        'type': 'crypto'
                    }
            
            await asyncio.sleep(1)  # Rate limit
        
        return all_prices
    except Exception as e:
        print(f"[ERROR] CoinGecko: {e}")
        return {}

async def get_stock_prices():
    prices = {}
    async with aiohttp.ClientSession() as session:
        for symbol in STOCK_ASSETS.keys():
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                params = {"interval": "1d", "range": "2d"}
                
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
                continue
            await asyncio.sleep(0.5)  # Be nice to Yahoo
    return prices

def check_big_move(symbol, data):
    change = abs(data['change_24h'])
    
    if data['type'] == 'crypto':
        if symbol in ['BTC', 'ETH']:
            threshold = THRESHOLDS['crypto']['major']
        elif symbol in ['SOL', 'BNB', 'XRP', 'AVAX', 'ADA', 'DOT']:
            threshold = THRESHOLDS['crypto']['mid']
        elif symbol in ['DOGE', 'SHIB', 'PEPE', 'WIF', 'BONK', 'FLOKI']:
            threshold = THRESHOLDS['crypto']['meme']
        else:
            threshold = THRESHOLDS['crypto']['alt']
    else:  # stock
        if symbol in ['GME', 'AMC']:
            threshold = THRESHOLDS['stock']['meme']
        elif symbol in ['TSLA', 'NVDA', 'COIN', 'HOOD', 'PLTR', 'RKLB', 'SMCI', 'MSTR']:
            threshold = THRESHOLDS['stock']['growth']
        elif symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']:
            threshold = THRESHOLDS['stock']['mega']
        elif symbol in ['SPY', 'QQQ', 'IWM', 'DIA']:
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

async def save_dashboard_data(crypto_prices, stock_prices):
    """Save data for unified dashboard"""
    try:
        all_assets = {**crypto_prices, **stock_prices}
        sorted_assets = sorted(all_assets.items(), key=lambda x: abs(x[1]['change_24h']), reverse=True)
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'crypto_count': len(crypto_prices),
            'stock_count': len(stock_prices),
            'top_movers': [
                {'symbol': s, 'change': d['change_24h'], 'price': d['price'], 'type': d['type']}
                for s, d in sorted_assets[:10]
            ]
        }
        
        with open(f"{DATA_DIR}/big_move_data.json", 'w') as f:
            json.dump(dashboard_data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Saving dashboard data: {e}")

async def run_scanner():
    print("="*60)
    print("🚀 ULTIMATE BIG MOVE ALERT BOT")
    print("="*60)
    print(f"Crypto: {len(CRYPTO_ASSETS)} assets")
    print(f"Stocks: {len(STOCK_ASSETS)} assets")
    print(f"Total: {len(CRYPTO_ASSETS) + len(STOCK_ASSETS)} assets\n")
    
    await send_message(
        "🟢 <b>Ultimate Big Move Bot Started</b>\n\n"
        f"Monitoring {len(CRYPTO_ASSETS) + len(STOCK_ASSETS)} assets:\n"
        f"• {len(CRYPTO_ASSETS)} cryptocurrencies\n"
        f"• {len(STOCK_ASSETS)} stocks\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    check_count = 0
    while True:
        try:
            check_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Check #{check_count}")
            
            crypto_task = get_crypto_prices()
            stock_task = get_stock_prices()
            crypto_prices, stock_prices = await asyncio.gather(crypto_task, stock_task)
            
            print(f"  Crypto: {len(crypto_prices)}/{len(CRYPTO_ASSETS)} assets")
            print(f"  Stocks: {len(stock_prices)}/{len(STOCK_ASSETS)} assets")
            
            # Save for dashboard
            await save_dashboard_data(crypto_prices, stock_prices)
            
            all_assets = {**crypto_prices, **stock_prices}
            alerts_sent = 0
            
            for symbol, data in all_assets.items():
                is_big_move, change_pct, threshold = check_big_move(symbol, data)
                if is_big_move and check_cooldown(symbol):
                    await send_big_move_alert(symbol, data)
                    alerts_sent += 1
            
            # Hourly summary
            if check_count % 60 == 0:
                top_movers = sorted(all_assets.items(), key=lambda x: abs(x[1]['change_24h']), reverse=True)[:5]
                summary = "📊 <b>Hourly Top Movers</b>\n\n"
                for i, (sym, d) in enumerate(top_movers, 1):
                    summary += f"{i}. {sym}: {d['change_24h']:+.2f}%\n"
                await send_message(summary)
            
            print(f"  Alerts: {alerts_sent}")
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_scanner())
