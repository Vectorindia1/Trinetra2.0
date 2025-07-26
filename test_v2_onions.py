#!/usr/bin/env python3

import requests
import time

def test_v2_onions():
    """Test with known stable v2 onion addresses (16 char)"""
    
    # Reliable v2 onion services (shorter addresses are more stable)
    v2_onions = [
        'http://3g2upl4pq6kufc4m.onion',        # DuckDuckGo
        'http://facebookcorewwwi.onion',        # Facebook (v2)
        'http://expyuzz4wqqyqhjn.onion',        # ProPublica
        'http://rougmnvswfsmd4dq.onion',        # Mail2Tor
    ]
    
    proxies = {
        'http': 'http://127.0.0.1:8118',
        'https': 'http://127.0.0.1:8118'
    }
    
    print("🔍 Testing V2 Onion Services")
    print("=" * 40)
    
    working = []
    
    for url in v2_onions:
        print(f"\\nTesting: {url}")
        try:
            start = time.time()
            response = requests.get(
                url,
                proxies=proxies,
                timeout=60,  # Shorter timeout for v2
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS! ({elapsed:.1f}s) - {len(response.content)} bytes")
                working.append((url, elapsed, len(response.content)))
            else:
                print(f"  ⚠️ Status: {response.status_code} ({elapsed:.1f}s)")
                
        except requests.exceptions.Timeout:
            print(f"  ❌ TIMEOUT after 60s")
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:80]}")
        
        # Small delay between requests
        time.sleep(3)
    
    print("\\n" + "=" * 40)
    print("RESULTS:")
    print("=" * 40)
    
    if working:
        print(f"\\n✅ WORKING SERVICES ({len(working)}):")
        for url, elapsed, size in working:
            print(f"  🟢 {url}")
            print(f"     Time: {elapsed:.1f}s | Size: {size} bytes")
        
        # Recommend the fastest one
        fastest = min(working, key=lambda x: x[1])
        print(f"\\n🚀 RECOMMENDED FOR CRAWLER:")
        print(f"   URL: {fastest[0]}")
        print(f"   Average response: {fastest[1]:.1f} seconds")
        print(f"   Suggested timeout: {int(fastest[1] * 2) + 30} seconds")
        
        return True
    else:
        print("\\n❌ No working onion services found")
        print("This indicates a Tor connectivity issue")
        return False

if __name__ == "__main__":
    success = test_v2_onions()
    if success:
        print("\\n🎉 Your Tor setup is working! You can use the recommended URL above.")
    else:
        print("\\n⚠️ Network issues detected. Check Tor configuration and network connectivity.")
