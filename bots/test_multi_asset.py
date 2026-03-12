#!/usr/bin/env python3
"""Quick test of multi-asset scanner"""
import asyncio
import aiohttp

async def test():
    print("🚀 Testing Multi-Asset Scanner")
    print("="*50)
    
    # Test Binance
    print("\n1. Fetching Binance perpetuals...")
    async with aiohttp.ClientSession() as session:
        async with session.get('https://fapi.binance.com/fapi/v1/premiumIndex') as resp:
            binance_data = await resp.json()
            print(f"   ✅ Found {len(binance_data)} markets")
            
    # Test Hyperliquid
    print("\n2. Fetching Hyperliquid perpetuals...")
    async with aiohttp.ClientSession() as session:
        async with session.post('https://api.hyperliquid.xyz/info', 
            json={'type': 'metaAndAssetCtxs'}) as resp:
            hl_data = await resp.json()
            print(f"   ✅ Found {len(hl_data[0]['universe'])} markets")
            
    # Find common
    binance_symbols = {d['symbol'].replace('USDT', '') for d in binance_data if 'USDT' in d['symbol']}
    hl_symbols = {a['name'] for a in hl_data[0]['universe']}
    common = binance_symbols & hl_symbols
    
    print(f"\n3. Common markets: {len(common)}")
    print(f"   Examples: {', '.join(sorted(common)[:10])}")
    
    # Calculate sample opportunities
    print("\n4. Checking funding spreads...")
    opportunities = []
    for symbol in sorted(common)[:20]:  # Check first 20
        # Get Binance funding
        binance_item = next((d for d in binance_data if d['symbol'] == symbol + 'USDT'), None)
        # Get HL funding
        hl_idx = next((i for i, a in enumerate(hl_data[0]['universe']) if a['name'] == symbol), None)
        
        if binance_item and hl_idx is not None:
            binance_funding = float(binance_item.get('lastFundingRate', 0))
            hl_funding = float(hl_data[1][hl_idx]['funding'])
            spread = abs(binance_funding - hl_funding)
            
            if spread > 0.0005:  # 0.05%
                opportunities.append((symbol, spread * 100))
    
    if opportunities:
        opportunities.sort(key=lambda x: x[1], reverse=True)
        print(f"\n🔥 Found {len(opportunities)} opportunities:")
        for sym, spread in opportunities[:5]:
            print(f"   {sym}: {spread:.4f}% spread")
    else:
        print("\n📊 No significant spreads found (market is calm)")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test())
