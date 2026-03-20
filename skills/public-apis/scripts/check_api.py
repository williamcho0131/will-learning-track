#!/usr/bin/env python3
"""
Check if an API is online and responding
"""

import requests
import sys
import time
from argparse import ArgumentParser

def check_api(url, timeout=10):
    """Check if API endpoint is responding"""
    try:
        start = time.time()
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Public-APIs-Checker/1.0'
        })
        elapsed = time.time() - start
        
        status = response.status_code
        
        if status == 200:
            print(f"✅ API is ONLINE")
            print(f"   Status: {status} OK")
            print(f"   Response time: {elapsed:.2f}s")
            print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
            return True
        elif status == 401:
            print(f"⚠️  API requires authentication")
            print(f"   Status: {status}")
            return True  # API exists, just needs auth
        elif status == 429:
            print(f"⚠️  Rate limited")
            print(f"   Status: {status}")
            return True  # API exists, just rate limited
        else:
            print(f"⚠️  API returned status {status}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout after {timeout}s")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error - API may be down")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    parser = ArgumentParser(description='Check API availability')
    parser.add_argument('url', help='API URL to check')
    parser.add_argument('--timeout', '-t', type=int, default=10, help='Timeout in seconds')
    
    args = parser.parse_args()
    
    print(f"🔍 Checking: {args.url}\n")
    
    success = check_api(args.url, args.timeout)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
