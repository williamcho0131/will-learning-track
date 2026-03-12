#!/usr/bin/env python3
"""
Setup wizard for Funding Arbitrage Alert Bot
"""

import os
import sys
import yaml

print("="*60)
print("🚀 Funding Arbitrage Alert Bot - Setup Wizard")
print("="*60)

# Check Python version
if sys.version_info < (3, 8):
    print("❌ Python 3.8+ required")
    sys.exit(1)

print("\n📋 Step 1: Install Dependencies")
print("-" * 40)
print("Running: pip install aiohttp pyyaml")
os.system("pip install -q aiohttp pyyaml")
print("✅ Dependencies installed")

print("\n📋 Step 2: Telegram Bot Configuration")
print("-" * 40)
print("1. Message @BotFather on Telegram")
print("2. Create a new bot: /newbot")
print("3. Copy the bot token (starts with numbers:letters)")
print("4. Message @userinfobot to get your chat ID")
print()

token = input("Enter your Telegram Bot Token: ").strip()
chat_id = input("Enter your Telegram Chat ID: ").strip()

# Test Telegram
print("\n📋 Step 3: Testing Telegram Connection")
print("-" * 40)

try:
    import aiohttp
    import asyncio
    
    async def test_telegram():
        url = f"https://api.telegram.org/bot{token}/getMe"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get('ok'):
                    print(f"✅ Bot connected: @{data['result']['username']}")
                    # Send test message
                    msg_url = f"https://api.telegram.org/bot{token}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": "🧪 Funding Arb Bot setup test successful!",
                        "parse_mode": "HTML"
                    }
                    async with session.post(msg_url, json=payload) as resp2:
                        if resp2.status == 200:
                            print("✅ Test message sent to your Telegram")
                            return True
                else:
                    print(f"❌ Bot error: {data}")
                    return False
    
    success = asyncio.run(test_telegram())
    if not success:
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Telegram test failed: {e}")
    sys.exit(1)

print("\n📋 Step 4: Creating Configuration")
print("-" * 40)

# Load template
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Update with user values
config['telegram']['token'] = token
config['telegram']['chat_id'] = chat_id

# Save
with open('config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)

print("✅ Configuration saved to config.yaml")

print("\n📋 Step 5: Creating Environment File")
print("-" * 40)

env_content = f"""# Funding Arbitrage Alert Bot Environment
TELEGRAM_BOT_TOKEN={token}
TELEGRAM_CHAT_ID={chat_id}
"""

with open('.env', 'w') as f:
    f.write(env_content)

print("✅ Environment file saved to .env")

print("\n" + "="*60)
print("✅ Setup Complete!")
print("="*60)
print("\nTo start the bot:")
print("  python3 scripts/funding_scanner.py")
print("\nTo run in background:")
print("  nohup python3 scripts/funding_scanner.py &")
print("\nTo check logs:")
print("  tail -f logs/funding_scanner.log")
print("\n" + "="*60)
