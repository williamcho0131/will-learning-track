#!/usr/bin/env python3
"""
Example: Get exchange rates
Uses exchangerate-api.com (free tier available)
"""

import requests

def get_exchange_rates(base_currency='USD'):
    """
    Get exchange rates for a base currency
    Free API, no key required for basic usage
    """
    # This is a free API endpoint
    url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching rates: {e}")
        return None

def convert_currency(amount, from_currency, to_currency):
    """Convert amount between currencies"""
    rates = get_exchange_rates(from_currency)
    
    if not rates or to_currency not in rates.get('rates', {}):
        return None
    
    rate = rates['rates'][to_currency]
    converted = amount * rate
    
    return {
        'original': amount,
        'from': from_currency,
        'to': to_currency,
        'rate': rate,
        'converted': converted
    }

if __name__ == "__main__":
    print("💱 Exchange Rates")
    print("="*50)
    
    # Get USD rates
    rates = get_exchange_rates('USD')
    
    if rates:
        print(f"\nBase: {rates['base']}")
        print(f"Date: {rates['date']}\n")
        
        # Show major currencies
        major_currencies = ['EUR', 'GBP', 'JPY', 'CNY', 'CAD', 'AUD', 'CHF']
        print("Major Currency Rates:")
        for currency in major_currencies:
            if currency in rates['rates']:
                print(f"  1 USD = {rates['rates'][currency]:.4f} {currency}")
        
        # Example conversion
        print("\n" + "="*50)
        print("\nExample Conversions:")
        
        conversions = [
            (100, 'USD', 'EUR'),
            (1000, 'USD', 'JPY'),
            (50, 'GBP', 'USD')
        ]
        
        for amount, from_c, to_c in conversions:
            result = convert_currency(amount, from_c, to_c)
            if result:
                print(f"  {amount} {from_c} = {result['converted']:.2f} {to_c}")
