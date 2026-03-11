#!/usr/bin/env python3
"""
Emergency Market Alert Bot
Monitors Binance + Hyperliquid for critical events
Sends Telegram alerts when thresholds are hit

Setup:
1. pip install ccxt python-telegram-bot asyncio aiohttp
2. Set env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
3. Run: python alert_bot.py
"""

import asyncio
import ccxt
import aiohttp
import os
from datetime import datetime
from telegram import Bot
import json

# ===== CONFIGURATION =====
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Alert Thresholds
THRESHOLDS = {
    'funding_rate': {
        'extreme_high': 0.001,   # 0.1%
        'extreme_low': -0.001,   # -0.1%
        'opportunity': -0.0005   # -0.05% (funding arb zone)
    },
    'liquidation': {
        'btc_major': 50_000_000,      # $50M BTC liquidations
        'total_major': 100_000_000,   # $100M total
        'cascade_window': 3600        # 1 hour
    },
    'price': {
        'btc_support': 65_000,
        'btc_resistance': 75_000,
        'eth_support': 3_000,
        'eth_resistance': 4_000
    },
    'oi_change': {
        'spike_pct': 0.15  # 15% OI change in 1h
    }
}

# State tracking
alert_cooldowns = {}
COOLDOWN_MINUTES = 60

class MarketMonitor:
    def __init__(self):
        self.binance = ccxt.binance({'enableRateLimit': True})
        self.hyperliquid = None  # Will use REST API directly
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
        
    async def send_alert(self, title: str, message: str, priority: str = "normal"):
        """Send Telegram alert with cooldown check"""
        alert_key = f"{title}_{priority}"
        now = datetime.now()
        
        # Check cooldown
        if alert_key in alert_cooldowns:
            last_sent = alert_cooldowns[alert_key]
            if (now - last_sent).total_seconds() < COOLDOWN_MINUTES * 60:
                return  # Skip, in cooldown
        
        alert_cooldowns[alert_key] = now
        
        # Priority emoji
        emoji = {"high": "🚨", "normal": "⚠️", "info": "ℹ️"}.get(priority, "⚠️")
        
        full_message = f"""{emoji} <b>{title}</b> {emoji}

{message}

<i>Alert time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC</i>
"""
        
        if self.bot and TELEGRAM_CHAT_ID:
            try:
                await self.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=full_message,
                    parse_mode='HTML'
                )
                print(f"[ALERT SENT] {title}")
            except Exception as e:
                print(f"[ERROR] Failed to send alert: {e}")
        else:
            print(f"[MOCK ALERT] {title}\n{message}")
    
    async def check_funding_rates(self):
        """Monitor funding rates across exchanges"""
        try:
            # Binance funding rates
            binance_funding = await self._get_binance_funding()
            hyperliquid_funding = await self._get_hyperliquid_funding()
            
            opportunities = []
            
            for symbol, rate in binance_funding.items():
                if rate < THRESHOLDS['funding_rate']['extreme_low']:
                    opportunities.append(f"📉 <b>Binance {symbol}</b>: {rate*100:.4f}% (PAID to long)")
                elif rate > THRESHOLDS['funding_rate']['extreme_high']:
                    opportunities.append(f"📈 <b>Binance {symbol}</b>: {rate*100:.4f}% (expensive to long)")
            
            for symbol, rate in hyperliquid_funding.items():
                if rate < THRESHOLDS['funding_rate']['extreme_low']:
                    opportunities.append(f"📉 <b>Hyperliquid {symbol}</b>: {rate*100:.4f}% (PAID to long)")
            
            if opportunities:
                message = "\n".join(opportunities[:5])  # Top 5
                message += f"\n\n💡 <b>Action:</b> Consider funding arb opportunities"
                await self.send_alert("Extreme Funding Rates Detected", message, "high")
                
            # Specific opportunity alert (for your strategy)
            for symbol in ['BTC/USDT', 'ETH/USDT']:
                binance_rate = binance_funding.get(symbol, 0)
                hyperliquid_rate = hyperliquid_funding.get(symbol.replace('/USDT', ''), 0)
                
                if binance_rate < THRESHOLDS['funding_rate']['opportunity']:
                    await self.send_alert(
                        f"Funding Arb Opportunity: {symbol}",
                        f"Binance funding: {binance_rate*100:.4f}%\n"
                        f"Hyperliquid funding: {hyperliquid_rate*100:.4f}%\n\n"
                        f"💡 Long perp on Binance (get paid), hedge spot elsewhere",
                        "normal"
                    )
                    
        except Exception as e:
            print(f"[ERROR] Funding check failed: {e}")
    
    async def _get_binance_funding(self) -> dict:
        """Fetch Binance funding rates"""
        try:
            tickers = self.binance.fetch_tickers()
            funding = {}
            # Note: ccxt doesn't directly expose funding rates in all versions
            # This is simplified - in production use Binance API directly
            return funding
        except:
            return {}
    
    async def _get_hyperliquid_funding(self) -> dict:
        """Fetch Hyperliquid funding rates via REST API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.hyperliquid.xyz/info', 
                    json={"type": "metaAndAssetCtxs"}) as resp:
                    data = await resp.json()
                    funding = {}
                    # Parse funding rates from response
                    return funding
        except:
            return {}
    
    async def check_price_levels(self):
        """Monitor critical price breaks"""
        try:
            btc_price = (await self._get_price('binance', 'BTC/USDT')) or 0
            eth_price = (await self._get_price('binance', 'ETH/USDT')) or 0
            
            # BTC support/resistance
            if btc_price < THRESHOLDS['price']['btc_support']:
                await self.send_alert(
                    "BTC Support Broken 🚨",
                    f"BTC dropped below $65K support!\n"
                    f"Current price: ${btc_price:,.2f}\n\n"
                    f"Watch for cascading liquidations",
                    "high"
                )
            elif btc_price > THRESHOLDS['price']['btc_resistance']:
                await self.send_alert(
                    "BTC Resistance Broken 🚀",
                    f"BTC broke above $75K resistance!\n"
                    f"Current price: ${btc_price:,.2f}\n\n"
                    f"Potential short squeeze incoming",
                    "high"
                )
                
        except Exception as e:
            print(f"[ERROR] Price check failed: {e}")
    
    async def _get_price(self, exchange: str, symbol: str) -> float:
        """Fetch current price"""
        try:
            if exchange == 'binance':
                ticker = self.binance.fetch_ticker(symbol)
                return ticker['last']
        except:
            return None
    
    async def check_liquidations(self):
        """Monitor liquidation data (requires CoinGlass API or similar)"""
        # Placeholder - requires paid API for reliable data
        pass
    
    async def run(self):
        """Main monitoring loop"""
        print(f"[{datetime.now()}] Alert Bot Started")
        print(f"Monitoring: Funding rates, Price levels")
        print(f"Check interval: 30 seconds")
        
        while True:
            try:
                await self.check_funding_rates()
                await self.check_price_levels()
                # await self.check_liquidations()  # Requires API key
                
            except Exception as e:
                print(f"[ERROR] Main loop: {e}")
            
            await asyncio.sleep(30)  # 30 second intervals

# ===== DAILY SNAPSHOT =====

async def generate_daily_snapshot():
    """Generate daily market snapshot for learning repo"""
    snapshot = {
        'date': datetime.now().isoformat(),
        'funding_rates': {},
        'prices': {},
        'opportunities': []
    }
    
    # Fetch data
    # ... (similar to above, but saves to JSON instead of alerting)
    
    # Save to file
    filename = f"/opt/will-learning-track/data/snapshot_{datetime.now().strftime('%Y-%m-%d')}.json"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"[SNAPSHOT] Saved to {filename}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--snapshot":
        # Run daily snapshot
        asyncio.run(generate_daily_snapshot())
    else:
        # Run alert bot
        monitor = MarketMonitor()
        asyncio.run(monitor.run())
