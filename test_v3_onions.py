#!/usr/bin/env python3

import requests
import time

def test_v3_onions():
    """Test with known active V3 onion addresses (56 chars)"""
    
    # Known working V3 onion services (as of 2024/2025)
    v3_onions = [
        # Facebook V3
        'http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion',
        
        # DuckDuckGo V3  
        'http://duckduckgogg42ts72.onion',
        
        # ProPublica V3
        'http://p53lf57qovyuvwsc6xnrppddxpr23otqjafljkxg5b5pz3jvfqc4rnid.onion',
        
        # The New York Times V3
        'http://nytimesn7cgmftshazwhfgzm37qxb4r64yvkb5c3kpdl5d2c6yv5y6sd.onion',
    ]
    
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    
    print("🔍 Testing V3 Onion Services (Direct SOCKS5)")
    print("=" * 50)
    print("Using newer V3 onion addresses...")
    
    working = []
    
    for url in v3_onions:
        print(f"\\nTesting: {url[:50]}...")
        try:
            start = time.time()
            response = requests.get(
                url,
                proxies=proxies,
                timeout=90,  # Longer timeout for V3
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                }
            )
            elapsed = time.time() - start
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS! ({elapsed:.1f}s) - {len(response.content)} bytes")
                working.append((url, elapsed, len(response.content)))
            elif response.status_code in [301, 302, 403]:
                print(f"  🟡 PARTIAL SUCCESS - Status: {response.status_code} ({elapsed:.1f}s)")
                print("     (Site is responding, may have restrictions)")
                working.append((url, elapsed, len(response.content)))
            else:
                print(f"  ⚠️ Status: {response.status_code} ({elapsed:.1f}s)")
                
        except requests.exceptions.Timeout:
            print(f"  ❌ TIMEOUT after 90s")
        except requests.exceptions.ConnectionError as e:
            error_str = str(e)
            if "503" in error_str:
                print(f"  ❌ Service unavailable (503)")
            elif "SOCKS5" in error_str:
                print(f"  ❌ SOCKS5 proxy error")
            else:
                print(f"  ❌ Connection error: {error_str[:60]}...")
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:80]}...")
        
        # Delay between requests to be respectful
        print("     Waiting 5 seconds...")
        time.sleep(5)
    
    print("\\n" + "=" * 50)
    print("FINAL RESULTS:")
    print("=" * 50)
    
    if working:
        print(f"\\n✅ WORKING SERVICES ({len(working)}):")
        for url, elapsed, size in working:
            short_url = url[:60] + "..." if len(url) > 60 else url
            print(f"  🟢 {short_url}")
            print(f"     Response time: {elapsed:.1f}s | Size: {size} bytes")
        
        # Save working URLs
        with open('working_onions.txt', 'w') as f:
            f.write("# Working Onion URLs\\n")
            f.write(f"# Tested: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            for url, elapsed, size in working:
                f.write(f"{url}\\n")
        
        # Recommend the fastest one
        fastest = min(working, key=lambda x: x[1])
        print(f"\\n🚀 RECOMMENDED URL:")
        print(f"   {fastest[0]}")
        print(f"   Average time: {fastest[1]:.1f}s")
        print(f"   Suggested timeout: {int(fastest[1] * 2) + 60} seconds")
        
        print(f"\\n🔧 CRAWLER CONFIGURATION:")
        print(f"   Proxy: socks5h://127.0.0.1:9050")
        print(f"   Timeout: {int(fastest[1] * 2) + 60} seconds")
        print(f"   Retry delay: 10-15 seconds")
        
        return True
    else:
        print("\\n❌ No working onion services found")
        print("\\n🔧 TROUBLESHOOTING:")
        print("   1. Your ISP might be blocking Tor traffic")
        print("   2. Try using Tor bridges:")
        print("      - Get bridges from https://bridges.torproject.org/")
        print("   3. Test from a different network (mobile hotspot)")
        print("   4. Consider using a VPN + Tor combination")
        return False

if __name__ == "__main__":
    success = test_v3_onions()
    if success:
        print("\\n🎉 SUCCESS! Your Tor setup can access onion services!")
        print("You can now use the working URLs for your crawler.")
    else:
        print("\\n⚠️ No onion services accessible.")
        print("This indicates network-level restrictions on Tor/onion traffic.")
