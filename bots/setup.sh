#!/bin/bash
# Setup script for Market Alert Bot

set -e

echo "🔧 Setting up Market Alert Bot..."

# Create directories
mkdir -p /opt/will-learning-track/bots
mkdir -p /opt/will-learning-track/data
mkdir -p /opt/will-learning-track/logs

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -q ccxt python-telegram-bot aiohttp 2>/dev/null || {
    echo "⚠️  pip install failed, you may need to run manually:"
    echo "   pip install ccxt python-telegram-bot aiohttp"
}

# Check environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo ""
    echo "⚠️  WARNING: TELEGRAM_BOT_TOKEN not set"
    echo "   Get it from @BotFather on Telegram"
    echo "   Then run: export TELEGRAM_BOT_TOKEN='your_token'"
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo ""
    echo "⚠️  WARNING: TELEGRAM_CHAT_ID not set"
    echo "   Get it by messaging @userinfobot on Telegram"
    echo "   Then run: export TELEGRAM_CHAT_ID='your_chat_id'"
fi

# Create systemd service files
echo "📝 Creating systemd services..."

# Alert bot service
cat > /tmp/alert-bot.service << 'EOF'
[Unit]
Description=Market Alert Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/will-learning-track/bots
Environment="TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE"
Environment="TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE"
ExecStart=/usr/bin/python3 /opt/will-learning-track/bots/market_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Daily snapshot service
cat > /tmp/snapshot-daily.service << 'EOF'
[Unit]
Description=Daily Market Snapshot
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=/opt/will-learning-track/bots
ExecStart=/usr/bin/python3 /opt/will-learning-track/bots/market_monitor.py --snapshot
EOF

# Daily snapshot timer
cat > /tmp/snapshot-daily.timer << 'EOF'
[Unit]
Description=Run daily market snapshot at 8 AM

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set your Telegram credentials:"
echo "   export TELEGRAM_BOT_TOKEN='your_token'"
echo "   export TELEGRAM_CHAT_ID='your_chat_id'"
echo ""
echo "2. Install systemd services (optional):"
echo "   sudo cp /tmp/alert-bot.service /etc/systemd/system/"
echo "   sudo cp /tmp/snapshot-daily.service /etc/systemd/system/"
echo "   sudo cp /tmp/snapshot-daily.timer /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now alert-bot"
echo "   sudo systemctl enable --now snapshot-daily.timer"
echo ""
echo "3. Or run manually:"
echo "   cd /opt/will-learning-track/bots"
echo "   python3 market_monitor.py              # Alert bot"
echo "   python3 market_monitor.py --snapshot   # Daily snapshot"
echo ""
