#!/usr/bin/env python3
"""
Test script for Market Alert Bot
Tests Telegram connectivity and basic data fetching
"""

import asyncio
import os
from datetime import datetime
from telegram import Bot
import ccxt
import aiohttp
import json

# Load env
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')

print(f"🧪 Testing Alert Bot")
print(f"Token: {TOKEN[:20]}...")
print(f"Chat ID: {CHAT_ID}")
print("="*50)

async def test_telegram():
    """Test Telegram bot connectivity"""
    print("\n📱 Test 1: Telegram Bot Connectivity")
    try:
        bot = Bot(token=TOKEN)
        me = await bot.get_me()
        print(f"   ✅ Bot connected: @{me.username}")
        
        # Send test message
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"🧪 <b>Alert Bot Test</b>\n\nConnected successfully!\nBot: @{me.username}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            parse_mode='HTML'
        )
        print(f"   ✅ Test message sent to chat {CHAT_ID}")
        return True
    except Exception as e:
        print(f"   ❌ Telegram error: {e}")
        return False

async def test_binance():
    """Test Binance API connectivity"""
    print("\n📊 Test 2: Binance API (Free)")
    try:
        binance = ccxt.binance({'enableRateLimit': True})
        
        # Get BTC price
        ticker = binance.fetch_ticker('BTC/USDT')
        btc_price = ticker['last']
        print(f"   ✅ BTC/USDT: ${btc_price:,.2f}")
        
        # Get funding rate
        try:
            funding = binance.fetchFundingRate('BTC/USDT')
            funding_rate = funding.get('fundingRate', 0)
            print(f"   ✅ Funding rate: {funding_rate*100:.4f}%")
        except Exception as e:
            print(f"   ⚠️  Funding rate not available via ccxt: {e}")
            funding_rate = 0
        
        return {'price': btc_price, 'funding': funding_rate}
    except Exception as e:
        print(f"   ❌ Binance error: {e}")
        return None

async def test_hyperliquid():
    """Test Hyperliquid API connectivity"""
    print("\n⛓️ Test 3: Hyperliquid API (Free)")
    try:
        async with aiohttp.ClientSession() as session:
            # Get all asset contexts
            async with session.post(
                'https://api.hyperliquid.xyz/info',
                json={"type": "metaAndAssetCtxs"}
            ) as resp:
                data = await resp.json()
                
                # Parse BTC data
                meta = data[0]
                asset_ctxs = data[1]
                
                # Find BTC
                btc_idx = None
                for i, asset in enumerate(meta['universe']):
                    if asset['name'] == 'BTC':
                        btc_idx = i
                        break
                
                if btc_idx is not None:
                    btc_ctx = asset_ctxs[btc_idx]
                    btc_price = float(btc_ctx['markPx'])
                    funding_rate = float(btc_ctx['funding'])
                    open_interest = float(btc_ctx['openInterest'])
                    
                    print(f"   ✅ BTC-PERP: ${btc_price:,.2f}")
                    print(f"   ✅ Funding: {funding_rate*100:.4f}%")
                    print(f"   ✅ Open Interest: ${open_interest:,.0f}")
                    
                    return {
                        'price': btc_price,
                        'funding': funding_rate,
                        'oi': open_interest
                    }
                else:
                    print("   ⚠️  BTC not found in response")
                    return None
                    
    except Exception as e:
        print(f"   ❌ Hyperliquid error: {e}")
        return None

async def test_funding_arbitrage(binance_data, hyperliquid_data):
    """Check for funding arbitrage opportunities"""
    print("\n💰 Test 4: Funding Arbitrage Scan")
    
    if not binance_data or not hyperliquid_data:
        print("   ⚠️  Missing data from one exchange")
        return
    
    binance_funding = binance_data.get('funding', 0)
    hl_funding = hyperliquid_data.get('funding', 0)
    
    print(f"   Binance: {binance_funding*100:.4f}%")
    print(f"   Hyperliquid: {hl_funding*100:.4f}%")
    print(f"   Spread: {abs(binance_funding - hl_funding)*100:.4f}%")
    
    # Check for opportunity
    threshold = -0.0005  # -0.05%
    opportunities = []
    
    if binance_funding < threshold:
        opportunities.append(f"📉 Binance BTC: {binance_funding*100:.4f}% (PAID to long)")
    if hl_funding < threshold:
        opportunities.append(f"📉 Hyperliquid BTC: {hl_funding*100:.4f}% (PAID to long)")
    
    if opportunities:
        print(f"   ✅ Opportunities found!")
        for opp in opportunities:
            print(f"      {opp}")
        
        # Send alert
        try:
            bot = Bot(token=TOKEN)
            message = "🎯 <b>Funding Arb Opportunity Detected</b>\n\n" + "\n".join(opportunities)
            message += f"\n\n<i>Scan time: {datetime.now().strftime('%H:%M:%S')} UTC</i>"
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
            print(f"   📱 Alert sent to Telegram")
        except Exception as e:
            print(f"   ❌ Failed to send alert: {e}")
    else:
        print(f"   ℹ️ No arb opportunities right now (threshold: -0.05%)")

async def send_market_summary(binance_data, hyperliquid_data):
    """Send a nice market summary"""
    print("\n📰 Test 5: Market Summary")
    
    try:
        bot = Bot(token=TOKEN)
        
        btc_binance = binance_data['price'] if binance_data else 0
        btc_hl = hyperliquid_data['price'] if hyperliquid_data else 0
        hl_funding = hyperliquid_data['funding']*100 if hyperliquid_data else 0
        
        message = f"""📊 <b>Market Snapshot</b>

<b>BTC Prices:</b>
• Binance Spot: ${btc_binance:,.2f}
• Hyperliquid Perp: ${btc_hl:,.2f}
• Spread: ${abs(btc_binance - btc_hl):,.2f}

<b>Hyperliquid BTC-PERP:</b>
• Funding: {hl_funding:.4f}%
• Open Interest: ${hyperliquid_data['oi']/1e6:.1f}M

<i>Alert bot is live! 🚀</i>
"""
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        print(f"   ✅ Market summary sent")
        
    except Exception as e:
        print(f"   ❌ Failed to send summary: {e}")

async def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("Starting tests...\n")
    
    # Test 1: Telegram
    telegram_ok = await test_telegram()
    
    # Test 2: Binance
    binance_data = await test_binance()
    
    # Test 3: Hyperliquid
    hyperliquid_data = await test_hyperliquid()
    
    # Test 4: Funding arb scan
    await test_funding_arbitrage(binance_data, hyperliquid_data)
    
    # Test 5: Market summary
    if telegram_ok:
        await send_market_summary(binance_data, hyperliquid_data)
    
    print("\n" + "="*50)
    print("✅ All tests completed!")
    print("\nTo run the full alert bot:")
    print("  export TELEGRAM_BOT_TOKEN='your_token'")
    print("  export TELEGRAM_CHAT_ID='your_chat_id'")
    print("  python3 market_monitor.py")

if __name__ == "__main__":
    asyncio.run(main())
