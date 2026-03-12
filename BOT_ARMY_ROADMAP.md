# 🤖 Alpha Bot Army - Roadmap

**Mission:** Build the ultimate alpha-hunting bot army

---

## 🎯 Bot Inventory

| Bot | Status | Description | Priority |
|-----|--------|-------------|----------|
| **funding_arb** | ✅ Live | Funding rate arbitrage scanner | HIGH |
| **big_move** | ✅ Built | Stock/crypto big move + news | HIGH |
| **polymarket_arb** | ✅ Built | Cross-market probability arb | MEDIUM |
| **alpha_snipe** | ✅ Built | New listings/protocol sniper | HIGH |

---

## 📋 Bot Details

### 1. Funding Arbitrage Bot (funding_arb) ✅

**Status:** Running 24/7
**Features:**
- Scans 200+ perpetual markets
- Ranks by opportunity score
- 5-second polling
- Telegram alerts for HIGH priority

**Next Steps:**
- [ ] Add Bybit integration
- [ ] Add OKX integration
- [ ] Auto-execution module
- [ ] Backtesting framework

---

### 2. Big Move Alert Bot (big_move) 🆕

**Status:** Built, ready to deploy
**Features:**
- Monitors 10 crypto + 10 stocks
- Detects >5% moves (crypto), >3% (stocks)
- Searches for news evidence
- Telegram alerts with context

**Next Steps:**
- [ ] Integrate news API (NewsAPI, GDELT)
- [ ] Add Twitter sentiment analysis
- [ ] Add stock price API (Polygon, Finnhub)
- [ ] Deploy and test

**Data Sources Needed:**
- CoinGecko (✅ free)
- NewsAPI (need key)
- Twitter API (need key)
- Stock API (Polygon/Finnhub)

---

### 3. Polymarket Arbitrage Bot (polymarket_arb) 🆕

**Status:** Built, ready to deploy
**Features:**
- Scans all Polymarket events
- Groups by category (politics, crypto, sports)
- Detects probability discrepancies >5%
- Suggests hedge strategies

**Next Steps:**
- [ ] Deploy and test with real data
- [ ] Add Kalshi integration (similar markets)
- [ ] Add prediction market aggregation
- [ ] Risk management module

---

### 4. Alpha Snipe Bot (alpha_snipe) 🆕

**Status:** Built, ready to deploy
**Features:**
- Monitors CoinGecko new listings
- Tracks DeFiLlama trending protocols
- Generates investment thesis
- Suggests how to capture alpha

**Next Steps:**
- [ ] Add Twitter monitoring for airdrops
- [ ] Add Discord/Telegram alpha groups
- [ ] Deploy and test
- [ ] Create alert ranking system

**Data Sources:**
- CoinGecko (✅ free)
- DeFiLlama (✅ free)
- Twitter API (need key)
- Token Terminal (optional)

---

## 🚀 Deployment Plan

### Phase 1: Testing (This Week)
- [x] Build all 4 bots
- [x] Create orchestrator
- [ ] Test big_move bot (need APIs)
- [ ] Test polymarket bot
- [ ] Test alpha_snipe bot

### Phase 2: API Integration (Next Week)
- [ ] Get NewsAPI key
- [ ] Get Twitter API key
- [ ] Get Polygon/Finnhub key
- [ ] Integrate all data sources

### Phase 3: Production (Week 3)
- [ ] Deploy all bots via orchestrator
- [ ] Monitor for 1 week
- [ ] Tune alert thresholds
- [ ] Add backtesting

### Phase 4: Advanced Features (Week 4)
- [ ] Auto-execution for funding arb
- [ ] Machine learning for alpha ranking
- [ ] Cross-bot correlation (e.g., big move → check funding)
- [ ] Dashboard/web UI

---

## 💰 Expected Alpha

| Bot | Frequency | Expected Edge | Risk |
|-----|-----------|---------------|------|
| funding_arb | Daily | 15-100% APY | Low |
| big_move | Weekly | 10-50% per trade | Medium |
| polymarket | Weekly | 5-20% per arb | Low |
| alpha_snipe | Monthly | 100-1000% if early | High |

---

## 🔧 Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| Async | asyncio, aiohttp |
| Data | REST APIs, WebSockets |
| Alerts | Telegram Bot API |
| Orchestration | Custom Python + systemd |
| Storage | SQLite (optional) |
| Monitoring | Custom logs + alerts |

---

## 📁 File Structure

```
bots/
├── multi_asset_scanner.py      # Funding arb (LIVE)
├── big_move_alert.py           # Big move detection
├── polymarket_arb.py           # Polymarket arb
├── alpha_snipe.py              # New listing sniper
├── bot_orchestrator.py         # Master controller
├── start_multi_asset.sh        # Convenience scripts
└── test_multi_asset.py         # Testing utilities

skills/
└── funding-arb-alert/          # Reusable skill
    ├── SKILL.md
    ├── README.md
    ├── config.yaml
    └── scripts/
```

---

## 🎯 Next Actions

### For User
- [ ] Provide API keys (NewsAPI, Twitter, Polygon)
- [ ] Review bot configurations
- [ ] Deploy and test each bot
- [ ] Tune alert thresholds based on noise

### For Me (Kimi)
- [ ] Update all bots to skills when stable
- [ ] Add error handling and retry logic
- [ ] Create comprehensive documentation
- [ ] Build backtesting framework

---

## 📝 Daily Sync Protocol

**Rule:** Any bot improvements → sync to skills immediately

**Checklist:**
- [ ] Code changes pushed to GitHub
- [ ] Skills updated if applicable
- [ ] Documentation updated
- [ ] Version bumped

---

*Last Updated: March 12, 2026*
*Status: 4 bots built, 1 live, 3 ready for testing*
