#!/bin/bash
# Start the new alt-focused bots
# Run once, then they auto-run forever

echo "🚀 Starting new alt-focused bots..."

# Stop old bots
systemctl stop funding-scanner 2>/dev/null
systemctl stop bigmove-bot 2>/dev/null
pkill -f ultimate_funding_scanner 2>/dev/null
pkill -f ultimate_big_move_alert 2>/dev/null
sleep 2

# Reload systemd
daemon-reload

# Enable and start NEW bots
systemctl enable alt-arbitrage.service
systemctl enable fifteen-minute-movers.service

systemctl start alt-arbitrage.service
systemctl start fifteen-minute-movers.service

echo ""
echo "📊 Status:"
systemctl is-active alt-arbitrage && echo "✅ Alt Arbitrage Scanner: RUNNING" || echo "❌ Failed"
systemctl is-active fifteen-minute-movers && echo "✅ 15-Min Movers Bot: RUNNING" || echo "❌ Failed"

echo ""
echo "📋 Bot Details:"
echo ""
echo "🔥 Alt Arbitrage Scanner:"
echo "  - Scans every 1 second"
echo "  - 37 alt coins (SOL, LINK, ARB, PEPE, etc)"
echo "  - Detects basis + funding arbitrage"
echo "  - Only alerts on score ≥ 8.0"
echo ""
echo "📊 15-Minute Movers:"
echo "  - Scans every 1 second"
echo "  - 20 cryptos + 10 stocks"
echo "  - Reports top 10 movers every 15 min"
echo "  - Shows % change in 15-min window"
echo ""
echo "📁 Log Files:"
echo "  tail -f /opt/will-learning-track/logs/alt_arbitrage.log"
echo "  tail -f /opt/will-learning-track/logs/fifteen_minute_movers.log"
