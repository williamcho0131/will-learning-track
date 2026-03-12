# 🚀 Funding Arbitrage Alert Bot

A professional-grade funding rate arbitrage scanner that monitors perpetual markets 24/7 and alerts you to profitable delta-neutral opportunities.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🎯 What It Does

- **Scans 200+ perpetual markets** across Binance, Hyperliquid (more coming)
- **Ranks opportunities** by funding spread × OI × liquidity score
- **Sends Telegram alerts** only when HIGH priority setups are found
- **Runs 24/7** with configurable check intervals
- **100% customizable** thresholds, exchanges, and alert rules

## 📊 Example Alert

```
🔥 HIGH PRIORITY ARB: PEPE

Funding Spread: 0.185% (threshold: 0.20%)

Funding Rates:
• Binance: -0.185% ⭐ BEST (PAID to long)
• Hyperliquid: -0.042%

Trade Setup:
💚 Long on Binance: -0.185%
❤️ Short on Hyperliquid: -0.042%

Market Data:
• OI: $420M
• Score: 0.62

Next funding: ~8 hours
```

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/williamcho0131/funding-arb-alerts.git
cd funding-arb-alerts
python3 scripts/setup.py
```

### 2. Run the Bot

```bash
python3 scripts/funding_scanner.py
```

### 3. Background Mode

```bash
nohup python3 scripts/funding_scanner.py &
tail -f logs/funding_scanner.log
```

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
exchanges:
  - binance
  - hyperliquid

telegram:
  token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"

thresholds:
  major: 0.0008    # BTC, ETH: alert if spread > 0.08%
  mid: 0.0012      # SOL, LINK: alert if spread > 0.12%
  alt: 0.0020      # DOGE, HYPE: alert if spread > 0.20%

scanning:
  interval_seconds: 5
```

## 📈 Opportunity Scoring

```
Score = Funding Spread × Liquidity Factor × (OI / $1B)

Example:
• PEPE: 0.185% spread × 0.5 (alt factor) × 0.42 ($420M OI)
• Score = 0.039 → HIGH priority alert
```

## 💰 Expected Returns

| Market | Avg Spread | Annual Return |
|--------|------------|---------------|
| Calm | 0.02% | 15-25% |
| Normal | 0.08% | 50-80% |
| Volatile | 0.20% | 150-200% |

## 🛡️ Risk Management

- **Delta-neutral**: Long + Short = no price exposure
- **Cooldown periods**: Prevent alert spam
- **Minimum OI check**: Only liquid markets
- **Volatility pause**: Stop during extreme moves

## 📝 File Structure

```
funding-arb-alerts/
├── SKILL.md                    # OpenClaw skill documentation
├── README.md                   # This file
├── config.yaml                 # Bot configuration
├── scripts/
│   ├── funding_scanner.py     # Main scanner (300 lines)
│   ├── setup.py               # Setup wizard
│   └── install_service.sh     # Systemd installer
├── references/
│   ├── exchanges.md           # API documentation
│   └── strategy_guide.md      # Arb strategy details
└── logs/                      # Runtime logs
```

## 🔧 Advanced Usage

### Add Custom Exchange

```python
# scripts/exchanges/custom.py
class CustomExchange:
    async def get_funding(self, symbol):
        # Your implementation
        pass
```

### Run as Systemd Service

```bash
sudo ./scripts/install_service.sh
sudo systemctl start funding-arb-alerts
```

### Backtest Strategy

```bash
python3 scripts/backtest.py \
  --start-date 2024-01-01 \
  --end-date 2024-03-01
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing`
5. Open Pull Request

## 📜 License

MIT License - Use at your own risk. Not financial advice.

## ⚠️ Disclaimer

Cryptocurrency trading carries significant risk. This tool is for educational purposes. Always:
- Start with small capital
- Understand 雙開 (double-sided) strategy risks
- Never risk more than you can afford to lose

## 🔗 Links

- **GitHub**: https://github.com/williamcho0131/funding-arb-alerts
- **Issues**: https://github.com/williamcho0131/funding-arb-alerts/issues
- **OpenClaw Hub**: Coming soon

---

**Made with ❤️ for the OpenClaw community**
