#!/usr/bin/env python3
"""
Example: Get stock data using Yahoo Finance (unofficial)
Free, no API key required
"""

import requests
import json

def get_stock_quote(symbol):
    """
    Get stock quote from Yahoo Finance
    
    Args:
        symbol: Stock ticker (e.g., 'AAPL', 'TSLA', 'MSFT')
    
    Returns:
        Dict with stock data
    """
    # Yahoo Finance chart API endpoint
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    
    params = {
        "interval": "1d",
        "range": "1d"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Public-APIs-Example/1.0)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        result = data['chart']['result'][0]
        meta = result['meta']
        
        return {
            'symbol': symbol.upper(),
            'price': meta.get('regularMarketPrice', 0),
            'previous_close': meta.get('previousClose', 0),
            'currency': meta.get('currency', 'USD'),
            'exchange': meta.get('exchangeName', 'Unknown')
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def get_multiple_quotes(symbols):
    """Get quotes for multiple stocks"""
    results = {}
    for symbol in symbols:
        data = get_stock_quote(symbol)
        if data:
            results[symbol] = data
    return results

if __name__ == "__main__":
    # Example: Get quotes for popular stocks
    symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
    
    print("📈 Stock Quotes (Yahoo Finance)")
    print("="*60)
    
    for symbol in symbols:
        data = get_stock_quote(symbol)
        if data:
            change = data['price'] - data['previous_close']
            change_pct = (change / data['previous_close']) * 100 if data['previous_close'] else 0
            
            print(f"\n{data['symbol']} ({data['exchange']}):")
            print(f"  Price: ${data['price']:.2f} {data['currency']}")
            print(f"  Change: ${change:+.2f} ({change_pct:+.2f}%)")
    
    print("="*60)
