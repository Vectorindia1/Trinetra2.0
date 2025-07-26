#!/usr/bin/env python3
"""
Test Multiple Onion Services
Find a working onion service for your crawler
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class OnionTester:
    def __init__(self):
        self.working_urls = []
        self.failed_urls = []
        
    def test_single_onion(self, url, timeout=90):
        """Test a single onion URL with extended timeout"""
        print(f"🔍 Testing: {url}")
        
        try:
            start_time = time.time()
            
            response = requests.get(
                url,
                proxies={'http': 'http://127.0.0.1:8118', 'https': 'http://127.0.0.1:8118'},
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                allow_redirects=True
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS! ({elapsed:.1f}s) - {len(response.content)} bytes")
                return url, True, elapsed, response.status_code, len(response.content)
            else:
                print(f"  ⚠️ Response: {response.status_code} ({elapsed:.1f}s)")
                return url, False, elapsed, response.status_code, 0
                
        except requests.exceptions.Timeout:
            print(f"  ❌ TIMEOUT after {timeout}s")
            return url, False, timeout, 'TIMEOUT', 0
        except requests.exceptions.ConnectionError as e:
            print(f"  ❌ Connection Error: {str(e)[:100]}...")
            return url, False, 0, 'CONNECTION_ERROR', 0
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}...")
            return url, False, 0, 'ERROR', 0
    
    def test_multiple_onions(self):
        """Test multiple onion services to find working ones"""
        
        # Reliable onion services (updated list)
        test_urls = [
            # DuckDuckGo (usually most reliable)
            'http://3g2upl4pq6kufc4m.onion',
            'http://duckduckgogg42ts72.onion',
            
            # Facebook (sometimes slow but reliable)
            'http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion',
            
            # Archive.today
            'http://archiveiya74codqgiixo33q62qlrqtkgmcitqx5u2oeqnmn5bpcbiyd.onion',
            
            # Tor Project
            'http://expyuzz4wqqyqhjn.onion',
            
            # Hacker News
            'http://hckrnews4k2j5uud.onion',
        ]
        
        print("🕷️ Testing Multiple Onion Services")
        print("=" * 50)
        print(f"Testing {len(test_urls)} onion services...")
        print("This may take several minutes due to network latency.\n")
        
        results = []
        
        # Test each URL sequentially to avoid overloading Tor
        for url in test_urls:
            result = self.test_single_onion(url, timeout=120)  # 2 minute timeout
            results.append(result)
            
            # Brief pause between tests
            time.sleep(2)
        
        # Process results
        working = [r for r in results if r[1]]
        failed = [r for r in results if not r[1]]
        
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)
        
        if working:
            print(f"✅ WORKING ONION SERVICES ({len(working)}):")
            for url, success, elapsed, status, size in working:
                print(f"  🟢 {url}")
                print(f"     Status: {status} | Time: {elapsed:.1f}s | Size: {size} bytes")
            
            # Save working URLs
            with open('verified_onion_urls.txt', 'w') as f:
                f.write("# Verified Working Onion URLs\n")
                f.write(f"# Tested on {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for url, _, elapsed, status, _ in working:
                    f.write(f"{url}  # Status: {status}, Time: {elapsed:.1f}s\n")
            
            print(f"\n💾 Saved working URLs to: verified_onion_urls.txt")
            
        else:
            print("❌ NO WORKING ONION SERVICES FOUND")
            print("This indicates a network connectivity issue.")
        
        if failed:
            print(f"\n⚠️ FAILED/TIMEOUT SERVICES ({len(failed)}):")
            for url, success, elapsed, status, size in failed[:3]:  # Show first 3
                print(f"  🔴 {url} - {status}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if working:
            best_url = min(working, key=lambda x: x[2])  # Fastest response
            print(f"🚀 Use this URL for testing your crawler:")
            print(f"   {best_url[0]}")
            print(f"   (Responds in {best_url[2]:.1f} seconds)")
            
            print(f"\n🔧 Crawler Settings:")
            print(f"   - URL: {best_url[0]}")
            print(f"   - Proxy: http://127.0.0.1:8118")
            print(f"   - Timeout: {int(best_url[2] * 1.5) + 30} seconds")
            print(f"   - Retry attempts: 3-5")
            
        else:
            print("🔧 Troubleshooting steps:")
            print("   1. Check if your ISP blocks Tor completely")
            print("   2. Try using a VPN + Tor combination")
            print("   3. Configure Tor bridges (obfs4)")
            print("   4. Test from a different network")
            
        return working, failed

def main():
    tester = OnionTester()
    working, failed = tester.test_multiple_onions()
    
    if working:
        print(f"\n🎉 Found {len(working)} working onion service(s)!")
        print("Your crawler should work with the recommended settings above.")
    else:
        print(f"\n⚠️ No working onion services found.")
        print("This suggests network-level restrictions on Tor traffic.")

if __name__ == "__main__":
    main()
