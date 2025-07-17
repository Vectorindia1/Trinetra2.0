#!/usr/bin/env python3
"""
Tor Connectivity Test Script
Tests connection to reliable .onion sites
"""

import requests
import time
from datetime import datetime

# Reliable .onion sites for testing
RELIABLE_ONION_SITES = [
    {
        "name": "DuckDuckGo",
        "url": "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion",
        "description": "Search engine"
    },
    {
        "name": "ProPublica",
        "url": "http://p53lf57qovyuvwsc6xnrppddxpr23otqjafbbhhoybztpfepdpgm2dyad.onion",
        "description": "News site"
    },
    {
        "name": "The New York Times",
        "url": "http://nytimenxaqidzhv6qbj7ppqzdyf7t7ysxvlomngshknnrh53h76u3inad.onion",
        "description": "News site"
    },
    {
        "name": "BBC News",
        "url": "http://bbcnewsv2vjtpsuy.onion",
        "description": "News site"
    },
    {
        "name": "Hidden Wiki",
        "url": "http://zqktlwiuavvvqqt4ybvgvi7tyo4hjl5xgfuvpdf6otjiycgwqbym2qad.onion",
        "description": "Directory site"
    }
]

def test_proxy_connection():
    """Test if Tor proxy is working"""
    print("🔍 Testing Tor Proxy Connection...")
    
    proxies = {
        'http': 'http://127.0.0.1:8118',
        'https': 'http://127.0.0.1:8118'
    }
    
    try:
        # Test with a clearnet site first
        response = requests.get('http://httpbin.org/ip', 
                              proxies=proxies, 
                              timeout=10)
        if response.status_code == 200:
            ip_info = response.json()
            print(f"✅ Proxy working - External IP: {ip_info.get('origin', 'Unknown')}")
            return True
        else:
            print(f"❌ Proxy test failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Proxy connection failed: {e}")
        return False

def test_onion_site(site_info):
    """Test connection to a specific .onion site"""
    print(f"\n🧅 Testing {site_info['name']}...")
    print(f"   URL: {site_info['url']}")
    
    proxies = {
        'http': 'http://127.0.0.1:8118',
        'https': 'http://127.0.0.1:8118'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        start_time = time.time()
        response = requests.get(site_info['url'], 
                              proxies=proxies,
                              headers=headers,
                              timeout=30,
                              allow_redirects=True)
        
        response_time = time.time() - start_time
        
        print(f"   Status: {response.status_code}")
        print(f"   Response Time: {response_time:.2f}s")
        print(f"   Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print(f"   ✅ {site_info['name']} is accessible!")
            return True, site_info['url']
        else:
            print(f"   ⚠️ {site_info['name']} returned status {response.status_code}")
            return False, None
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ {site_info['name']} timed out")
        return False, None
    except Exception as e:
        print(f"   ❌ {site_info['name']} failed: {e}")
        return False, None

def main():
    print("🕵️ TOR CONNECTIVITY TEST")
    print("=" * 50)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test proxy connection first
    if not test_proxy_connection():
        print("\n❌ Tor proxy is not working. Please check:")
        print("   1. Tor service is running: sudo systemctl status tor")
        print("   2. Privoxy is running: sudo systemctl status privoxy")
        print("   3. Port 8118 is open: netstat -tlnp | grep 8118")
        return
    
    print("\n🧅 Testing .onion sites...")
    print("-" * 30)
    
    working_sites = []
    failed_sites = []
    
    for site in RELIABLE_ONION_SITES:
        success, url = test_onion_site(site)
        if success:
            working_sites.append(url)
        else:
            failed_sites.append(site['name'])
        
        # Small delay between tests
        time.sleep(2)
    
    print("\n📊 TEST RESULTS")
    print("=" * 50)
    print(f"✅ Working sites: {len(working_sites)}")
    print(f"❌ Failed sites: {len(failed_sites)}")
    
    if working_sites:
        print("\n🟢 WORKING .ONION SITES:")
        for url in working_sites:
            print(f"   • {url}")
        print(f"\n💡 Use any of these URLs in your TRINETRA dashboard!")
        
        # Suggest the best one for testing
        best_site = working_sites[0]
        print(f"\n🎯 RECOMMENDED FOR TESTING:")
        print(f"   {best_site}")
        print(f"\n📋 Copy this URL and paste it into your Manual TOR Scraper!")
    
    if failed_sites:
        print(f"\n🔴 FAILED SITES:")
        for site in failed_sites:
            print(f"   • {site}")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
