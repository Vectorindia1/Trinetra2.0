#!/usr/bin/env python3

import requests
import time

def test_direct_tor():
    """Test direct connection to Tor SOCKS5 proxy"""
    
    # Direct SOCKS5 proxy to Tor (bypass Privoxy)
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    
    print("🔍 Testing Direct Tor SOCKS5 Connection")
    print("=" * 45)
    print("Bypassing Privoxy - connecting directly to Tor")
    
    # Test 1: Regular website through Tor
    print("\\n1. Testing regular website through Tor...")
    try:
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Tor IP: {data.get('origin', 'unknown')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Simple onion service
    print("\\n2. Testing DuckDuckGo onion directly...")
    try:
        start = time.time()
        response = requests.get(
            'http://3g2upl4pq6kufc4m.onion',
            proxies=proxies,
            timeout=60,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"   ✅ SUCCESS! ({elapsed:.1f}s) - {len(response.content)} bytes")
            print("   🎉 Direct Tor connection works!")
            return True
        else:
            print(f"   ⚠️ Status: {response.status_code} ({elapsed:.1f}s)")
            
    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT after 60s")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
    
    return False

if __name__ == "__main__":
    print("Testing if the issue is with Privoxy or Tor itself...")
    print()
    
    success = test_direct_tor()
    
    print("\\n" + "=" * 45)
    if success:
        print("✅ DIRECT TOR WORKS!")
        print("The issue is with the Privoxy configuration.")
        print("\\n💡 SOLUTION: Update crawler to use direct SOCKS5:")
        print("   Proxy: socks5h://127.0.0.1:9050")
        print("   (No need for Privoxy)")
    else:
        print("❌ DIRECT TOR ALSO FAILS")
        print("The issue is with Tor itself or network restrictions.")
        print("\\n💡 TROUBLESHOOTING:")
        print("   1. Check ISP blocks Tor traffic")
        print("   2. Try Tor bridges")
        print("   3. Test from different network")
