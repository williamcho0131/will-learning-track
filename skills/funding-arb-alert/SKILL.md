---
name: funding-arb-alerts
description: Deploy a funding rate arbitrage alert bot that scans perpetual markets across exchanges, ranks opportunities by score, and sends Telegram alerts when high-priority setups are found. Use when you want to monitor funding rate differentials for delta-neutral arbitrage opportunities across Binance, Hyperliquid, Bybit, and other exchanges.
---

# Funding Arbitrage Alert Bot Skill

Deploy a professional-grade funding rate arbitrage scanner that monitors perpetual markets 24/7 and alerts you to profitable opportunities.

## Quick Start

### 1. Configure Environment
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
export TELEGRAM_CHAT_ID='your_chat_id'
```

### 2. Install Dependencies
```bash
pip install aiohttp python-telegram-bot
```

### 3. Run the Scanner
```bash
python3 scripts/funding_scanner.py
```

## What It Does

- **Scans ALL perpetual markets** across multiple exchanges
- **Calculates opportunity scores** based on funding spread × OI × liquidity
- **Ranks opportunities** from highest to lowest score
- **Sends Telegram alerts** only when score exceeds threshold
- **Runs 24/7** with configurable check intervals

## Supported Exchanges

| Exchange | Status | Data Provided |
|----------|--------|---------------|
| Binance | ✅ Live | 600+ perp markets |
| Hyperliquid | ✅ Live | 200+ perp markets |
| Bybit | 🔄 Coming | Perps + OI |
| OKX | 🔄 Coming | Perps + Funding |
| dYdX | 🔄 Coming | DEX perps |

## Opportunity Scoring

```
Score = Funding Spread × Liquidity Factor × (OI / $1B)

Where:
- Funding Spread = |Exchange A - Exchange B|
- Liquidity Factor: Major=1.0, Mid=0.7, Alt=0.5, Exotic=0.3
- OI = Total Open Interest (notional)
```

### Alert Thresholds

| Asset Class | Min Spread | Examples |
|-------------|------------|----------|
| Major | 0.08% | BTC, ETH |
| Mid-cap | 0.12% | SOL, LINK, ARB |
| Alts | 0.20% | DOGE, HYPE |
| Exotic | 0.30% | Memes, new listings |

## Configuration

Edit `config.yaml` to customize:

```yaml
exchanges:
  - binance
  - hyperliquid
  # - bybit (coming soon)

telegram:
  token: ${TELEGRAM_BOT_TOKEN}
  chat_id: ${TELEGRAM_CHAT_ID}

thresholds:
  major: 0.0008      # 0.08%
  mid: 0.0012        # 0.12%
  alt: 0.0020        # 0.20%
  exotic: 0.0030     # 0.30%

scanning:
  interval_seconds: 5
  cooldown_minutes: 30

assets:
  include_all: true  # Scan everything
  # OR specify list:
  # whitelist: [BTC, ETH, SOL]
```

## Alert Format

### HIGH Priority Alert
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
• Volume: $2.1B
• Score: 0.62

Next funding: ~8 hours
```

### Daily Summary
```
📊 Top 3 Opportunities

1. PEPE: 0.185% spread (score: 0.62)
2. DOGE: 0.142% spread (score: 0.45)
3. HYPE: 0.098% spread (score: 0.31)
```

## Commands

### Start Scanner
```bash
python3 scripts/funding_scanner.py
```

### Start with Config
```bash
python3 scripts/funding_scanner.py --config config.yaml
```

### Run as Background Service
```bash
./scripts/install_service.sh
sudo systemctl start funding-arb-alerts
```

### Check Logs
```bash
tail -f logs/funding_scanner.log
```

## File Structure

```
funding-arb-alert-skill/
├── SKILL.md                    # This file
├── config.yaml                 # Configuration
├── scripts/
│   ├── funding_scanner.py     # Main scanner
│   ├── setup.py               # Setup wizard
│   ├── install_service.sh     # Systemd installer
│   └── backtest.py            # Historical testing
├── references/
│   ├── exchanges.md           # Exchange API docs
│   ├── strategy_guide.md      # Arb strategy details
│   └── risk_management.md     # Risk controls
└── assets/
    └── alert_templates/       # Telegram message templates
```

## Advanced Usage

### Backtest Strategy
```bash
python3 scripts/backtest.py --start-date 2024-01-01 --end-date 2024-03-01
```

### Add Custom Exchange
Edit `scripts/exchanges/custom.py`:
```python
class CustomExchange:
    async def get_funding(self, symbol):
        # Your implementation
        pass
```

### Modify Scoring Algorithm
Edit `scripts/scoring.py` to customize opportunity calculation.

## Risk Management

### Automatic Safeguards
- ❌ No alerts during extreme volatility (>10% 1h move)
- ❌ Cooldown periods prevent spam
- ❌ Minimum OI check ($1M+)
- ❌ Exchange health monitoring

### Manual Controls
```bash
# Pause alerts
python3 scripts/control.py pause

# Resume
python3 scripts/control.py resume

# Emergency stop
python3 scripts/control.py stop
```

## Troubleshooting

### No alerts received
1. Check Telegram bot token: `echo $TELEGRAM_BOT_TOKEN`
2. Verify chat ID: `echo $TELEGRAM_CHAT_ID`
3. Test bot: `python3 scripts/test_telegram.py`
4. Check logs: `tail -20 logs/funding_scanner.log`

### Rate limit errors
- Increase `interval_seconds` in config
- Reduce number of exchanges
- Use exchange API keys for higher limits

### Process keeps dying
- Run with systemd: `./scripts/install_service.sh`
- Or use tmux: `tmux new -s funding-bot`

## Expected Performance

| Metric | Value |
|--------|-------|
| Markets scanned | 200+ per exchange |
| Scan interval | 5 seconds |
| Alert latency | < 10 seconds |
| Memory usage | ~100MB |
| CPU usage | < 5% |

## Returns (Example)

| Market Condition | Avg Spread | Annual Return |
|------------------|------------|---------------|
| Calm | 0.02% | 15-25% |
| Normal | 0.08% | 50-80% |
| Volatile | 0.20% | 150-200% |

*Returns vary based on capital, execution, and market conditions*

## Contributing

To add features or exchanges:
1. Fork the repository
2. Add your changes
3. Test thoroughly
4. Submit PR

## License

MIT - Use at your own risk. Not financial advice.

## Disclaimer

This tool is for educational purposes. Cryptocurrency trading carries significant risk. Always:
- Start with small capital
- Test thoroughly before scaling
- Understand the risks of 雙開 (double-sided) strategies
- Never risk more than you can afford to lose

## Support

- GitHub Issues: Report bugs
- Telegram: @your_support_channel
- Documentation: See references/ folder
