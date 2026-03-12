#!/bin/bash
# Start the multi-asset opportunity scanner

cd /opt/will-learning-track/bots

# Kill old monitors
pkill -f monitor_live.py 2>/dev/null
pkill -f multi_asset_scanner.py 2>/dev/null
sleep 2

# Set credentials
export TELEGRAM_BOT_TOKEN='8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA'
export TELEGRAM_CHAT_ID='-1003832962281'

# Start new scanner
nohup python3 multi_asset_scanner.py > ../logs/multi_asset.log 2>&1 &
echo $! > multi_asset.pid

echo "✅ Multi-Asset Scanner Started!"
echo "PID: $(cat multi_asset.pid)"
echo "Log: tail -f /opt/will-learning-track/logs/multi_asset.log"
echo ""
echo "Scanning: ALL perpetual markets (200+ from Binance, 100+ from Hyperliquid)"
echo "Alerting: Only HIGH opportunity scores"
