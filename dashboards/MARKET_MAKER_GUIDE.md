# 📊 Market Maker Simulator - Complete Guide

**Learn market making by running an interactive simulation.**

---

## 🎯 What This Simulator Teaches

### Core Concepts
1. **Spread Capture** - How market makers earn the bid-ask spread
2. **Inventory Management** - Balancing long/short exposure
3. **Adverse Selection** - Getting picked off by informed traders
4. **Market Regimes** - Different strategies for calm/volatile/trending markets
5. **Risk Management** - When to hedge, when to hold

---

## 🚀 Quick Start

### View the Dashboard
```bash
# Open in browser
open /opt/will-learning-track/dashboards/market_maker_simulator.html

# Or serve via HTTP
python3 -m http.server 8080 --directory /opt/will-learning-track/dashboards/
# Then visit: http://localhost:8080/market_maker_simulator.html
```

---

## 📖 Tutorial Walkthrough

### Part 1: Understanding the Interface

#### 1. Order Book Panel (Left)
Shows the market's limit orders:
- **Red (Asks)** - People selling, prices go UP
- **Green (Bids)** - People buying, prices go DOWN
- **Mid Price** - Fair value between bid and ask
- **Market Spread** - Difference between best bid and ask

#### 2. Your Quote Panel (Center)
Where you set your market maker quotes:
- **Bid Price** - What you'll pay to buy
- **Bid Size** - How much you'll buy
- **Ask Price** - What you'll sell for
- **Ask Size** - How much you'll sell
- **Your Spread** - Your profit margin

#### 3. Market Regime Panel (Top Right)
Three market conditions:
- **🟢 Calm** - Low volatility, tight spreads, balanced flow
- **🔴 Volatile** - High volatility, wide spreads, risk of large moves
- **🟠 Trending** - One-sided flow, adverse selection risk

#### 4. PnL Panel (Middle Right)
Your performance metrics:
- **Realized PnL** - Closed trades profit/loss
- **Unrealized PnL** - Open position mark-to-market
- **Spread Captured** - Total spread income
- **Adverse Selection** - Losses to informed traders

#### 5. Inventory Panel (Bottom Right)
Your position tracking:
- **Long Inventory** - You've bought more than sold
- **Short Inventory** - You've sold more than bought
- **Neutral** - Balanced (target state)

---

## 🎮 How to Play

### Scenario 1: Basic Market Making

**Starting State:**
- Mid Price: $100
- Your Inventory: 0
- Your Goal: Capture spread while keeping inventory near 0

**Steps:**
1. Set Bid at $99.96 (0.04% below mid)
2. Set Ask at $100.04 (0.04% above mid)
3. Your spread: 0.08%
4. Wait for trades

**What Happens:**
- If someone hits your bid → You buy, go LONG
- If someone lifts your ask → You sell, go SHORT
- If both happen → You earn $0.08 per unit, inventory stays 0 ✅

---

### Scenario 2: Inventory Management

**Starting State:**
- You've bought 200 units (LONG inventory)
- Price starts dropping
- Your unrealized PnL is negative

**Your Options:**

**Option A: Hold and Quote Skew**
- Lower your bid (buy less aggressively)
- Lower your ask (sell more aggressively)
- Goal: Sell inventory, get back to neutral

**Option B: Hedge (Panic Button)**
- Click "Hedge Inventory"
- Market sells your 200 units
- Pay slippage, but flatten position

**Option C: Do Nothing**
- Keep quoting symmetrically
- Hope price comes back
- Risk: Inventory grows larger if price keeps dropping

**Lesson:** Inventory is risk. Manage it actively.

---

### Scenario 3: Calm Market (🟢)

**Characteristics:**
- Volatility: Low
- Flow: Balanced
- Spread Target: 0.04% - 0.12%

**Strategy:**
- Quote tight spreads
- Capture small profits consistently
- Keep inventory near zero
- High frequency, low margin

**In Simulator:**
```
Bid: $99.97
Ask: $100.03
Spread: 0.06%
Size: 100 units each side
```

**Expected:** 10-20 trades per minute, small but steady profits.

---

### Scenario 4: Volatile Market (🔴)

**Characteristics:**
- Volatility: High
- Price jumps: Large and sudden
- Spread Target: 0.15% - 0.40%

**Strategy:**
- Widen your spreads
- Reduce position sizes
- Hedge quickly if inventory builds
- Lower frequency, higher margin

**In Simulator:**
```
Bid: $99.85
Ask: $100.25
Spread: 0.40%
Size: 50 units each side
```

**Risk:** Price can gap through your quotes. You buy at $99.85, price drops to $99.00 instantly. **-0.85% loss.**

---

### Scenario 5: Trending Market (🟠)

**Characteristics:**
- Directional flow (everyone buying or selling)
- Adverse selection high
- Smart money knows something you don't

**Strategy:**
- **SKEW YOUR QUOTES**
- If trend is UP: Raise both bid and ask
- If trend is DOWN: Lower both bid and ask
- Don't fight the trend

**In Simulator (Trending UP):**
```
Bid: $100.10 (above mid!)
Ask: $100.25
```

**Why:** You think price is going up, so you're willing to pay more to buy. You don't want to sell too cheap.

**Risk:** If trend reverses, you're caught wrong-footed with bad inventory.

---

## 💡 Key Lessons

### Lesson 1: Spread is Your Income

```
Buy at  $99.96
Sell at $100.04
Profit: $0.08 (0.08%)

Do this 100 times per day:
$0.08 × 100 = $8 per day per unit
$8 × 365 = $2,920 annual per unit
With $100K position: $292K/year
```

**BUT:** This assumes:
- Perfect inventory management
- No adverse selection
- Calm markets
- No operational costs

**Reality:** Market makers earn 10-30% of theoretical spread after costs.

---

### Lesson 2: Inventory is Risk

**Good Market Maker:**
- Inventory oscillates around 0
- Quickly flattens large positions
- Accepts small losses to avoid large ones

**Bad Market Maker:**
- Lets inventory build to ±500 units
- Hopes price reverses
- Gets run over by trending markets

**Rule:** "Your inventory is your enemy. The spread is your friend."

---

### Lesson 3: Adverse Selection Kills

**What is it?**
Informed traders know something you don't. They:
- Buy from you before good news
- Sell to you before bad news
- You think you captured spread, but you got toxic flow

**In Simulator:**
- Trending market regime
- You quote $99.96 / $100.04
- Informed trader knows price is going to $101
- They buy everything at $100.04
- Price jumps to $101
- You're short at $100.04, mark-to-market shows -$0.96 loss
- Your "spread capture" was actually adverse selection

**Protection:**
- Widen spreads in uncertain times
- Skew quotes when you detect one-sided flow
- Hedge large inventory quickly

---

### Lesson 4: Market Regimes Require Different Strategies

| Regime | Spread | Inventory | Skew | Frequency |
|--------|--------|-----------|------|-----------|
| Calm | Tight | Small | None | High |
| Volatile | Wide | Very Small | Slight | Medium |
| Trending | Medium | Tiny | Heavy | Low |

---

## 📊 Advanced Scenarios

### Scenario 6: The Hedge

**Situation:**
- You're LONG 300 units
- Price is dropping
- Unrealized loss: -$150

**Action:**
Click "Hedge Inventory"

**Result:**
- Market sells 300 units at $99.70 (slippage!)
- You lock in -$90 loss + slippage
- Position is now 0
- You can restart quoting

**Lesson:** Sometimes it's better to take a small loss than let it become a large one.

---

### Scenario 7: Auto-Quote Mode

**Enable:** Check "Auto-Quote (AI Market Maker Mode)"

**What it does:**
- Automatically adjusts quotes based on:
  - Current market regime
  - Your inventory level
  - Mid price movements

**Strategy Logic:**
```python
if inventory > 100:
    lower_bid()  # Buy less aggressively
    lower_ask()  # Sell more aggressively
if regime == 'trending_up':
    raise_both_quotes()
if regime == 'volatile':
    widen_spread()
```

**Use this to:**
- See how an algorithmic market maker behaves
- Learn quote adjustment patterns
- Compare your manual quoting vs AI

---

## 🎯 Success Metrics

### After 10 Minutes of Simulation, Check:

**Good Market Maker:**
- ✅ Realized PnL > $50
- ✅ Inventory stays between -100 and +100
- ✅ Spread captured > adverse selection
- ✅ 15+ trades executed

**Bad Market Maker:**
- ❌ Large negative PnL
- ❌ Inventory > 300 or < -300
- ❌ Adverse selection > spread captured
- ❌ Very few trades (spreads too wide)

---

## 🛠️ Real-World Application

### How This Applies to Your Funding Arb Bot

Your funding arb bot IS a market maker:
- **Long perp** on exchange with negative funding
- **Short perp** on exchange with positive funding
- **Spread** = funding differential
- **Inventory risk** = price moves against your hedge

**Skills you learned:**
1. Quote placement → Which exchange to long/short
2. Inventory management → When to close arb
3. Adverse selection → Funding rate flips against you
4. Market regimes → Volatility affects hedge ratio

---

## 📚 Further Reading

### Books
- "Market Microstructure Theory" by Maureen O'Hara
- "Trading and Exchanges" by Larry Harris
- "Algorithmic Trading" by Ernest Chan

### Papers
- "High Frequency Trading" by Aldridge
- "Market Making in the Age of Prop Trading"

### Videos
- Search: "KCG market making", "Jane Street market making"

---

## 🎓 Exercises

### Exercise 1: Calm Market Profit Target
**Goal:** Make $100 in realized PnL in calm market
**Constraint:** Inventory must stay between -50 and +50
**Time:** 5 minutes

### Exercise 2: Survive Volatility
**Goal:** Don't lose more than $50 in volatile market
**Strategy:** Widen spreads, reduce size, hedge quickly
**Time:** 5 minutes

### Exercise 3: Master the Trend
**Goal:** End with positive PnL in trending market
**Strategy:** Skew quotes in direction of trend
**Time:** 5 minutes

### Exercise 4: All-Weather MM
**Goal:** Positive PnL across all three regimes
**Switch regimes every 2 minutes**
**Total time:** 6 minutes

---

## 🔧 Technical Details

### Simulation Parameters

**Calm Market:**
- Volatility: 2% per tick
- Trade frequency: 30%
- Adverse selection: 10%

**Volatile Market:**
- Volatility: 8% per tick
- Trade frequency: 30%
- Adverse selection: 40%

**Trending Market:**
- Volatility: 5% per tick
- Trade frequency: 30%
- Adverse selection: 60%
- Flow bias: 80% one direction

### Code Location
```
/opt/will-learning-track/dashboards/market_maker_simulator.html
```

Pure HTML/JavaScript - no backend required. Can run locally in any browser.

---

## 📝 Notes for Improvement

### Future Enhancements:
1. Add real historical data replay
2. Multiple assets simultaneously
3. Competing market makers (multiplayer)
4. Machine learning MM bot to compete against
5. Backtesting framework
6. Risk metrics (Sharpe, max drawdown)

---

**Start the simulation and become a market maker!** 🚀
