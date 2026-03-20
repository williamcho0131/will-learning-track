#!/bin/bash
# Start trading bots as systemd services
# Run once, then they auto-start forever

echo "🚀 Setting up trading bot services..."

# Stop any existing processes
pkill -f ultimate_funding_scanner 2>/dev/null
pkill -f ultimate_big_move_alert 2>/dev/null
sleep 2

# Reload systemd
daemon-reload

# Enable services (start on boot)
systemctl enable funding-scanner.service
systemctl enable bigmove-bot.service

# Start services
systemctl start funding-scanner.service
systemctl start bigmove-bot.service

# Wait and check
sleep 3

echo ""
echo "📊 Status:"
systemctl is-active funding-scanner.service && echo "✅ Funding Scanner: RUNNING" || echo "❌ Funding Scanner: FAILED"
systemctl is-active bigmove-bot.service && echo "✅ Big Move Bot: RUNNING" || echo "❌ Big Move Bot: FAILED"

echo ""
echo "📋 Management Commands:"
echo "  systemctl status funding-scanner  - Check funding bot"
echo "  systemctl status bigmove-bot      - Check big move bot"
echo "  systemctl restart funding-scanner - Restart funding bot"
echo "  systemctl restart bigmove-bot     - Restart big move bot"
echo "  systemctl stop funding-scanner    - Stop funding bot"
echo "  systemctl stop bigmove-bot        - Stop big move bot"

echo ""
echo "📁 Log Files:"
echo "  tail -f /opt/will-learning-track/logs/ultimate_funding.log"
echo "  tail -f /opt/will-learning-track/logs/ultimate_bigmove.log"
