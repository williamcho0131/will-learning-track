#!/usr/bin/env python3
"""
Enhanced Funding Arbitrage Alert Bot
Now with Binance, Hyperliquid, Bybit, and OKX support
"""

import asyncio
import aiohttp
import os
from datetime import datetime
import time

# Config
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Exchange configurations
EXCHANGES = {
    'binance': {
        'name': 'Binance',
        'funding_url': 'https://fapi.binance.com/fapi/v1/premiumIndex',
        'has_funding': True,
        'weight': 1.0  # Reliability weight
    },
    'hyperliquid': {
        'name': 'Hyperliquid',
        'funding_url': 'https://api.hyperliquid.xyz/info',
        'has_funding': True,
        'weight': 0.9
    },
    'bybit': {
        'name': 'Bybit',
        'funding_url': 'https://api.bybit.com/v5/market/tickers',
        'has_funding': True,
        'weight': 0.95
    },
    'okx': {
        'name': 'OKX',
        'funding_url': 'https://www.okx.com/api/v5/public/funding-rate',
        'has_funding': True,
        'weight': 0.9
    }
}

# Opportunity thresholds
THRESHOLDS = {
    'major': {'min_spread': 0.0008, 'liquidity_factor': 1.0},
    'mid': {'min_spread': 0.0012, 'liquidity_factor': 0.7},
    'alt': {'min_spread': 0.0020, 'liquidity_factor': 0.5},
    'exotic': {'min_spread': 0.0030, 'liquidity_factor': 0.3},
}

ASSET_CLASS = {
    'BTC': 'major', 'ETH': 'major',
    'SOL': 'mid', 'LINK': 'mid', 'ARB': 'mid', 'AVAX': 'mid',
    'DOGE': 'alt', 'HYPE': 'alt', 'PEPE': 'alt', 'SHIB': 'alt',
}

def get_asset_class(symbol):
    base = symbol.replace('USDT', '').replace('USD', '').replace('-PERP', '')
    return ASSET_CLASS.get(base, 'mid')

cooldowns = {}
last_opportunities = {}

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

# ============ EXCHANGE API FETCHERS ============

async def get_binance_perps():
    """Fetch ALL perpetual markets from Binance"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://fapi.binance.com/fapi/v1/premiumIndex") as resp:
                data = await resp.json()
            
            async with session.get("https://fapi.binance.com/fapi/v1/ticker/24hr") as resp:
                tickers = {t['symbol']: t for t in await resp.json()}
            
            perps = {}
            for item in data:
                symbol = item['symbol']
                if not symbol.endswith('USDT'):
                    continue
                
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
    """Fetch ALL perpetual markets from Hyperliquid"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.hyperliquid.xyz/info', 
                json={"type": "metaAndAssetCtxs"}) as resp:
                data = await resp.json()
            
            meta, ctxs = data[0], data[1]
            perps = {}
            
            for i, asset in enumerate(meta['universe']):
                name = asset['name']
                ctx = ctxs[i]
                perps[name] = {
                    'funding': float(ctx['funding']),
                    'price': float(ctx['markPx']),
                    'oi': float(ctx['openInterest']),
                    'volume': float(ctx['dayNtlVlm']),
                    'exchange': 'Hyperliquid'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] Hyperliquid: {e}")
        return {}

async def get_bybit_perps():
    """Fetch perpetual markets from Bybit"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get tickers for USDT perpetuals
            url = "https://api.bybit.com/v5/market/tickers"
            params = {"category": "linear"}
            
            async with session.get(url, params=params) as resp:
                data = await resp.json()
            
            if data.get('retCode') != 0:
                return {}
            
            perps = {}
            for item in data['result']['list']:
                symbol = item['symbol']
                if not symbol.endswith('USDT'):
                    continue
                
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
    """Fetch perpetual markets from OKX"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://www.okx.com/api/v5/public/funding-rate"
            
            async with session.get(url) as resp:
                data = await resp.json()
            
            if data.get('code') != '0':
                return {}
            
            perps = {}
            for item in data['data']:
                symbol = item['instId']
                if not symbol.endswith('USDT'):
                    continue
                
                perps[symbol] = {
                    'funding': float(item.get('fundingRate', 0)),
                    'price': float(item.get('markPrice', 0)),
                    'volume': 0,  # Would need separate call
                    'change_24h': 0,  # Would need separate call
                    'exchange': 'OKX'
                }
            return perps
    except Exception as e:
        print(f"[ERROR] OKX: {e}")
        return {}

# ============ OPPORTUNITY ANALYSIS ============

def calculate_opportunity_score(asset, exchange_data):
    """Calculate opportunity score across multiple exchanges"""
    # Get all funding rates for this asset
    fundings = {}
    for ex_name, data in exchange_data.items():
        if data and asset in data:
            fundings[ex_name] = data[asset]['funding']
    
    if len(fundings) < 2:
        return None
    
    # Find max spread
    max_funding = max(fundings.values())
    min_funding = min(fundings.values())
    spread = abs(max_funding - min_funding)
    
    # Get asset class
    asset_class = get_asset_class(asset)
    min_spread = THRESHOLDS[asset_class]['min_spread']
    liquidity_factor = THRESHOLDS[asset_class]['liquidity_factor']
    
    if spread < min_spread:
        return None
    
    # Calculate score (simplified)
    score = spread * liquidity_factor * 100  # Scale up
    
    # Find best exchanges
    best_long = min(fundings, key=fundings.get)  # Most negative = paid to long
    best_short = max(fundings, key=fundings.get)  # Most positive = paid to short
    
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
    """Send HIGH priority opportunity alert"""
    asset = opp['asset']
    spread_pct = opp['spread'] * 100
    
    # Build funding rate lines
    funding_lines = []
    for ex, rate in sorted(opp['fundings'].items(), key=lambda x: x[1]):
        emoji = "🟢" if rate < 0 else "🔴"
        star = " ⭐" if ex == opp['best_long'] else ""
        funding_lines.append(f"  • {ex}: {rate*100:+.4f}%{star}")
    
    message = f"""🔥 <b>HIGH PRIORITY ARB: {asset}</b>

<b>Funding Spread:</b> {spread_pct:.4f}% (threshold: {opp['threshold']*100:.2f}%)

<b>Funding Rates by Exchange:</b>
{chr(10).join(funding_lines)}

<b>Best Trade Setup:</b>
💚 Long on {opp['best_long'].upper()} (most negative)
❤️ Short on {opp['best_short'].upper()} (most positive)

<b>Opportunity Score:</b> {opp['score']:.2f}

⏰ Check funding times - varies by exchange
<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>
"""
    
    await send_message(message)
    print(f"  🔥 ALERT SENT: {asset} (score: {opp['score']:.2f})")

async def send_multi_exchange_summary(opportunities, top_n=5):
    """Send summary of top opportunities"""
    if not opportunities:
        return
    
    lines = [f"📊 <b>Top {min(top_n, len(opportunities))} Multi-Exchange Opportunities</b>\n"]
    
    for i, opp in enumerate(opportunities[:top_n], 1):
        spread_pct = opp['spread'] * 100
        ex_count = len(opp['fundings'])
        lines.append(f"{i}. {opp['asset']}: {spread_pct:.4f}% spread ({ex_count} exchanges)")
    
    message = "\n".join(lines)
    await send_message(message)

# ============ MAIN SCANNER ============

async def scan_all_opportunities():
    """Scan all perpetuals across all exchanges"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning all exchanges...")
    
    # Fetch from all exchanges
    tasks = [
        get_binance_perps(),
        get_hyperliquid_perps(),
        get_bybit_perps(),
        get_okx_perps()
    ]
    
    results = await asyncio.gather(*tasks)
    exchange_data = {
        'binance': results[0],
        'hyperliquid': results[1],
        'bybit': results[2],
        'okx': results[3]
    }
    
    print(f"  Binance: {len(results[0])} markets")
    print(f"  Hyperliquid: {len(results[1])} markets")
    print(f"  Bybit: {len(results[2])} markets")
    print(f"  OKX: {len(results[3])} markets")
    
    # Find common assets across exchanges
    all_assets = set()
    for data in results:
        if data:
            all_assets.update(data.keys())
    
    # Normalize symbol formats
    normalized = {}
    for asset in all_assets:
        # Remove USDT suffix for matching
        base = asset.replace('USDT', '').replace('USD', '').replace('-PERP', '')
        if base not in normalized:
            normalized[base] = []
        normalized[base].append(asset)
    
    print(f"  Unique assets: {len(normalized)}")
    
    # Calculate opportunities
    opportunities = []
    for base_asset, variants in normalized.items():
        # Build exchange data for this asset
        asset_ex_data = {}
        for ex_name, data in exchange_data.items():
            if data:
                for variant in variants:
                    if variant in data:
                        asset_ex_data[ex_name] = data
                        break
        
        opp = calculate_opportunity_score(base_asset, asset_ex_data)
        if opp:
            opportunities.append(opp)
    
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    return opportunities, exchange_data

async def run_scanner():
    """Main scanner loop"""
    print("="*60)
    print("🚀 Multi-Exchange Funding Arbitrage Scanner")
    print("="*60)
    print(f"Exchanges: Binance, Hyperliquid, Bybit, OKX")
    print(f"Alert threshold: Score > 0.05")
    print(f"Scan interval: 5 seconds\n")
    
    await send_message(
        "🟢 <b>Multi-Exchange Scanner Started</b>\n\n"
        "Scanning:\n"
        "• Binance (600+ markets)\n"
        "• Hyperliquid (200+ markets)\n"
        "• Bybit (200+ markets)\n"
        "• OKX (200+ markets)\n\n"
        "Ranking: By cross-exchange opportunity score\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    scan_count = 0
    while True:
        try:
            scan_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan #{scan_count}")
            
            opportunities, exchange_data = await scan_all_opportunities()
            
            if opportunities:
                print(f"  Found {len(opportunities)} opportunities")
                
                # Send HIGH priority alerts
                high_priority = [o for o in opportunities if o['score'] > 0.05]
                for opp in high_priority:
                    if check_cooldown(opp['asset'], 'high_priority', 30):
                        await send_opportunity_alert(opp)
                
                # Send summary every 10 scans
                if scan_count % 10 == 0:
                    await send_multi_exchange_summary(opportunities)
            else:
                print(f"  No opportunities above threshold")
                # Show top spreads for monitoring
                if opportunities:
                    print(f"  Best: {opportunities[0]['asset']} @ {opportunities[0]['spread']*100:.4f}%")
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
        
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_scanner())
