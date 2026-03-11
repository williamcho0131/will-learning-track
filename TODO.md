# 🚨 Alert Bot Iteration Roadmap

**Status:** Active Development  
**Started:** March 12, 2026  
**Goal:** Build the most comprehensive funding/spread arbitrage monitoring bot

---

## Current Status

✅ **Live Features:**
- Binance + Hyperliquid price monitoring
- Funding rate alerts (±0.1% threshold)
- OI tracking with notional value ($1.85B format)
- OI spike alerts (>±10% change)
- Price level alerts ($65K/$75K)
- Telegram notifications

---

## Phase 1: Opportunity-First Alert System (Week 1)

Priority: HIGH — Only alert when there's actual alpha

### Alert Philosophy
**OLD:** Monitor fixed assets (BTC, ETH, SOL...)  
**NEW:** Scan ALL markets, rank by opportunity size, only alert top 3

### Opportunity Score Formula
```
Score = |Funding Spread| × OI × Liquidity Factor

Where:
- Funding Spread = Max(funding) - Min(funding) across exchanges
- OI = Total Open Interest (notional)
- Liquidity Factor = 1 for majors, 0.7 for mid-caps, 0.4 for alts

Threshold: Only alert if Score > 0.05 (significant edge)
```

### Alert Tiers

| Tier | Trigger | Action |
|------|---------|--------|
| **🔥 HIGH** | Funding spread >0.15% + OI >$100M | Immediate Telegram alert |
| **⚠️ MEDIUM** | Funding spread 0.08-0.15% | Batch in hourly digest |
| **📊 LOW** | Funding spread <0.08% | Log only, no alert |

### What Gets Scanned
- **ALL perpetual markets** on Binance, Hyperliquid, Bybit, OKX
- **Not just majors** — any coin with funding divergence
- **Dynamic ranking** — opportunities change, alerts follow

### Special BTC Alerts (Always On)
- Support break <$65K
- Resistance break >$75K
- >5% move in 1h
- OI spike >20% (potential squeeze)

**Deliverable:** Only actionable alerts, zero noise

---

## Phase 2: Signal Enhancement (Week 2)

Priority: HIGH — Better signals = better trades

### New Signals to Add:
- [ ] **Funding Spread Matrix** — Compare all exchanges side-by-side
- [ ] **OI Delta** — Rate of change, not just absolute
- [ ] **Liquidation Clusters** — Where will liquidations cascade?
- [ ] **Funding Momentum** — Is funding accelerating or decelerating?
- [ ] **Spot-Perp Basis** — Annualized % difference
- [ ] **Long/Short Ratio** — Retail positioning

**Deliverable:** "This is the best arb right now" ranked list

---

## Phase 3: Advanced Signals (Week 3)

Priority: MEDIUM — Pro-level data

### Institutional Signals:
- [ ] **CVD (Cumulative Volume Delta)** — Smart money flow
- [ ] **Order Book Imbalance** — Bid/ask pressure
- [ ] **Options Flow** — Deribit whale positioning
- [ ] **Correlation Monitor** — BTC vs ETH vs SPY divergence
- [ ] **Volatility Regime** — HV vs IV for options

**Deliverable:** Professional-grade signals (like CoinGlass Pro)

---

## Phase 4: Execution Integration (Week 4)

Priority: LOW — Optional automation

### Execution Features:
- [ ] **Auto-hedge Calculator** — "Long X on Binance, Short Y on Hyperliquid"
- [ ] **Position Sizing** — Based on margin requirements
- [ ] **PnL Tracking** — Log executed arbs
- [ ] **Daily Report** — What you made/lost
- [ ] **Paper Trading Mode** — Test without risk

**Deliverable:** Full trading decision support

---

## Daily Iteration Checklist

Each day I should:
- [ ] Review yesterday's alerts — were they useful?
- [ ] Add ONE new exchange or signal
- [ ] Update this TODO with progress
- [ ] Push changes to GitHub
- [ ] Document new features in learning log

---

## Data Sources to Integrate

| Source | Data | Cost | Priority |
|--------|------|------|----------|
| Binance API | Funding, OI, Price | Free | ✅ Done |
| Hyperliquid API | Funding, OI, Price | Free | ✅ Done |
| Bybit API | Funding, OI, Price | Free | 🔥 Next |
| OKX API | Funding, OI, Price | Free | 🔄 Todo |
| CoinGlass API | Liquidations, L/S | Paid | 🔄 Todo |
| Velo Data | Flow, Whales | Paid | 🔄 Todo |
| The Block | News, Events | Free | 🔄 Todo |

---

## Signal Quality Metrics

How do we know if the bot is good?

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Alert Accuracy | >70% | Signals that moved within 1h |
| False Positive Rate | <30% | Alerts with no follow-through |
| Arb Opportunity Capture | >80% | Did we catch the best opportunities? |
| Latency | <60s | Time from event to Telegram |

---

## User Feedback Log

| Date | Feedback | Action |
|------|----------|--------|
| 2026-03-11 | "No OI data" | Fixed: Added proper OI notional display |
| | "Add more exchanges" | In Progress: Bybit, OKX integration |
| | | |

---

*This is a living document. Updated daily as we iterate.*

---

## NEW: Opportunity-First Alert Logic (Priority Update)

### Philosophy Change
**FROM:** Monitor fixed list of coins  
**TO:** Scan all markets, rank by opportunity size, alert only actionable setups

### Opportunity Score Algorithm

```python
# Score = Potential daily profit adjusted for risk
opportunity_score = funding_spread * oi_notional * liquidity_factor

# Thresholds for alerting:
# - HIGH: score > 0.10 (immediate alert)
# - MEDIUM: score 0.05-0.10 (hourly digest)
# - LOW: score < 0.05 (logged only)

# Where:
# funding_spread = max(funding) - min(funding) across exchanges
# oi_notional = open_interest * mark_price
# liquidity_factor = 1.0 (BTC/ETH), 0.7 (SOL/LINK), 0.5 (alts), 0.3 (exotics)
```

### Dynamic Market Coverage

| Market Cap | Min Spread to Alert | Examples |
|------------|---------------------|----------|
| Majors (>$10B) | 0.08% | BTC, ETH |
| Mid-caps ($1-10B) | 0.12% | SOL, LINK, ARB |
| Small-caps ($100M-1B) | 0.20% | DOGE, HYPE |
| Micro-caps (<$100M) | 0.30% | New listings, memes |

### Alert Format (Updated)

```
🔥 HIGH PRIORITY ARB OPPORTUNITY

PEPE-PERP
═══════════════════════════════════
Funding Rates:
  • Binance:  -0.185% ⭐ BEST (PAID to long)
  • Bybit:    -0.042%
  • Hyperliq: -0.089%
  
Spread: 0.143% | OI: $420M | Score: 0.60

💡 Trade: Long Binance (earn 0.185% / 8h)
   Hedge: Short on Hyperliquid or spot
   
⚠️ Risk: Meme coin, high volatility
   Required: $X margin for $Y position

⏰ Next funding: 2h 14m
```

### BTC Always-On Alerts

Regardless of opportunity score, always alert on:
- Price breaks ($65K / $75K)
- >5% move in 1h
- OI spike >20%
- Funding extreme (>±0.2%)

### Implementation Priority

1. **Day 2:** Bybit API + Opportunity ranking logic
2. **Day 3:** Multi-coin scanning (not just BTC)
3. **Day 4:** Score-based alerting (only HIGH priority)
4. **Day 5:** Backtest: Did yesterday's alerts work?

