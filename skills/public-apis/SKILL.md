---
name: public-apis
description: Access and query the public-apis repository (https://github.com/public-apis/public-apis) to discover free APIs for data, finance, weather, crypto, news, and more. Use when you need to find public APIs, check API availability, get API documentation, or discover free data sources for projects without authentication requirements.
---

# Public APIs Skill

Access thousands of free public APIs organized by category.

## What This Skill Does

This skill helps you discover and use free public APIs for:
- Market data (stocks, crypto, forex)
- Weather and climate
- News and information
- Geolocation and maps
- Social media data
- Government data
- Science and math
- Entertainment

## Repository

**GitHub:** https://github.com/public-apis/public-apis

## Quick Start

### Browse APIs by Category

```bash
# Get APIs in a specific category
python3 scripts/query_apis.py --category finance

# Search for specific API types
python3 scripts/query_apis.py --search "stock price"

# Check if an API requires auth
python3 scripts/query_apis.py --auth none
```

### Popular Categories

| Category | Use Case | Example APIs |
|----------|----------|--------------|
| **Finance** | Stock prices, crypto, forex | Yahoo Finance, CoinGecko, Alpha Vantage |
| **Weather** | Current weather, forecasts | OpenWeatherMap, WeatherAPI |
| **News** | Headlines, articles | NewsAPI, GNews |
| **Geocoding** | Location data, maps | Nominatim, OpenCage |
| **Government** | Public data | data.gov, EU Open Data |
| **Crypto** | Prices, blockchain | CoinGecko, CryptoCompare |

## Top Free APIs (No Auth Required)

### Finance & Crypto

| API | Data | Auth | Rate Limit |
|-----|------|------|------------|
| CoinGecko | Crypto prices, market cap | No | 10-30 calls/min |
| Yahoo Finance | Stocks, forex | No | 2,000/hour |
| ExchangeRate-API | Currency conversion | No | 1,500/month |
| Financial Modeling Prep | Stocks, financials | Optional | 250/day free |

### Weather

| API | Data | Auth | Rate Limit |
|-----|------|------|------------|
| OpenWeatherMap | Weather, forecast | Yes (free tier) | 1,000/day |
| WeatherAPI | Weather, forecast | Yes (free tier) | 1M/month |

### News

| API | Data | Auth | Rate Limit |
|-----|------|------|------------|
| NewsAPI | Headlines, articles | Yes (free tier) | 100/day |
| GNews | News articles | Yes (free tier) | 100/day |

### Data & Knowledge

| API | Data | Auth | Rate Limit |
|-----|------|------|------------|
| REST Countries | Country info | No | Unlimited |
| Open Library | Books, authors | No | 100/min |
| NASA APIs | Space data, images | No | 1,000/hour |
| Random User | Fake user data | No | Unlimited |

## Usage Examples

### Get Crypto Prices

```python
import requests

# CoinGecko - Free, no API key
url = "https://api.coingecko.com/api/v3/simple/price"
params = {
    "ids": "bitcoin,ethereum",
    "vs_currencies": "usd"
}
response = requests.get(url, params=params)
data = response.json()

print(f"BTC: ${data['bitcoin']['usd']}")
print(f"ETH: ${data['ethereum']['usd']}")
```

### Get Stock Data

```python
import requests

# Yahoo Finance (unofficial)
url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL"
response = requests.get(url)
data = response.json()

price = data['chart']['result'][0]['meta']['regularMarketPrice']
print(f"AAPL: ${price}")
```

### Get Weather

```python
import requests

# OpenWeatherMap (requires free API key)
api_key = "your_api_key"
url = f"http://api.openweathermap.org/data/2.5/weather"
params = {
    "q": "London",
    "appid": api_key,
    "units": "metric"
}
response = requests.get(url, params=params)
data = response.json()

print(f"Temperature: {data['main']['temp']}°C")
print(f"Weather: {data['weather'][0]['description']}")
```

## Rate Limiting Best Practices

1. **Cache responses** - Don't hammer APIs
2. **Respect limits** - Check documentation
3. **Handle errors** - 429 = rate limited
4. **Use backoff** - Exponential retry

## API Status Check

```bash
# Check if an API is online
python3 scripts/check_api.py --url "https://api.coingecko.com/api/v3/ping"
```

## Common Issues

### 429 Too Many Requests
- You're hitting rate limits
- Solution: Add delays, cache data

### 403 Forbidden
- API requires authentication
- Solution: Get free API key

### 404 Not Found
- Endpoint changed or deprecated
- Solution: Check documentation

## Resources

- **Full API List:** https://github.com/public-apis/public-apis/blob/master/README.md
- **API Status:** https://github.com/public-apis/public-apis#status
- **Categories:** https://github.com/public-apis/public-apis#index

## Scripts Included

| Script | Purpose |
|--------|---------|
| `query_apis.py` | Search and filter APIs |
| `check_api.py` | Test API availability |
| `examples/` | Working code examples |

---

**Note:** APIs change frequently. Always check the official repository for latest status and documentation.
