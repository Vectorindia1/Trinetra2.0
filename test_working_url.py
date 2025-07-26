#!/usr/bin/env python3
"""
Simple working URL test for dark web crawling
Uses the most reliable approach for testing onion connectivity
"""

import requests
import time

def test_simple_onion_access():
    """Test the most basic onion access"""
    print("🔧 Testing simple onion access...")
    
    # Use a v2 onion which is often more reliable
    test_urls = [
        'http://3g2upl4pq6kufc4m.onion',  # DuckDuckGo v2
        'http://duckduckgogg42ts72.onion',  # DuckDuckGo v2 alt
    ]
    
    # Configure session for reliability
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # Try different proxy approaches
    proxy_configs = [
        {'http': 'http://127.0.0.1:8118', 'https': 'http://127.0.0.1:8118'},  # Privoxy
        {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'},  # Direct SOCKS5
    ]
    
    for i, proxies in enumerate(proxy_configs):
        proxy_name = "Privoxy" if i == 0 else "Direct SOCKS5"
        print(f"\n🔍 Testing with {proxy_name}...")
        
        for url in test_urls:
            try:
                print(f"  Testing: {url}")
                response = session.get(
                    url,
                    proxies=proxies,
                    timeout=20,  # Shorter timeout
                    verify=False
                )
                
                if response.status_code == 200:
                    print(f"  ✅ SUCCESS: {url} is accessible via {proxy_name}")
                    print(f"     Status: {response.status_code}")
                    print(f"     Content length: {len(response.content)} bytes")
                    return True, url, proxy_name, proxies
                else:
                    print(f"  ⚠️ Response code: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"  ❌ Timeout: {url}")
            except requests.exceptions.ProxyError as e:
                print(f"  ❌ Proxy error: {e}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    return False, None, None, None

def create_working_crawler_command(working_url, proxy_config):
    """Create a working crawler command"""
    if working_url and proxy_config:
        print(f"\n🚀 WORKING CONFIGURATION FOUND!")
        print(f"   URL: {working_url}")
        print(f"   Proxy: {list(proxy_config.values())[0]}")
        
        # Create a simple test command
        if 'socks5' in str(proxy_config.values()):
            print(f"\n💡 Use this URL for testing your crawler:")
            print(f"   {working_url}")
            print(f"\n🔧 Configure your crawler to use SOCKS5 proxy:")
            print(f"   Proxy: socks5://127.0.0.1:9050")
        else:
            print(f"\n💡 Use this URL for testing your crawler:")
            print(f"   {working_url}")
            print(f"\n🔧 Configure your crawler to use HTTP proxy:")
            print(f"   Proxy: http://127.0.0.1:8118")

if __name__ == "__main__":
    print("🕷️ Dark Web Connectivity Tester")
    print("=" * 50)
    
    success, working_url, proxy_name, proxy_config = test_simple_onion_access()
    
    if success:
        create_working_crawler_command(working_url, proxy_config)
        print(f"\n✅ Your system can access .onion sites!")
        print(f"   Try using the crawler with the working configuration above.")
    else:
        print(f"\n❌ No working .onion connectivity found.")
        print(f"\n🔧 Troubleshooting steps:")
        print(f"   1. Check if Tor is running: systemctl status tor")
        print(f"   2. Check if Privoxy is running: systemctl status privoxy") 
        print(f"   3. Restart both services:")
        print(f"      sudo systemctl restart tor")
        print(f"      sudo systemctl restart privoxy")
        print(f"   4. Check your network/ISP doesn't block Tor")
        print(f"   5. Consider using Tor bridges if needed")
