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

## Phase 1: Exchange Expansion (Week 1)

Priority: HIGH — More exchanges = more arb opportunities

| Exchange | Funding | OI | Spot | Status |
|----------|---------|-----|------|--------|
| Binance | ✅ | ✅ | ✅ | Live |
| Hyperliquid | ✅ | ✅ | ❌ | Live |
| Bybit | 🔄 | 🔄 | 🔄 | Todo |
| OKX | 🔄 | 🔄 | 🔄 | Todo |
| dYdX | 🔄 | 🔄 | ❌ | Todo |
| Aevo | 🔄 | 🔄 | ❌ | Todo |
| Deribit | 🔄 | 🔄 | ❌ | Todo (options) |

**Deliverable:** Cross-exchange funding spread alerts

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
