#!/usr/bin/env python3
"""
Polymarket Cross-Market Arbitrage Bot
Detects probability discrepancies across similar events
"""

import asyncio
import aiohttp
import os
from datetime import datetime

# Config
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '-1003832962281')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# Minimum edge to alert (probability difference)
MIN_EDGE = 0.05  # 5% difference
MIN_LIQUIDITY = 10000  # $10k minimum liquidity

class PolymarketAPI:
    """Polymarket data fetcher"""
    
    BASE_URL = "https://gamma-api.polymarket.com"
    
    @staticmethod
    async def get_active_markets():
        """Fetch all active markets"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{PolymarketAPI.BASE_URL}/markets?active=true&closed=false"
                async with session.get(url) as resp:
                    return await resp.json()
        except Exception as e:
            print(f"[ERROR] Polymarket API: {e}")
            return []
    
    @staticmethod
    async def get_market_details(market_id):
        """Get detailed market info"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{PolymarketAPI.BASE_URL}/markets/{market_id}"
                async with session.get(url) as resp:
                    return await resp.json()
        except Exception as e:
            print(f"[ERROR] Market details: {e}")
            return None

class ArbitrageDetector:
    """Detect arbitrage opportunities across related markets"""
    
    def __init__(self):
        self.opportunities = []
    
    def find_related_markets(self, markets):
        """Group related markets by category/topic"""
        categories = {}
        
        for market in markets:
            # Extract category from tags or description
            tags = market.get('tags', [])
            category = self._categorize_market(market, tags)
            
            if category not in categories:
                categories[category] = []
            categories[category].append(market)
        
        return categories
    
    def _categorize_market(self, market, tags):
        """Categorize market by topic"""
        title = market.get('question', '').lower()
        
        # Political events
        if any(word in title for word in ['election', 'trump', 'biden', 'vote']):
            return 'politics'
        
        # Crypto
        if any(word in title for word in ['bitcoin', 'eth', 'crypto', 'etf', 'sec']):
            return 'crypto'
        
        # Sports
        if any(word in title for word in ['super bowl', 'nba', 'world cup', 'olympics']):
            return 'sports'
        
        # Economic
        if any(word in title for word in ['fed', 'interest rate', 'inflation', 'recession']):
            return 'economics'
        
        return 'other'
    
    def calculate_implied_probabilities(self, markets):
        """Calculate implied probabilities from market prices"""
        probs = {}
        
        for market in markets:
            if market.get('liquidity', 0) < MIN_LIQUIDITY:
                continue
            
            # Get best yes/no prices
            outcomes = market.get('outcomes', [])
            if len(outcomes) >= 2:
                yes_price = outcomes[0].get('price', 0)
                no_price = outcomes[1].get('price', 0)
                
                # Implied probability from yes price
                prob = yes_price
                probs[market['id']] = {
                    'question': market['question'],
                    'probability': prob,
                    'liquidity': market.get('liquidity', 0),
                    'volume': market.get('volume', 0),
                }
        
        return probs
    
    def find_arbitrage(self, category, markets):
        """Find arbitrage within a category"""
        opportunities = []
        probs = self.calculate_implied_probabilities(markets)
        
        # Check for complementary events
        # Example: "Will Trump win?" vs "Will Biden win?" should sum to ~100%
        # If Trump 60% + Biden 50% = 110%, there's arbitrage
        
        market_list = list(probs.items())
        for i, (id1, m1) in enumerate(market_list):
            for id2, m2 in market_list[i+1:]:
                # Check if markets are related (simplified)
                if self._are_related(m1['question'], m2['question']):
                    diff = abs(m1['probability'] - m2['probability'])
                    
                    if diff >= MIN_EDGE:
                        opportunities.append({
                            'market1': m1,
                            'market2': m2,
                            'diff': diff,
                            'category': category,
                        })
        
        return opportunities
    
    def _are_related(self, q1, q2):
        """Check if two market questions are related"""
        # Simple keyword matching - can be improved with NLP
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())
        
        # Common meaningful words (excluding stop words)
        stop_words = {'will', 'the', 'a', 'an', 'in', 'on', 'at', 'by', 'to', 'of'}
        common = (words1 & words2) - stop_words
        
        return len(common) >= 2  # At least 2 common keywords

class PolymarketArbBot:
    """Main bot"""
    
    def __init__(self):
        self.detector = ArbitrageDetector()
    
    async def send_alert(self, opp):
        """Send arbitrage opportunity alert"""
        m1, m2 = opp['market1'], opp['market2']
        
        message = f"""💰 <b>Polymarket Arbitrage Opportunity</b>

<b>Category:</b> {opp['category'].upper()}
<b>Edge:</b> {opp['diff']*100:.1f}%

<b>Market A:</b>
{m1['question'][:100]}...
• Probability: {m1['probability']*100:.1f}%
• Liquidity: ${m1['liquidity']:,.0f}

<b>Market B:</b>
{m2['question'][:100]}...
• Probability: {m2['probability']*100:.1f}%
• Liquidity: ${m2['liquidity']:,.0f}

<b>Strategy:</b>
Buy YES on lower prob, NO on higher prob
(or vice versa depending on market structure)

⚠️ Check market rules carefully before trading
<i>{datetime.now().strftime('%H:%M:%S')} UTC</i>
"""
        
        url = f"{BASE_URL}/sendMessage"
        async with aiohttp.ClientSession() as session:
            await session.post(url, json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            })
        
        print(f"  💰 Arbitrage: {opp['diff']*100:.1f}% edge in {opp['category']}")
    
    async def scan(self):
        """Run one scan cycle"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning Polymarket...")
        
        # Get all markets
        markets = await PolymarketAPI.get_active_markets()
        print(f"  Found {len(markets)} active markets")
        
        # Categorize
        categories = self.detector.find_related_markets(markets)
        print(f"  Categories: {list(categories.keys())}")
        
        # Find arbitrage in each category
        all_opportunities = []
        for category, cat_markets in categories.items():
            if len(cat_markets) >= 2:
                opps = self.detector.find_arbitrage(category, cat_markets)
                all_opportunities.extend(opps)
        
        # Send alerts
        if all_opportunities:
            print(f"  Found {len(all_opportunities)} opportunities")
            for opp in all_opportunities[:5]:  # Top 5
                await self.send_alert(opp)
        else:
            print(f"  No arbitrage opportunities (min edge: {MIN_EDGE*100:.0f}%)")
    
    async def run(self):
        """Main loop"""
        print("="*60)
        print("💰 Polymarket Arbitrage Bot")
        print("="*60)
        print(f"Min edge: {MIN_EDGE*100:.0f}%")
        print(f"Min liquidity: ${MIN_LIQUIDITY:,}")
        print(f"Check interval: 5 minutes\n")
        
        while True:
            try:
                await self.scan()
            except Exception as e:
                print(f"[ERROR] {e}")
            
            await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    bot = PolymarketArbBot()
    asyncio.run(bot.run())
