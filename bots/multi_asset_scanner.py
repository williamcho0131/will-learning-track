#!/usr/bin/env python3
"""
Multi-Asset Opportunity Scanner
Scans ALL perpetual markets across exchanges
Ranks by opportunity score, alerts only on HIGH priority
"""

import asyncio
import aiohttp
import os
from datetime import datetime
import time

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Opportunity score thresholds
THRESHOLDS = {
    'major': {'min_spread': 0.0008, 'liquidity_factor': 1.0},      # BTC, ETH
    'mid': {'min_spread': 0.0012, 'liquidity_factor': 0.7},         # SOL, LINK, ARB
    'alt': {'min_spread': 0.0020, 'liquidity_factor': 0.5},         # DOGE, HYPE
    'exotic': {'min_spread': 0.0030, 'liquidity_factor': 0.3},      # Memes, new listings
}

# Asset classification
ASSET_CLASS = {
    'BTC': 'major', 'ETH': 'major',
    'SOL': 'mid', 'LINK': 'mid', 'ARB': 'mid',
    'DOGE': 'alt', 'HYPE': 'alt', 'PEPE': 'alt',
}

def get_asset_class(symbol):
    """Classify asset by market cap/liquidity"""
    base = symbol.replace('USDT', '').replace('USD', '').replace('-PERP', '')
    return ASSET_CLASS.get(base, 'mid')  # Default to mid if unknown

# Track state
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
        print(f"[ERROR] Send failed: {e}")
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

async def get_binance_perps():
    """Fetch ALL perpetual markets from Binance"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get all funding rates
            async with session.get("https://fapi.binance.com/fapi/v1/premiumIndex") as resp:
                data = await resp.json()
                
            # Get 24h ticker for volume/price
            async with session.get("https://fapi.binance.com/fapi/v1/ticker/24hr") as resp:
                tickers = {t['symbol']: t for t in await resp.json()}
            
            perps = {}
            for item in data:
                symbol = item['symbol']
                if not symbol.endswith('USDT'):
                    continue
                    
                funding = float(item.get('lastFundingRate', 0))
                mark_price = float(item['markPrice'])
                
                # Get additional data from ticker
                ticker = tickers.get(symbol, {})
                volume = float(ticker.get('quoteVolume', 0))
                price_change = float(ticker.get('priceChangePercent', 0))
                
                perps[symbol] = {
                    'funding': funding,
                    'price': mark_price,
                    'volume': volume,
                    'change_24h': price_change,
                    'exchange': 'Binance'
                }
            
            return perps
    except Exception as e:
        print(f"[ERROR] Binance fetch: {e}")
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
                name = asset['name']  # e.g., "BTC"
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
        print(f"[ERROR] Hyperliquid fetch: {e}")
        return {}

def calculate_opportunity_score(asset, binance_data, hl_data):
    """Calculate opportunity score for an asset"""
    if not binance_data or not hl_data:
        return None
    
    # Get asset class
    asset_class = get_asset_class(asset)
    config = THRESHOLDS[asset_class]
    
    # Calculate funding spread
    binance_funding = binance_data['funding']
    hl_funding = hl_data['funding']
    spread = abs(binance_funding - hl_funding)
    
    # Minimum spread check
    if spread < config['min_spread']:
        return None
    
    # Calculate notional OI
    oi_notional = hl_data.get('oi', 0) * hl_data.get('price', 0)
    
    # Opportunity score
    score = spread * config['liquidity_factor'] * (oi_notional / 1e9)
    
    return {
        'asset': asset,
        'spread': spread,
        'binance_funding': binance_funding,
        'hl_funding': hl_funding,
        'binance_price': binance_data['price'],
        'hl_price': hl_data['price'],
        'oi_notional': oi_notional,
        'volume': hl_data.get('volume', 0) + binance_data.get('volume', 0),
        'asset_class': asset_class,
        'score': score,
        'threshold': config['min_spread']
    }

async def scan_all_opportunities():
    """Scan all perpetuals and return ranked opportunities"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning all perp markets...")
    
    # Fetch all markets
    binance_perps = await get_binance_perps()
    hl_perps = await get_hyperliquid_perps()
    
    print(f"  Binance: {len(binance_perps)} markets")
    print(f"  Hyperliquid: {len(hl_perps)} markets")
    
    # Find common assets
    common_assets = set(binance_perps.keys()) & set(hl_perps.keys())
    print(f"  Common: {len(common_assets)} assets")
    
    # Calculate scores
    opportunities = []
    for asset in common_assets:
        opp = calculate_opportunity_score(
            asset, 
            binance_perps[asset], 
            hl_perps[asset]
        )
        if opp:
            opportunities.append(opp)
    
    # Sort by score descending
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    return opportunities, binance_perps, hl_perps

async def send_opportunity_alert(opp):
    """Send HIGH priority opportunity alert"""
    asset = opp['asset']
    spread_pct = opp['spread'] * 100
    
    # Determine best exchange to long/short
    if opp['binance_funding'] < opp['hl_funding']:
        best_long = 'Binance'
        best_short = 'Hyperliquid'
        long_funding = opp['binance_funding'] * 100
        short_funding = opp['hl_funding'] * 100
    else:
        best_long = 'Hyperliquid'
        best_short = 'Binance'
        long_funding = opp['hl_funding'] * 100
        short_funding = opp['binance_funding'] * 100
    
    message = f"""🔥 <b>HIGH PRIORITY ARB: {asset}</b>

Funding Spread: {spread_pct:.4f}% (threshold: {opp['threshold']*100:.2f}%)

<b>Funding Rates:</b>
• Binance: {opp['binance_funding']*100:.4f}%
• Hyperliquid: {opp['hl_funding']*100:.4f}%

<b>Trade Setup:</b>
💚 Long on {best_long}: {long_funding:.4f}%
❤️ Short on {best_short}: {short_funding:.4f}%

<b>Market Data:</b>
• OI: ${opp['oi_notional']/1e6:.1f}M
• Volume: ${opp['volume']/1e6:.1f}M
• Score: {opp['score']:.3f}

⏰ Next funding: ~8 hours
<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>
"""
    
    await send_message(message)
    print(f"  🔥 ALERT SENT: {asset} (score: {opp['score']:.3f})")

async def send_top_opportunities_summary(opportunities, top_n=3):
    """Send summary of top opportunities"""
    if not opportunities:
        return
    
    lines = [f"📊 <b>Top {min(top_n, len(opportunities))} Opportunities</b>\n"]
    
    for i, opp in enumerate(opportunities[:top_n], 1):
        spread_pct = opp['spread'] * 100
        lines.append(f"{i}. {opp['asset']}: {spread_pct:.4f}% spread (score: {opp['score']:.2f})")
    
    message = "\n".join(lines)
    await send_message(message)

async def run_scanner():
    """Main scanner loop"""
    print(f"[{datetime.now()}] Multi-Asset Opportunity Scanner Started")
    print(f"Scanning: ALL perpetual markets")
    print(f"Exchanges: Binance + Hyperliquid")
    print(f"Alert threshold: Score-based\n")
    
    # Send startup message
    await send_message(
        "🟢 <b>Multi-Asset Scanner Started</b>\n\n"
        "Scanning: ALL perpetual markets\n"
        "Ranking: By opportunity score\n"
        "Alerting: Only HIGH priority (score > 0.05)\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    scan_count = 0
    while True:
        try:
            scan_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan #{scan_count}")
            
            # Scan all opportunities
            opportunities, binance_perps, hl_perps = await scan_all_opportunities()
            
            if not opportunities:
                print(f"  No opportunities above threshold")
                # Print top 3 anyway for monitoring
                all_scores = []
                for asset in set(binance_perps.keys()) & set(hl_perps.keys()):
                    opp = calculate_opportunity_score(asset, binance_perps[asset], hl_perps[asset])
                    if opp:
                        all_scores.append((asset, opp['spread']*100))
                all_scores.sort(key=lambda x: x[1], reverse=True)
                if all_scores:
                    print(f"  Top spreads: {all_scores[:3]}")
            else:
                print(f"  Found {len(opportunities)} opportunities")
                
                # Send alerts for HIGH priority (score > 0.05)
                high_priority = [o for o in opportunities if o['score'] > 0.05]
                
                for opp in high_priority:
                    if check_cooldown(opp['asset'], 'high_priority', 60):
                        await send_opportunity_alert(opp)
                
                # Send summary of top 3 every 10 scans
                if scan_count % 10 == 0:
                    await send_top_opportunities_summary(opportunities)
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
        
        await asyncio.sleep(5)  # 5 second intervals

if __name__ == "__main__":
    asyncio.run(run_scanner())
