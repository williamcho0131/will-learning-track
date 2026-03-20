#!/usr/bin/env python3
"""
Ultimate Funding Arbitrage Alert Bot
8 exchanges: Binance, Hyperliquid, Bybit, OKX, dYdX, KuCoin, GMX, Drift
"""

import asyncio
import aiohttp
import os
from datetime import datetime
import time
import json

# Config
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DATA_DIR = "/opt/will-learning-track/data"

# Exchange configurations (8 exchanges)
EXCHANGES = {
    'binance': {'name': 'Binance', 'weight': 1.0},
    'hyperliquid': {'name': 'Hyperliquid', 'weight': 0.9},
    'bybit': {'name': 'Bybit', 'weight': 0.95},
    'okx': {'name': 'OKX', 'weight': 0.9},
    'dydx': {'name': 'dYdX', 'weight': 0.85},
    'kucoin': {'name': 'KuCoin', 'weight': 0.8},
    'gmx': {'name': 'GMX V2', 'weight': 0.75},
    'drift': {'name': 'Drift', 'weight': 0.7}
}

# Opportunity thresholds
THRESHOLDS = {
    'major': {'min_spread': 0.0008, 'liquidity_factor': 1.0},
    'mid': {'min_spread': 0.0012, 'liquidity_factor': 0.7},
    'alt': {'min_spread': 0.0020, 'liquidity_factor': 0.5},
    'exotic': {'min_spread': 0.0030, 'liquidity_factor': 0.3}
}

ASSET_CLASS = {
    'BTC': 'major', 'ETH': 'major',
    'SOL': 'mid', 'LINK': 'mid', 'ARB': 'mid', 'AVAX': 'mid', 'OP': 'mid',
    'DOGE': 'alt', 'HYPE': 'alt', 'PEPE': 'alt', 'SHIB': 'alt', 'WIF': 'alt',
}

cooldowns = {}
last_opportunities = {}

def get_asset_class(symbol):
    base = symbol.replace('USDT', '').replace('USD', '').replace('-PERP', '').replace('-USD', '')
    return ASSET_CLASS.get(base, 'mid')

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

def check_cooldown(asset, alert_type, minutes=30):
    """Check if alert is in cooldown"""
    now = time.time()
    key = f"{asset}_{alert_type}"
    if key in cooldowns:
        if now - cooldowns[key] < minutes * 60:
            return False
    cooldowns[key] = now
    return True

# ============ EXCHANGE FETCHERS (8 EXCHANGES) ============

async def get_binance_perps():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://fapi.binance.com/fapi/v1/premiumIndex") as resp:
                data = await resp.json()
            async with session.get("https://fapi.binance.com/fapi/v1/ticker/24hr") as resp:
                tickers = {t['symbol']: t for t in await resp.json()}
            
            perps = {}
            for item in data:
                symbol = item['symbol']
                if not symbol.endswith('USDT'): continue
                ticker = tickers.get(symbol, {})
                perps[symbol] = {
                    'funding': float(item.get('lastFundingRate', 0)),
                    'price': float(item['markPrice']),
                    'volume': float(ticker.get('quoteVolume', 0)),
                    'change_24h': float(ticker.get('priceChangePercent', 0)),
                    'exchange': 'Binance'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] Binance: {e}")
        return {}

async def get_hyperliquid_perps():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.hyperliquid.xyz/info', json={"type": "metaAndAssetCtxs"}) as resp:
                data = await resp.json()
            meta, ctxs = data[0], data[1]
            perps = {}
            for i, asset in enumerate(meta['universe']):
                name = asset['name']
                ctx = ctxs[i]
                perps[name] = {
                    'funding': float(ctx['funding']),
                    'price': float(ctx['markPx']),
                    'volume': float(ctx['dayNtlVlm']),
                    'exchange': 'Hyperliquid'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] Hyperliquid: {e}")
        return {}

async def get_bybit_perps():
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.bybit.com/v5/market/tickers"
            params = {"category": "linear"}
            async with session.get(url, params=params) as resp:
                data = await resp.json()
            if data.get('retCode') != 0: return {}
            
            perps = {}
            for item in data['result']['list']:
                symbol = item['symbol']
                if not symbol.endswith('USDT'): continue
                funding = item.get('fundingRate', '0')
                perps[symbol] = {
                    'funding': float(funding) if funding else 0,
                    'price': float(item.get('lastPrice', 0)),
                    'volume': float(item.get('turnover24h', 0)),
                    'change_24h': float(item.get('price24hPcnt', 0)) * 100,
                    'exchange': 'Bybit'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] Bybit: {e}")
        return {}

async def get_okx_perps():
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://www.okx.com/api/v5/public/funding-rate"
            async with session.get(url) as resp:
                data = await resp.json()
            if data.get('code') != '0': return {}
            
            perps = {}
            for item in data['data']:
                symbol = item['instId']
                if not symbol.endswith('USDT'): continue
                perps[symbol] = {
                    'funding': float(item.get('fundingRate', 0)),
                    'price': float(item.get('markPrice', 0)),
                    'volume': 0,
                    'change_24h': 0,
                    'exchange': 'OKX'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] OKX: {e}")
        return {}

async def get_dydx_perps():
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://indexer.dydx.trade/v4/perpetualMarkets"
            async with session.get(url) as resp:
                data = await resp.json()
            
            perps = {}
            for market in data.get('markets', []):
                ticker = market.get('ticker', '')
                if not ticker.endswith('-USD'): continue
                symbol = ticker.replace('-USD', 'USDT')
                perps[symbol] = {
                    'funding': float(market.get('nextFundingRate', 0)),
                    'price': float(market.get('oraclePrice', 0)),
                    'volume': float(market.get('volume24H', 0)),
                    'change_24h': float(market.get('priceChange24H', 0)) * 100,
                    'exchange': 'dYdX'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] dYdX: {e}")
        return {}

async def get_kucoin_perps():
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api-futures.kucoin.com/api/v1/contracts/active"
            async with session.get(url) as resp:
                data = await resp.json()
            if data.get('code') != '200000': return {}
            
            perps = {}
            for item in data.get('data', []):
                symbol = item.get('symbol', '')
                if not symbol.endswith('USDTM'): continue
                clean_symbol = symbol.replace('USDTM', 'USDT')
                perps[clean_symbol] = {
                    'funding': float(item.get('fundingFeeRate', 0)),
                    'price': float(item.get('markPrice', 0)),
                    'volume': float(item.get('volumeOf24h', 0)),
                    'change_24h': float(item.get('priceChgPct', 0)) * 100,
                    'exchange': 'KuCoin'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] KuCoin: {e}")
        return {}

async def get_drift_perps():
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://mainnet-beta.api.drift.trade/markets"
            async with session.get(url) as resp:
                data = await resp.json()
            
            perps = {}
            for market in data.get('markets', []):
                symbol = market.get('marketName', '')
                if not symbol.endswith('-PERP'): continue
                perps[symbol] = {
                    'funding': float(market.get('lastFundingRate', 0)),
                    'price': float(market.get('markPrice', 0)),
                    'volume': float(market.get('volume24h', 0)),
                    'change_24h': float(market.get('priceChange24h', 0)) * 100,
                    'exchange': 'Drift'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] Drift: {e}")
        return {}

async def get_gmx_perps():
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://gmx-synthetics-api.vercel.app/prices"
            async with session.get(url) as resp:
                data = await resp.json()
            
            perps = {}
            for token, price_data in data.items():
                if token in ['USDC', 'USDT', 'DAI']: continue
                symbol = f"{token}USDT"
                perps[symbol] = {
                    'funding': float(price_data.get('fundingRate', 0)),
                    'price': float(price_data.get('price', 0)),
                    'volume': float(price_data.get('volume24h', 0)),
                    'change_24h': 0,
                    'exchange': 'GMX'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] GMX: {e}")
        return {}

# ============ ANALYSIS ============

def calculate_opportunity_score(asset, exchange_data):
    """Calculate cross-exchange opportunity"""
    fundings = {}
    for ex_name, data in exchange_data.items():
        if data and asset in data:
            fundings[ex_name] = data[asset]['funding']
    
    if len(fundings) < 2:
        return None
    
    max_funding = max(fundings.values())
    min_funding = min(fundings.values())
    spread = abs(max_funding - min_funding)
    
    asset_class = get_asset_class(asset)
    min_spread = THRESHOLDS[asset_class]['min_spread']
    liquidity_factor = THRESHOLDS[asset_class]['liquidity_factor']
    
    if spread < min_spread:
        return None
    
    score = spread * liquidity_factor * 100
    best_long = min(fundings, key=fundings.get)
    best_short = max(fundings, key=fundings.get)
    
    return {
        'asset': asset,
        'spread': spread,
        'score': score,
        'fundings': fundings,
        'best_long': best_long,
        'best_short': best_short,
        'asset_class': asset_class,
        'threshold': min_spread
    }

async def send_opportunity_alert(opp):
    """Send HIGH priority alert"""
    asset = opp['asset']
    spread_pct = opp['spread'] * 100
    
    funding_lines = []
    for ex, rate in sorted(opp['fundings'].items(), key=lambda x: x[1]):
        emoji = "🟢" if rate < 0 else "🔴"
        star = " ⭐" if ex == opp['best_long'] else ""
        funding_lines.append(f"  • {ex}: {rate*100:+.4f}%{star}")
    
    message = f"""🔥 <b>HIGH PRIORITY ARB: {asset}</b>

<b>Funding Spread:</b> {spread_pct:.4f}%

<b>Funding Rates by Exchange:</b>
{chr(10).join(funding_lines)}

<b>Best Setup:</b>
💚 Long on {opp['best_long'].upper()}
❤️ Short on {opp['best_short'].upper()}

<b>Score:</b> {opp['score']:.2f}
<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>
"""
    await send_message(message)
    print(f"  🔥 ALERT: {asset} (score: {opp['score']:.2f})")

async def save_dashboard_data(opportunities, exchange_data):
    """Save data for unified dashboard"""
    try:
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'opportunities': opportunities[:20],
            'exchange_status': {k: bool(v) for k, v in exchange_data.items()},
            'total_markets': sum(len(v) for v in exchange_data.values() if v)
        }
        
        with open(f"{DATA_DIR}/funding_arb_data.json", 'w') as f:
            json.dump(dashboard_data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Saving dashboard data: {e}")

# ============ MAIN ============

async def scan_all_opportunities():
    """Scan all 8 exchanges"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning 8 exchanges...")
    
    tasks = [
        get_binance_perps(),
        get_hyperliquid_perps(),
        get_bybit_perps(),
        get_okx_perps(),
        get_dydx_perps(),
        get_kucoin_perps(),
        get_drift_perps(),
        get_gmx_perps()
    ]
    
    results = await asyncio.gather(*tasks)
    exchange_data = {
        'binance': results[0],
        'hyperliquid': results[1],
        'bybit': results[2],
        'okx': results[3],
        'dydx': results[4],
        'kucoin': results[5],
        'drift': results[6],
        'gmx': results[7]
    }
    
    for name, data in exchange_data.items():
        count = len(data) if data else 0
        status = "✅" if data else "❌"
        print(f"  {status} {name.capitalize()}: {count} markets")
    
    # Find common assets
    all_assets = set()
    for data in results:
        if data:
            for symbol in data.keys():
                base = symbol.replace('USDT', '').replace('USD', '').replace('-PERP', '')
                all_assets.add(base)
    
    # Calculate opportunities
    opportunities = []
    for base_asset in all_assets:
        asset_ex_data = {}
        for ex_name, data in exchange_data.items():
            if data:
                for symbol, info in data.items():
                    if base_asset in symbol:
                        asset_ex_data[ex_name] = data
                        break
        
        opp = calculate_opportunity_score(base_asset, asset_ex_data)
        if opp:
            opportunities.append(opp)
    
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    return opportunities, exchange_data

async def run_scanner():
    """Main loop"""
    print("="*60)
    print("🚀 ULTIMATE FUNDING ARBITRAGE SCANNER")
    print("="*60)
    print("Exchanges: Binance | Hyperliquid | Bybit | OKX | dYdX | KuCoin | Drift | GMX")
    print(f"Scan interval: 5 seconds\n")
    
    await send_message(
        "🟢 <b>Ultimate Funding Scanner Started</b>\n\n"
        "Scanning 8 exchanges:\n"
        "• Binance (600+)\n"
        "• Hyperliquid (200+)\n"
        "• Bybit (200+)\n"
        "• OKX (200+)\n"
        "• dYdX (50+)\n"
        "• KuCoin (200+)\n"
        "• Drift (20+)\n"
        "• GMX (10+)\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    scan_count = 0
    while True:
        try:
            scan_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan #{scan_count}")
            
            opportunities, exchange_data = await scan_all_opportunities()
            
            # Save dashboard data
            await save_dashboard_data(opportunities, exchange_data)
            
            if opportunities:
                print(f"  Found {len(opportunities)} opportunities")
                
                # Send HIGH priority alerts
                high_priority = [o for o in opportunities if o['score'] > 0.05]
                for opp in high_priority:
                    if check_cooldown(opp['asset'], 'high_priority', 30):
                        await send_opportunity_alert(opp)
                
                # Summary every 10 scans
                if scan_count % 10 == 0 and opportunities:
                    summary = f"📊 <b>Top 5 Opportunities</b>\n\n"
                    for i, opp in enumerate(opportunities[:5], 1):
                        spread_pct = opp['spread'] * 100
                        summary += f"{i}. {opp['asset']}: {spread_pct:.4f}% ({len(opp['fundings'])} ex)\n"
                    await send_message(summary)
            else:
                print(f"  No opportunities above threshold")
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
        
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_scanner())
