#!/usr/bin/env python3
"""
Master Bot Orchestrator
Manages all alpha-hunting bots
"""

import asyncio
import subprocess
import os
from datetime import datetime

BOTS = {
    'funding_arb': {
        'script': 'multi_asset_scanner.py',
        'description': 'Funding rate arbitrage across exchanges',
        'status': 'running'
    },
    'big_move': {
        'script': 'big_move_alert.py',
        'description': 'Stock/crypto big move detection with news',
        'status': 'ready'
    },
    'polymarket': {
        'script': 'polymarket_arb.py',
        'description': 'Polymarket probability arbitrage',
        'status': 'ready'
    },
    'alpha_snipe': {
        'script': 'alpha_snipe.py',
        'description': 'New listings and protocol sniper',
        'status': 'ready'
    }
}

def print_status():
    """Print status of all bots"""
    print("="*60)
    print("🤖 Alpha Bot Army - Status Dashboard")
    print("="*60)
    print(f"{'Bot':<20} {'Status':<10} {'Description'}")
    print("-"*60)
    
    for name, info in BOTS.items():
        status_emoji = "🟢" if info['status'] == 'running' else "⚪"
        print(f"{name:<20} {status_emoji} {info['status']:<8} {info['description']}")
    
    print("="*60)

def start_bot(name):
    """Start a specific bot"""
    if name not in BOTS:
        print(f"❌ Unknown bot: {name}")
        return
    
    bot = BOTS[name]
    script_path = f"/opt/will-learning-track/bots/{bot['script']}"
    
    print(f"Starting {name}...")
    
    # Set environment
    env = os.environ.copy()
    env['TELEGRAM_BOT_TOKEN'] = '8472788444:AAH59Lk_kEgSkhTfv6qlcfI8Ow-ffXDvnOA'
    env['TELEGRAM_CHAT_ID'] = '-1003832962281'
    
    # Start in background
    log_file = f"/opt/will-learning-track/logs/{name}.log"
    
    subprocess.Popen(
        ['python3', script_path],
        stdout=open(log_file, 'a'),
        stderr=subprocess.STDOUT,
        env=env,
        start_new_session=True
    )
    
    print(f"✅ {name} started (log: {log_file})")

def stop_bot(name):
    """Stop a specific bot"""
    import signal
    
    # Find and kill process
    result = subprocess.run(
        ['pgrep', '-f', BOTS[name]['script']],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        for pid in result.stdout.strip().split('\n'):
            if pid:
                os.kill(int(pid), signal.SIGTERM)
        print(f"🛑 {name} stopped")
    else:
        print(f"⚠️ {name} not running")

def start_all():
    """Start all bots"""
    print("Starting all bots...")
    for name in BOTS:
        if BOTS[name]['status'] == 'ready':
            start_bot(name)

def stop_all():
    """Stop all bots"""
    print("Stopping all bots...")
    for name in BOTS:
        stop_bot(name)

def show_logs(name=None):
    """Show logs for a bot or all bots"""
    if name:
        log_file = f"/opt/will-learning-track/logs/{name}.log"
        print(f"\n{'='*60}")
        print(f"📜 Logs for {name}")
        print('='*60)
        subprocess.run(['tail', '-20', log_file])
    else:
        for bot_name in BOTS:
            show_logs(bot_name)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print_status()
        print("\nUsage:")
        print("  python3 bot_orchestrator.py status")
        print("  python3 bot_orchestrator.py start <bot_name|all>")
        print("  python3 bot_orchestrator.py stop <bot_name|all>")
        print("  python3 bot_orchestrator.py logs [bot_name]")
        print("\nBots: funding_arb, big_move, polymarket, alpha_snipe")
    
    else:
        command = sys.argv[1]
        
        if command == 'status':
            print_status()
        
        elif command == 'start':
            if len(sys.argv) > 2:
                target = sys.argv[2]
                if target == 'all':
                    start_all()
                else:
                    start_bot(target)
            else:
                print("❌ Specify bot name or 'all'")
        
        elif command == 'stop':
            if len(sys.argv) > 2:
                target = sys.argv[2]
                if target == 'all':
                    stop_all()
                else:
                    stop_bot(target)
            else:
                print("❌ Specify bot name or 'all'")
        
        elif command == 'logs':
            if len(sys.argv) > 2:
                show_logs(sys.argv[2])
            else:
                show_logs()
        
        else:
            print(f"❌ Unknown command: {command}")
