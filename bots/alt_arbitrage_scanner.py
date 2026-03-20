#!/usr/bin/env python3
"""
Alt-Focused Funding & Basis Arbitrage Scanner
Scans every 1 second, alerts only on high-opportunity alt coin setups
"""

import asyncio
import aiohttp
import os
from datetime import datetime, timedelta
import time

# Config
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Focus on ALT coins (not BTC/ETH majors)
# Basis = spot vs perpetual price difference
# Funding = funding rate arbitrage across exchanges
ALT_COINS = [
    'SOL', 'LINK', 'ARB', 'OP', 'AVAX', 'DOT', 'MATIC', 'UNI', 'AAVE',
    'DOGE', 'SHIB', 'PEPE', 'WIF', 'BONK', 'FLOKI',
    'SUI', 'SEI', 'TIA', 'INJ', 'APT', 'NEAR', 'DYDX',
    'ATOM', 'ALGO', 'VET', 'XLM', 'FIL', 'ICP', 'GRT', 'RNDR',
    'FET', 'AGIX', 'WLD', 'PYTH', 'JUP', 'JTO', 'HYPE'
]

# Thresholds for ALTS only
THRESHOLDS = {
    'funding_spread': 0.003,      # 0.3% funding rate difference
    'basis_premium': 0.005,       # 0.5% basis (spot vs perp)
    'combined_score': 0.08,       # Combined opportunity score
}

# Track opportunities to avoid spam
opportunity_cooldown = {}
COOLDOWN_MINUTES = 15

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

def check_cooldown(asset, opp_type):
    """Check if opportunity is in cooldown"""
    now = time.time()
    key = f"{asset}_{opp_type}"
    if key in opportunity_cooldown:
        if now - opportunity_cooldown[key] < COOLDOWN_MINUTES * 60:
            return False
    opportunity_cooldown[key] = now
    return True

async def get_binance_ticker(symbol):
    """Get spot and perp prices from Binance"""
    try:
        async with aiohttp.ClientSession() as session:
            # Spot price
            spot_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
            async with session.get(spot_url, timeout=5) as resp:
                if resp.status != 200:
                    return None
                spot_data = await resp.json()
            
            # Perp price
            perp_url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}USDT"
            async with session.get(perp_url, timeout=5) as resp:
                if resp.status != 200:
                    return None
                perp_data = await resp.json()
            
            spot_price = float(spot_data['lastPrice'])
            perp_price = float(perp_data['markPrice'])
            funding_rate = float(perp_data['lastFundingRate'])
            
            # Calculate basis (premium/discount)
            basis = (perp_price - spot_price) / spot_price
            
            return {
                'spot': spot_price,
                'perp': perp_price,
                'basis': basis,
                'funding': funding_rate,
                'volume': float(spot_data['quoteVolume'])
            }
    except Exception as e:
        return None

async def get_bybit_ticker(symbol):
    """Get perp data from Bybit"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://api.bybit.com/v5/market/tickers"
            params = {"category": "linear", "symbol": f"{symbol}USDT"}
            
            async with session.get(url, params=params, timeout=5) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
            
            if data.get('retCode') != 0:
                return None
            
            ticker = data['result']['list'][0]
            return {
                'perp': float(ticker['lastPrice']),
                'funding': float(ticker.get('fundingRate', 0)),
                'volume': float(ticker.get('turnover24h', 0))
            }
    except Exception as e:
        return None

async def get_hyperliquid_ticker(symbol):
    """Get perp data from Hyperliquid"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.hyperliquid.xyz/info',
                json={"type": "allMids"},
                timeout=5
            ) as resp:
                if resp.status != 200:
                    return None
                prices = await resp.json()
            
            async with session.post(
                'https://api.hyperliquid.xyz/info',
                json={"type": "metaAndAssetCtxs"},
                timeout=5
            ) as resp:
                if resp.status != 200:
                    return None
                ctx_data = await resp.json()
            
            # Find symbol in data
            meta, ctxs = ctx_data[0], ctx_data[1]
            for i, asset in enumerate(meta['universe']):
                if asset['name'] == symbol:
                    return {
                        'perp': float(prices.get(symbol, 0)),
                        'funding': float(ctxs[i].get('funding', 0)),
                        'volume': float(ctxs[i].get('dayNtlVlm', 0))
                    }
            return None
    except Exception as e:
        return None

async def scan_alt_opportunities():
    """Scan alt coins for basis + funding opportunities"""
    opportunities = []
    
    for symbol in ALT_COINS:
        # Get data from multiple exchanges
        binance_data = await get_binance_ticker(symbol)
        bybit_data = await get_bybit_ticker(symbol)
        hyperliquid_data = await get_hyperliquid_ticker(symbol)
        
        if not binance_data:
            continue
        
        opp = None
        
        # Check 1: BASIS ARBITRAGE (Spot vs Perp on same exchange)
        basis = binance_data['basis']
        basis_pct = abs(basis) * 100
        
        if basis_pct >= THRESHOLDS['basis_premium'] * 100:
            # Basis arbitrage: buy spot, short perp (or vice versa)
            direction = "perp_premium" if basis > 0 else "spot_premium"
            score = basis_pct * 10  # Scale up
            
            opp = {
                'symbol': symbol,
                'type': 'basis',
                'subtype': direction,
                'score': score,
                'basis_pct': basis_pct,
                'funding_annual': binance_data['funding'] * 100 * 365,  # Annualized
                'spot_price': binance_data['spot'],
                'perp_price': binance_data['perp'],
                'volume': binance_data['volume'],
                'exchange': 'Binance'
            }
        
        # Check 2: FUNDING ARBITRAGE (across exchanges)
        fundings = {}
        if binance_data:
            fundings['Binance'] = binance_data['funding']
        if bybit_data:
            fundings['Bybit'] = bybit_data['funding']
        if hyperliquid_data:
            fundings['Hyperliquid'] = hyperliquid_data['funding']
        
        if len(fundings) >= 2:
            max_funding = max(fundings.values())
            min_funding = min(fundings.values())
            funding_spread = abs(max_funding - min_funding)
            funding_spread_pct = funding_spread * 100
            
            if funding_spread_pct >= THRESHOLDS['funding_spread'] * 100:
                best_long = min(fundings, key=fundings.get)
                best_short = max(fundings, key=fundings.get)
                
                score = funding_spread_pct * 5
                
                # Only alert if better than basis opp
                if not opp or score > opp['score']:
                    opp = {
                        'symbol': symbol,
                        'type': 'funding',
                        'score': score,
                        'funding_spread_pct': funding_spread_pct,
                        'fundings': fundings,
                        'best_long': best_long,
                        'best_short': best_short,
                        'price': binance_data['spot'] if binance_data else 0,
                        'volume': binance_data['volume'] if binance_data else 0
                    }
        
        # Check 3: COMBINED OPPORTUNITY (basis + funding)
        if basis_pct >= THRESHOLDS['basis_premium'] * 100 and len(fundings) >= 2:
            combined_score = basis_pct * 10 + funding_spread_pct * 5
            
            if combined_score >= THRESHOLDS['combined_score'] * 100:
                opp = {
                    'symbol': symbol,
                    'type': 'combined',
                    'score': combined_score,
                    'basis_pct': basis_pct,
                    'funding_spread_pct': funding_spread_pct if len(fundings) >= 2 else 0,
                    'spot_price': binance_data['spot'],
                    'perp_price': binance_data['perp'],
                    'fundings': fundings if len(fundings) >= 2 else {},
                    'exchange': 'Binance'
                }
        
        if opp and opp['score'] >= THRESHOLDS['combined_score'] * 100:
            opportunities.append(opp)
    
    return opportunities

async def send_opportunity_alert(opp):
    """Send formatted alert"""
    symbol = opp['symbol']
    
    if opp['type'] == 'basis':
        message = f"""🔥 <b>ALT BASIS ARB: {symbol}</b>

<b>Type:</b> Spot vs Perp Basis
<b>Basis:</b> {opp['basis_pct']:.2f}%
<b>Spot:</b> ${opp['spot_price']:.4f}
<b>Perp:</b> ${opp['perp_price']:.4f}
<b>Funding (annual):</b> {opp['funding_annual']:.1f}%
<b>Volume:</b> ${opp['volume']/1e6:.1f}M

<b>Trade:</b> Buy Spot + Short Perp
<b>Score:</b> {opp['score']:.1f}

<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>"""
    
    elif opp['type'] == 'funding':
        funding_lines = "\n".join([f"  {ex}: {rate*100:+.4f}%" for ex, rate in sorted(opp['fundings'].items(), key=lambda x: x[1])])
        
        message = f"""💰 <b>ALT FUNDING ARB: {symbol}</b>

<b>Type:</b> Cross-Exchange Funding
<b>Spread:</b> {opp['funding_spread_pct']:.3f}%
<b>Price:</b> ${opp['price']:.4f}

<b>Funding Rates:</b>
{funding_lines}

<b>Long:</b> {opp['best_long']} (cheaper)
<b>Short:</b> {opp['best_short']} (expensive)
<b>Score:</b> {opp['score']:.1f}

<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>"""
    
    else:  # combined
        funding_info = ""
        if opp.get('fundings'):
            funding_lines = "\n".join([f"  {ex}: {rate*100:+.4f}%" for ex, rate in sorted(opp['fundings'].items(), key=lambda x: x[1])[:3]])
            funding_info = f"\n<b>Funding Rates:</b>\n{funding_lines}"
        
        message = f"""🚀 <b>ALT COMBINED ARB: {symbol}</b>

<b>Type:</b> Basis + Funding
<b>Basis:</b> {opp['basis_pct']:.2f}%
<b>Funding Spread:</b> {opp.get('funding_spread_pct', 0):.3f}%
<b>Spot:</b> ${opp['spot_price']:.4f}
<b>Perp:</b> ${opp['perp_price']:.4f}
{funding_info}

<b>Score:</b> {opp['score']:.1f} 🔥🔥

<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>"""
    
    await send_message(message)
    print(f"  🚨 ALERT: {symbol} ({opp['type']}) Score: {opp['score']:.1f}")

async def run_scanner():
    """Main loop - scan every 1 second"""
    print("="*60)
    print("🚀 ALT-FOCUSED BASIS + FUNDING SCANNER")
    print("="*60)
    print(f"Scanning: {len(ALT_COINS)} alt coins")
    print(f"Frequency: Every 1 second")
    print(f"Basis threshold: ±{THRESHOLDS['basis_premium']*100:.1f}%")
    print(f"Funding spread: ±{THRESHOLDS['funding_spread']*100:.1f}%")
    print(f"Cooldown: {COOLDOWN_MINUTES} minutes per alert\n")
    
    await send_message(
        "🟢 <b>Alt Arbitrage Scanner Started</b>\n\n"
        f"Monitoring {len(ALT_COINS)} alt coins:\n"
        f"• Basis arbitrage (spot vs perp)\n"
        f"• Funding rate arbitrage\n"
        f"• Combined opportunities\n\n"
        f"Scan every 1 second\n"
        f"Alert threshold: Score ≥ {THRESHOLDS['combined_score']*100:.0f}\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    scan_count = 0
    last_status_time = time.time()
    
    while True:
        try:
            scan_count += 1
            start_time = time.time()
            
            opportunities = await scan_alt_opportunities()
            
            # Send alerts for high-scoring opportunities
            alerts_sent = 0
            for opp in opportunities:
                if opp['score'] >= THRESHOLDS['combined_score'] * 100:
                    if check_cooldown(opp['symbol'], opp['type']):
                        await send_opportunity_alert(opp)
                        alerts_sent += 1
            
            # Status update every 60 seconds
            if time.time() - last_status_time >= 60:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Scan #{scan_count} | Opps: {len(opportunities)} | Alerts: {alerts_sent}")
                last_status_time = time.time()
            
            # Ensure exactly 1 second between scans
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 - elapsed)
            await asyncio.sleep(sleep_time)
            
        except Exception as e:
            print(f"[ERROR] Scan failed: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_scanner())
