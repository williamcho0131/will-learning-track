#!/usr/bin/env python3
"""
Simplified test script using direct HTTP requests
No complex telegram library dependencies
"""

import asyncio
import aiohttp
import os
from datetime import datetime

# Config
TOKEN = "8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA"
CHAT_ID = "-1003832962281"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

print(f"🧪 Testing Alert Bot")
print(f"Token: {TOKEN[:20]}...")
print(f"Chat ID: {CHAT_ID}")
print("="*50)

async def send_telegram_message(text, parse_mode="HTML"):
    """Send message via Telegram Bot API"""
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                error = await resp.text()
                raise Exception(f"Telegram API error: {error}")

async def test_telegram():
    """Test Telegram connectivity"""
    print("\n📱 Test 1: Telegram Bot Connectivity")
    try:
        # Get bot info
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/getMe") as resp:
                data = await resp.json()
                if data.get('ok'):
                    bot_info = data['result']
                    print(f"   ✅ Bot connected: @{bot_info['username']}")
                else:
                    print(f"   ❌ Bot error: {data}")
                    return False
        
        # Send test message
        await send_telegram_message(
            f"🧪 <b>Alert Bot Test</b>\n\n"
            f"✅ Connected successfully!\n"
            f"Bot is live and monitoring markets.\n\n"
            f"<i>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</i>"
        )
        print(f"   ✅ Test message sent to chat {CHAT_ID}")
        return True
    except Exception as e:
        print(f"   ❌ Telegram error: {e}")
        return False

async def test_binance():
    """Test Binance API"""
    print("\n📊 Test 2: Binance API (Free)")
    try:
        async with aiohttp.ClientSession() as session:
            # Get BTC price
            async with session.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT") as resp:
                data = await resp.json()
                btc_price = float(data['lastPrice'])
                btc_change = float(data['priceChangePercent'])
                print(f"   ✅ BTC/USDT: ${btc_price:,.2f} ({btc_change:+.2f}%)")
                
            # Get funding rate
            async with session.get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1") as resp:
                funding_data = await resp.json()
                if funding_data:
                    funding_rate = float(funding_data[0]['fundingRate'])
                    print(f"   ✅ Funding rate: {funding_rate*100:.4f}%")
                else:
                    funding_rate = 0
                    print(f"   ⚠️  No funding data")
                
        return {'price': btc_price, 'funding': funding_rate, 'change': btc_change}
    except Exception as e:
        print(f"   ❌ Binance error: {e}")
        return None

async def test_hyperliquid():
    """Test Hyperliquid API"""
    print("\n⛓️ Test 3: Hyperliquid API (Free)")
    try:
        async with aiohttp.ClientSession() as session:
            # Get meta and asset contexts
            async with session.post(
                'https://api.hyperliquid.xyz/info',
                json={"type": "metaAndAssetCtxs"}
            ) as resp:
                data = await resp.json()
                
                meta = data[0]
                asset_ctxs = data[1]
                
                # Find BTC index
                btc_idx = None
                for i, asset in enumerate(meta['universe']):
                    if asset['name'] == 'BTC':
                        btc_idx = i
                        break
                
                if btc_idx is not None:
                    ctx = asset_ctxs[btc_idx]
                    price = float(ctx['markPx'])
                    funding = float(ctx['funding'])
                    oi = float(ctx['openInterest'])
                    volume = float(ctx['dayNtlVlm'])
                    
                    print(f"   ✅ BTC-PERP: ${price:,.2f}")
                    print(f"   ✅ Funding: {funding*100:.4f}%")
                    print(f"   ✅ Open Interest: ${oi:,.0f}")
                    print(f"   ✅ 24h Volume: ${volume/1e6:.1f}M")
                    
                    return {
                        'price': price,
                        'funding': funding,
                        'oi': oi,
                        'volume': volume
                    }
                else:
                    print("   ❌ BTC not found")
                    return None
                    
    except Exception as e:
        print(f"   ❌ Hyperliquid error: {e}")
        return None

async def check_funding_arb(binance_data, hl_data):
    """Check for arbitrage opportunities"""
    print("\n💰 Test 4: Funding Arbitrage Scan")
    
    if not binance_data or not hl_data:
        print("   ⚠️  Missing data")
        return False
    
    binance_funding = binance_data['funding']
    hl_funding = hl_data['funding']
    spread = abs(binance_funding - hl_funding)
    
    print(f"   Binance: {binance_funding*100:.4f}%")
    print(f"   Hyperliquid: {hl_funding*100:.4f}%")
    print(f"   Spread: {spread*100:.4f}%")
    
    # Check thresholds
    opportunities = []
    if binance_funding < -0.0005:
        opportunities.append(f"📉 Binance: {binance_funding*100:.4f}% (PAID to long)")
    if hl_funding < -0.0005:
        opportunities.append(f"📉 Hyperliquid: {hl_funding*100:.4f}% (PAID to long)")
    if spread > 0.0003:
        opportunities.append(f"🔄 Spread arb: {spread*100:.4f}% difference")
    
    if opportunities:
        print(f"   ✅ Opportunities found!")
        for opp in opportunities:
            print(f"      {opp}")
        
        # Send alert
        try:
            msg = "🚨 <b>Funding Alert</b>\n\n" + "\n".join(opportunities)
            msg += f"\n\n<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>"
            await send_telegram_message(msg)
            print(f"   📱 Alert sent!")
        except Exception as e:
            print(f"   ❌ Alert failed: {e}")
        return True
    else:
        print(f"   ℹ️ No opportunities (threshold: ±0.05%)")
        return False

async def send_summary(binance_data, hl_data):
    """Send market summary"""
    print("\n📰 Test 5: Market Summary")
    
    try:
        msg = f"""📊 <b>Alert Bot is LIVE 🚀</b>

<b>BTC Market Snapshot:</b>
• Binance: ${binance_data['price']:,.2f} ({binance_data['change']:+.2f}%)
• Hyperliquid: ${hl_data['price']:,.2f}
• Spread: ${abs(binance_data['price'] - hl_data['price']):,.2f}

<b>Funding Rates:</b>
• Binance: {binance_data['funding']*100:.4f}%
• Hyperliquid: {hl_data['funding']*100:.4f}%

<b>Hyperliquid Stats:</b>
• OI: ${hl_data['oi']/1e6:.1f}M
• 24h Vol: ${hl_data['volume']/1e6:.1f}M

<i>Monitoring 24/7 for opportunities...</i>
"""
        await send_telegram_message(msg)
        print(f"   ✅ Summary sent to Telegram")
        
    except Exception as e:
        print(f"   ❌ Summary failed: {e}")

async def main():
    print("\n" + "="*50)
    print("Starting tests...\n")
    
    # Test 1: Telegram
    telegram_ok = await test_telegram()
    
    # Test 2: Binance
    binance_data = await test_binance()
    
    # Test 3: Hyperliquid
    hl_data = await test_hyperliquid()
    
    # Test 4: Funding arb
    await check_funding_arb(binance_data, hl_data)
    
    # Test 5: Summary
    if telegram_ok and binance_data and hl_data:
        await send_summary(binance_data, hl_data)
    
    print("\n" + "="*50)
    print("✅ All tests completed!")
    
    if telegram_ok:
        print("\n🚀 Alert bot is ready!")
        print("To run continuous monitoring:")
        print("  nohup python3 market_monitor_simple.py &")
    else:
        print("\n⚠️  Fix Telegram issues before running")

if __name__ == "__main__":
    asyncio.run(main())
