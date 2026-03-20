#!/usr/bin/env python3
"""
Example: Get cryptocurrency prices using CoinGecko API
Free, no API key required, rate limit: 10-30 calls/minute
"""

import requests
import json

def get_crypto_prices(coins=['bitcoin', 'ethereum'], currency='usd'):
    """
    Get current cryptocurrency prices
    
    Args:
        coins: List of coin IDs (e.g., ['bitcoin', 'ethereum', 'solana'])
        currency: Target currency (usd, eur, gbp, etc.)
    
    Returns:
        Dict with coin prices
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    
    params = {
        "ids": ",".join(coins),
        "vs_currencies": currency,
        "include_24hr_change": "true",
        "include_market_cap": "true"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching prices: {e}")
        return None

def display_prices(data, currency='usd'):
    """Display prices nicely"""
    if not data:
        return
    
    print(f"\n💰 Cryptocurrency Prices ({currency.upper()})")
    print("="*50)
    
    for coin, info in data.items():
        price = info.get(currency, 0)
        change = info.get(f'{currency}_24h_change', 0)
        market_cap = info.get(f'{currency}_market_cap', 0)
        
        # Format price
        if price >= 1000:
            price_str = f"${price:,.2f}"
        else:
            price_str = f"${price:.4f}"
        
        # Format change with color indicator
        change_str = f"{change:+.2f}%"
        
        print(f"\n{coin.upper()}:")
        print(f"  Price: {price_str}")
        print(f"  24h Change: {change_str}")
        print(f"  Market Cap: ${market_cap/1e9:.1f}B")
    
    print("="*50)

if __name__ == "__main__":
    # Example: Get Bitcoin, Ethereum, and Solana prices
    coins = ['bitcoin', 'ethereum', 'solana', 'cardano']
    
    print("🔄 Fetching prices from CoinGecko...")
    data = get_crypto_prices(coins)
    
    if data:
        display_prices(data)
        
        # Example: Calculate portfolio value
        portfolio = {
            'bitcoin': 0.5,
            'ethereum': 4.0,
            'solana': 50.0
        }
        
        print(f"\n📊 Portfolio Value:")
        total = 0
        for coin, amount in portfolio.items():
            if coin in data:
                value = data[coin]['usd'] * amount
                total += value
                print(f"  {amount} {coin}: ${value:,.2f}")
        
        print(f"\n  Total Value: ${total:,.2f}")
    else:
        print("❌ Failed to fetch prices")
