#!/usr/bin/env python3
"""
Query the Public APIs repository
Search and filter APIs by category, authentication, and more
"""

import requests
import json
import sys
from argparse import ArgumentParser

# Public APIs raw JSON URL
API_LIST_URL = "https://raw.githubusercontent.com/public-apis/public-apis/master/db/resources.json"

def fetch_apis():
    """Fetch the latest API list from GitHub"""
    try:
        response = requests.get(API_LIST_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching APIs: {e}")
        # Fallback: use local cache if available
        try:
            with open('data/apis_cache.json', 'r') as f:
                return json.load(f)
        except:
            return []

def list_categories(apis):
    """List all available categories"""
    categories = set()
    for api in apis:
        cat = api.get('category', 'Uncategorized')
        categories.add(cat)
    return sorted(categories)

def search_apis(apis, query, category=None, auth=None):
    """Search APIs by query string"""
    results = []
    query_lower = query.lower()
    
    for api in apis:
        # Category filter
        if category and api.get('category') != category:
            continue
        
        # Auth filter
        if auth and api.get('auth', '').lower() != auth.lower():
            continue
        
        # Search in name, description, and category
        searchable = f"{api.get('name', '')} {api.get('description', '')} {api.get('category', '')}".lower()
        if query_lower in searchable:
            results.append(api)
    
    return results

def display_api(api):
    """Display API information nicely"""
    print(f"\n{'='*60}")
    print(f"📡 {api.get('name', 'Unknown')}")
    print(f"{'='*60}")
    print(f"Description: {api.get('description', 'N/A')}")
    print(f"Category: {api.get('category', 'N/A')}")
    print(f"Auth: {api.get('auth', 'None') or 'None'}")
    print(f"HTTPS: {'Yes' if api.get('https', False) else 'No'}")
    print(f"CORS: {api.get('cors', 'Unknown')}")
    print(f"Link: {api.get('url', 'N/A')}")
    print(f"{'='*60}")

def main():
    parser = ArgumentParser(description='Query Public APIs repository')
    parser.add_argument('--search', '-s', help='Search query')
    parser.add_argument('--category', '-c', help='Filter by category')
    parser.add_argument('--auth', '-a', help='Filter by auth type (None, apiKey, OAuth)')
    parser.add_argument('--list-categories', '-l', action='store_true', help='List all categories')
    parser.add_argument('--no-auth', action='store_true', help='Show only no-auth APIs')
    parser.add_argument('--limit', type=int, default=10, help='Limit results')
    
    args = parser.parse_args()
    
    print("🌐 Fetching Public APIs...")
    apis = fetch_apis()
    
    if not apis:
        print("❌ Could not fetch APIs")
        sys.exit(1)
    
    print(f"✅ Loaded {len(apis)} APIs\n")
    
    # List categories
    if args.list_categories:
        categories = list_categories(apis)
        print("📂 Available Categories:")
        for cat in categories:
            count = sum(1 for a in apis if a.get('category') == cat)
            print(f"  • {cat} ({count} APIs)")
        return
    
    # Build search
    query = args.search or ""
    auth_filter = None
    
    if args.no_auth:
        auth_filter = "None"
    elif args.auth:
        auth_filter = args.auth
    
    # Search
    results = search_apis(apis, query, args.category, auth_filter)
    
    # Display
    print(f"🔍 Found {len(results)} results")
    if results:
        for api in results[:args.limit]:
            display_api(api)
        
        if len(results) > args.limit:
            print(f"\n... and {len(results) - args.limit} more (use --limit to show more)")
    else:
        print("\n💡 Try:")
        print("  • Broader search terms")
        print("  • Different category")
        print("  • python3 query_apis.py --list-categories")

if __name__ == "__main__":
    main()
