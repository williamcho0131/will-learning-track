#!/bin/bash
# Quick restart script for market monitor

cd /opt/will-learning-track/bots

# Kill existing
pkill -f monitor_live.py 2>/dev/null
sleep 1

# Set env
export TELEGRAM_BOT_TOKEN='8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA'
export TELEGRAM_CHAT_ID='-1003832962281'

# Start new
nohup python3 monitor_live.py >> ../logs/monitor.log 2>&1 &
echo $! > monitor.pid

echo "✅ Monitor restarted (PID: $(cat monitor.pid))"
echo "Log: tail -f /opt/will-learning-track/logs/monitor.log"
