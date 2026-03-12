#!/usr/bin/env python3
"""
Funding Arbitrage Alert Bot
Reusable scanner for funding rate opportunities
"""

import asyncio
import aiohttp
import os
import yaml
import sys
from datetime import datetime
import time
from typing import Dict, List, Optional, Tuple

# Load config
CONFIG_PATH = os.getenv('FUNDING_BOT_CONFIG', 'config.yaml')

def load_config():
    """Load configuration from YAML or environment"""
    config = {
        'telegram': {
            'token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
        },
        'exchanges': ['binance', 'hyperliquid'],
        'thresholds': {
            'major': 0.0008,
            'mid': 0.0012,
            'alt': 0.0020,
            'exotic': 0.0030,
        },
        'scanning': {
            'interval_seconds': 5,
            'cooldown_minutes': 30,
        },
        'assets': {
            'include_all': True,
            'whitelist': [],
        }
    }
    
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config.update(file_config)
    
    return config

# Asset classification
ASSET_CLASS = {
    'BTC': 'major', 'ETH': 'major',
    'SOL': 'mid', 'LINK': 'mid', 'ARB': 'mid', 'AVAX': 'mid',
    'DOGE': 'alt', 'HYPE': 'alt', 'PEPE': 'alt', 'SHIB': 'alt',
}

def get_asset_class(symbol: str) -> str:
    """Classify asset by market cap/liquidity"""
    base = symbol.replace('USDT', '').replace('USD', '').replace('-PERP', '')
    return ASSET_CLASS.get(base, 'mid')

def get_liquidity_factor(asset_class: str) -> float:
    """Get liquidity multiplier for scoring"""
    factors = {'major': 1.0, 'mid': 0.7, 'alt': 0.5, 'exotic': 0.3}
    return factors.get(asset_class, 0.5)

class TelegramNotifier:
    """Telegram notification handler"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    async def send_message(self, text: str) -> bool:
        """Send Telegram message"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                async with session.post(url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"[ERROR] Telegram failed: {e}")
            return False

class ExchangeAPI:
    """Exchange API wrapper"""
    
    @staticmethod
    async def get_binance_perps() -> Dict:
        """Fetch ALL perpetual markets from Binance"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get funding rates
                async with session.get("https://fapi.binance.com/fapi/v1/premiumIndex") as resp:
                    funding_data = await resp.json()
                
                # Get 24h ticker
                async with session.get("https://fapi.binance.com/fapi/v1/ticker/24hr") as resp:
                    tickers = {t['symbol']: t for t in await resp.json()}
                
                perps = {}
                for item in funding_data:
                    symbol = item['symbol']
                    if not symbol.endswith('USDT'):
                        continue
                    
                    ticker = tickers.get(symbol, {})
                    perps[symbol] = {
                        'funding': float(item.get('lastFundingRate', 0)),
                        'price': float(item['markPrice']),
                        'volume': float(ticker.get('quoteVolume', 0)),
                        'change_24h': float(ticker.get('priceChangePercent', 0)),
                    }
                return perps
        except Exception as e:
            print(f"[ERROR] Binance API: {e}")
            return {}
    
    @staticmethod
    async def get_hyperliquid_perps() -> Dict:
        """Fetch ALL perpetual markets from Hyperliquid"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.hyperliquid.xyz/info',
                    json={"type": "metaAndAssetCtxs"}
                ) as resp:
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
                    }
                return perps
        except Exception as e:
            print(f"[ERROR] Hyperliquid API: {e}")
            return {}

class OpportunityAnalyzer:
    """Analyze and score arbitrage opportunities"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cooldowns = {}
    
    def check_cooldown(self, asset: str, minutes: int = 30) -> bool:
        """Check if alert is in cooldown"""
        now = time.time()
        key = f"{asset}_alert"
        if key in self.cooldowns:
            if now - self.cooldowns[key] < minutes * 60:
                return False
        self.cooldowns[key] = now
        return True
    
    def calculate_score(self, asset: str, binance_data: Dict, hl_data: Dict) -> Optional[Dict]:
        """Calculate opportunity score"""
        if not binance_data or not hl_data:
            return None
        
        asset_class = get_asset_class(asset)
        min_spread = self.config['thresholds'].get(asset_class, 0.001)
        liquidity_factor = get_liquidity_factor(asset_class)
        
        # Calculate spread
        spread = abs(binance_data['funding'] - hl_data['funding'])
        
        if spread < min_spread:
            return None
        
        # Calculate notional OI
        oi_notional = hl_data.get('oi', 0) * hl_data.get('price', 0)
        
        # Score formula
        score = spread * liquidity_factor * (oi_notional / 1e9)
        
        # Determine best side
        if binance_data['funding'] < hl_data['funding']:
            best_long = 'Binance'
            best_short = 'Hyperliquid'
            long_funding = binance_data['funding']
            short_funding = hl_data['funding']
        else:
            best_long = 'Hyperliquid'
            best_short = 'Binance'
            long_funding = hl_data['funding']
            short_funding = binance_data['funding']
        
        return {
            'asset': asset,
            'spread': spread,
            'score': score,
            'asset_class': asset_class,
            'binance_funding': binance_data['funding'],
            'hl_funding': hl_data['funding'],
            'binance_price': binance_data['price'],
            'hl_price': hl_data['price'],
            'oi_notional': oi_notional,
            'volume': hl_data.get('volume', 0) + binance_data.get('volume', 0),
            'best_long': best_long,
            'best_short': best_short,
            'long_funding': long_funding,
            'short_funding': short_funding,
            'threshold': min_spread,
        }

class FundingArbBot:
    """Main bot class"""
    
    def __init__(self):
        self.config = load_config()
        self.notifier = TelegramNotifier(
            self.config['telegram']['token'],
            self.config['telegram']['chat_id']
        )
        self.analyzer = OpportunityAnalyzer(self.config)
        self.scan_count = 0
    
    async def send_opportunity_alert(self, opp: Dict):
        """Send HIGH priority opportunity alert"""
        spread_pct = opp['spread'] * 100
        
        message = f"""🔥 <b>HIGH PRIORITY ARB: {opp['asset']}</b>

Funding Spread: {spread_pct:.4f}% (threshold: {opp['threshold']*100:.2f}%)

<b>Funding Rates:</b>
• Binance: {opp['binance_funding']*100:.4f}%
• Hyperliquid: {opp['hl_funding']*100:.4f}%

<b>Trade Setup:</b>
💚 Long on {opp['best_long']}: {opp['long_funding']*100:.4f}%
❤️ Short on {opp['best_short']}: {opp['short_funding']*100:.4f}%

<b>Market Data:</b>
• OI: ${opp['oi_notional']/1e6:.1f}M
• Volume: ${opp['volume']/1e6:.1f}M
• Score: {opp['score']:.3f}

⏰ Next funding: ~8 hours
<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>
"""
        await self.notifier.send_message(message)
        print(f"  🔥 ALERT SENT: {opp['asset']} (score: {opp['score']:.3f})")
    
    async def send_summary(self, opportunities: List[Dict]):
        """Send summary of top opportunities"""
        if not opportunities:
            return
        
        lines = [f"📊 <b>Top {min(3, len(opportunities))} Opportunities</b>\n"]
        
        for i, opp in enumerate(opportunities[:3], 1):
            spread_pct = opp['spread'] * 100
            lines.append(f"{i}. {opp['asset']}: {spread_pct:.4f}% spread (score: {opp['score']:.2f})")
        
        message = "\n".join(lines)
        await self.notifier.send_message(message)
    
    async def scan(self):
        """Run one scan cycle"""
        self.scan_count += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scan #{self.scan_count}")
        
        # Fetch data
        binance_perps = await ExchangeAPI.get_binance_perps()
        hl_perps = await ExchangeAPI.get_hyperliquid_perps()
        
        print(f"  Binance: {len(binance_perps)} markets")
        print(f"  Hyperliquid: {len(hl_perps)} markets")
        
        # Find common assets
        common = set(binance_perps.keys()) & set(hl_perps.keys())
        print(f"  Common: {len(common)} assets")
        
        # Analyze opportunities
        opportunities = []
        for asset in common:
            opp = self.analyzer.calculate_score(
                asset,
                binance_perps[asset],
                hl_perps[asset]
            )
            if opp:
                opportunities.append(opp)
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        if opportunities:
            print(f"  Found {len(opportunities)} opportunities")
            
            # Send HIGH priority alerts
            high_priority = [o for o in opportunities if o['score'] > 0.05]
            for opp in high_priority:
                if self.analyzer.check_cooldown(opp['asset'], 30):
                    await self.send_opportunity_alert(opp)
            
            # Send summary every 10 scans
            if self.scan_count % 10 == 0:
                await self.send_summary(opportunities)
        else:
            print(f"  No opportunities above threshold")
            # Show top spreads for monitoring
            all_spreads = []
            for asset in list(common)[:20]:
                spread = abs(binance_perps[asset]['funding'] - hl_perps[asset]['funding'])
                all_spreads.append((asset, spread * 100))
            all_spreads.sort(key=lambda x: x[1], reverse=True)
            if all_spreads:
                print(f"  Top spreads: {all_spreads[:3]}")
    
    async def run(self):
        """Main loop"""
        print("="*60)
        print("🚀 Funding Arbitrage Alert Bot")
        print("="*60)
        print(f"Scanning: ALL perpetual markets")
        print(f"Exchanges: {', '.join(self.config['exchanges'])}")
        print(f"Alert threshold: Score > 0.05")
        print(f"Scan interval: {self.config['scanning']['interval_seconds']}s")
        print("="*60)
        
        # Send startup message
        await self.notifier.send_message(
            f"🟢 <b>Funding Arb Bot Started</b>\n\n"
            f"Scanning: {len(self.config['exchanges'])} exchanges\n"
            f"Markets: ALL perpetuals\n"
            f"Ranking: By opportunity score\n\n"
            f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        
        while True:
            try:
                await self.scan()
            except Exception as e:
                print(f"[ERROR] Scan failed: {e}")
            
            await asyncio.sleep(self.config['scanning']['interval_seconds'])

async def main():
    """Entry point"""
    bot = FundingArbBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
        sys.exit(0)
