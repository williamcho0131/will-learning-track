#!/usr/bin/env python3
"""
Live Forex & Economic Data Feed
Uses free public APIs for macro dashboard
"""

import asyncio
import aiohttp
from datetime import datetime

async def get_exchange_rates():
    """Get live exchange rates from exchangerate-api.com (free)"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
        
        major_pairs = {
            'EUR': data['rates'].get('EUR', 0),
            'GBP': data['rates'].get('GBP', 0),
            'JPY': data['rates'].get('JPY', 0),
            'CNY': data['rates'].get('CNY', 0),
            'CAD': data['rates'].get('CAD', 0),
            'AUD': data['rates'].get('AUD', 0),
            'CHF': data['rates'].get('CHF', 0),
        }
        
        return major_pairs
    except Exception as e:
        print(f"Error fetching forex: {e}")
        return {}

async def get_crypto_global():
    """Get global crypto market data from CoinGecko"""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
        
        return {
            'total_market_cap': data['data']['total_market_cap']['usd'],
            'total_volume': data['data']['total_volume']['usd'],
            'btc_dominance': data['data']['market_cap_percentage']['btc'],
            'eth_dominance': data['data']['market_cap_percentage']['eth'],
        }
    except Exception as e:
        print(f"Error fetching crypto global: {e}")
        return {}

async def get_fear_greed():
    """Get Fear & Greed index (alternative: use CoinGecko data)"""
    # Note: Alternative.me API sometimes blocks, using CoinGecko fear/greed via their API if available
    # For now, return None - can be enhanced
    return None

def format_macro_summary(forex, crypto):
    """Format nice summary"""
    output = []
    output.append("="*60)
    output.append("📊 LIVE MACRO DATA SNAPSHOT")
    output.append("="*60)
    
    if forex:
        output.append("\n💱 Forex Rates (USD base):")
        for currency, rate in forex.items():
            output.append(f"  1 USD = {rate:.4f} {currency}")
    
    if crypto:
        output.append("\n₿ Crypto Global:")
        output.append(f"  Total Market Cap: ${crypto['total_market_cap']/1e12:.2f}T")
        output.append(f"  24h Volume: ${crypto['total_volume']/1e9:.1f}B")
        output.append(f"  BTC Dominance: {crypto['btc_dominance']:.1f}%")
        output.append(f"  ETH Dominance: {crypto['eth_dominance']:.1f}%")
    
    output.append("\n" + "="*60)
    return "\n".join(output)

async def main():
    """Fetch and display live macro data"""
    print("Fetching live macro data from free APIs...\n")
    
    # Fetch in parallel
    forex_task = get_exchange_rates()
    crypto_task = get_crypto_global()
    
    forex, crypto = await asyncio.gather(forex_task, crypto_task)
    
    # Display
    summary = format_macro_summary(forex, crypto)
    print(summary)
    
    # Save to file for dashboard
    data = {
        'timestamp': datetime.now().isoformat(),
        'forex': forex,
        'crypto_global': crypto
    }
    
    with open('/opt/will-learning-track/data/live_macro.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Data saved to data/live_macro.json")

if __name__ == "__main__":
    import json
    asyncio.run(main())
