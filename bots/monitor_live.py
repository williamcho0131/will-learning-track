#!/usr/bin/env python3
"""
Continuous Market Monitor
Lightweight, runs 24/7, sends alerts when thresholds hit
"""

import asyncio
import aiohttp
import os
from datetime import datetime
import time

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Alert thresholds
THRESHOLDS = {
    'funding_extreme': 0.001,    # ±0.1%
    'funding_opportunity': -0.0005,  # -0.05%
    'btc_support': 65000,
    'btc_resistance': 75000,
    'price_change_1h': 0.05,     # 5% move
    'oi_change_pct': 0.10,       # 10% OI change
    'oi_large_value': 50000000000,  # $50B notional OI
}

# Track state
cooldowns = {}
last_prices = {'btc': 0, 'eth': 0}
last_oi = {'hl_btc': 0}  # Track OI for change alerts

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

def check_cooldown(alert_type, minutes=60):
    """Check if alert is in cooldown"""
    now = time.time()
    key = f"{alert_type}_{datetime.now().strftime('%Y%m%d_%H')}"
    if key in cooldowns:
        if now - cooldowns[key] < minutes * 60:
            return False
    cooldowns[key] = now
    return True

async def get_binance_data():
    """Fetch Binance BTC data"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT") as resp:
                data = await resp.json()
                return {
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent']),
                }
    except Exception as e:
        print(f"[ERROR] Binance: {e}")
        return None

async def get_binance_funding():
    """Fetch Binance funding rate"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1") as resp:
                data = await resp.json()
                return float(data[0]['fundingRate']) if data else 0
    except Exception as e:
        print(f"[ERROR] Binance funding: {e}")
        return 0

async def get_hyperliquid_data():
    """Fetch Hyperliquid BTC data"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.hyperliquid.xyz/info', json={"type": "metaAndAssetCtxs"}) as resp:
                data = await resp.json()
                meta, ctxs = data[0], data[1]
                
                for i, asset in enumerate(meta['universe']):
                    if asset['name'] == 'BTC':
                        ctx = ctxs[i]
                        return {
                            'price': float(ctx['markPx']),
                            'funding': float(ctx['funding']),
                            'oi': float(ctx['openInterest']),
                            'volume': float(ctx['dayNtlVlm']),
                        }
    except Exception as e:
        print(f"[ERROR] Hyperliquid: {e}")
        return None

async def check_alerts(binance_data, binance_funding, hl_data):
    """Check all alert conditions"""
    alerts_sent = []
    
    # 1. Price level alerts
    btc_price = binance_data['price']
    if btc_price < THRESHOLDS['btc_support'] and check_cooldown('btc_support', 120):
        await send_message(
            f"🚨 <b>BTC Support Broken!</b>\n\n"
            f"Price: ${btc_price:,.2f}\n"
            f"Below $65K support!\n\n"
            f"Watch for liquidations..."
        )
        alerts_sent.append('btc_support')
    
    if btc_price > THRESHOLDS['btc_resistance'] and check_cooldown('btc_resistance', 120):
        await send_message(
            f"🚀 <b>BTC Resistance Broken!</b>\n\n"
            f"Price: ${btc_price:,.2f}\n"
            f"Above $75K!\n\n"
            f"Potential short squeeze..."
        )
        alerts_sent.append('btc_resistance')
    
    # 2. Funding rate alerts
    for exchange, funding in [('Binance', binance_funding), ('Hyperliquid', hl_data['funding'])]:
        if funding > THRESHOLDS['funding_extreme'] and check_cooldown(f'{exchange}_funding_high', 60):
            await send_message(
                f"📈 <b>High Funding: {exchange}</b>\n\n"
                f"BTC funding: {funding*100:.4f}%\n"
                f"Longs are paying shorts!"
            )
            alerts_sent.append(f'{exchange}_funding_high')
        
        if funding < -THRESHOLDS['funding_extreme'] and check_cooldown(f'{exchange}_funding_low', 60):
            await send_message(
                f"📉 <b>Negative Funding: {exchange}</b>\n\n"
                f"BTC funding: {funding*100:.4f}%\n"
                f"Shorts are paying longs!"
            )
            alerts_sent.append(f'{exchange}_funding_low')
        
        # Opportunity alert
        if funding < THRESHOLDS['funding_opportunity'] and check_cooldown(f'{exchange}_funding_opp', 240):
            await send_message(
                f"💰 <b>Funding Arb Opportunity!</b>\n\n"
                f"{exchange} BTC: {funding*100:.4f}%\n\n"
                f"Consider: Long perp (get paid) + Short spot"
            )
            alerts_sent.append(f'{exchange}_funding_opp')
    
    # 3. Large price move
    change = binance_data['change_24h']
    if abs(change) > THRESHOLDS['price_change_1h'] * 100 and check_cooldown('large_move', 60):
        emoji = "🚀" if change > 0 else "📉"
        await send_message(
            f"{emoji} <b>Large BTC Move</b>\n\n"
            f"24h change: {change:+.2f}%\n"
            f"Price: ${btc_price:,.2f}"
        )
        alerts_sent.append('large_move')
    
    # 4. Open Interest alerts
    global last_oi
    btc_price = binance_data['price']
    oi_contracts = hl_data['oi']  # Number of BTC contracts
    oi_notional = oi_contracts * btc_price  # Dollar value
    
    # Log current OI
    print(f"  OI: {oi_contracts:,.0f} BTC (${oi_notional/1e9:.2f}B notional)")
    
    # Check for OI spike (if we have previous data)
    if last_oi['hl_btc'] > 0:
        oi_change = (oi_notional - last_oi['hl_btc']) / last_oi['hl_btc']
        if abs(oi_change) > THRESHOLDS['oi_change_pct'] and check_cooldown('oi_spike', 60):
            direction = "📈 Rising" if oi_change > 0 else "📉 Falling"
            emoji = "🚨" if abs(oi_change) > 0.20 else "⚠️"
            await send_message(
                f"{emoji} <b>OI Spike Alert: Hyperliquid</b>\n\n"
                f"{direction} fast!\n"
                f"Change: {oi_change*100:+.1f}%\n"
                f"Current OI: {oi_contracts:,.0f} BTC\n"
                f"Notional: ${oi_notional/1e9:.2f}B\n\n"
                f"💡 High OI + Funding rate = Watch for squeeze"
            )
            alerts_sent.append('oi_spike')
    
    # Update last OI
    last_oi['hl_btc'] = oi_notional
    
    return alerts_sent

async def run_monitor():
    """Main monitoring loop"""
    print(f"[{datetime.now()}] Market Monitor Started")
    print(f"Monitoring: BTC price, Funding rates, Price levels")
    print(f"Check interval: 30 seconds")
    print(f"Alerts go to: {CHAT_ID}\n")
    
    # Send startup message
    await send_message(
        "🟢 <b>Alert Bot Started</b>\n\n"
        "Monitoring:\n"
        "• BTC price levels ($65K-$75K)\n"
        "• Funding rates (±0.1% alerts)\n"
        "• Arb opportunities (<-0.05%)\n"
        "• Large price moves (±5%)\n"
        "• OI spikes (±10% change)\n\n"
        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Check #{iteration}")
            
            # Fetch all data
            binance_data = await get_binance_data()
            binance_funding = await get_binance_funding()
            hl_data = await get_hyperliquid_data()
            
            if binance_data and hl_data:
                # Calculate OI for display
                oi_contracts = hl_data['oi']
                oi_notional = oi_contracts * binance_data['price']
                
                # Check alerts
                alerts = await check_alerts(binance_data, binance_funding, hl_data)
                if alerts:
                    print(f"  Alerts sent: {', '.join(alerts)}")
                else:
                    print(f"  BTC: ${binance_data['price']:,.0f} | OI: {oi_contracts:,.0f} BTC (${oi_notional/1e9:.2f}B)")
            else:
                print(f"  ⚠️ Data fetch failed")
            
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        await asyncio.sleep(5)  # 5 second intervals

if __name__ == "__main__":
    asyncio.run(run_monitor())
