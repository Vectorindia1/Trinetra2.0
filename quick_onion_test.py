#!/usr/bin/env python3
"""
Quick test for specific onion connectivity
"""
import requests
import time

def test_facebook_onion():
    """Test Facebook onion service specifically"""
    print("🔗 Testing Facebook onion service...")
    
    url = "http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion"
    
    # Test via Privoxy
    try:
        print("  📡 Testing via Privoxy (HTTP proxy)...")
        response = requests.get(
            url,
            proxies={'http': 'http://127.0.0.1:8118'},
            timeout=45,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        if response.status_code == 200:
            print(f"  ✅ SUCCESS! Facebook onion is accessible")
            print(f"     Status: {response.status_code}")
            print(f"     Title found: {'facebook' in response.text.lower()}")
            return True
        else:
            print(f"  ⚠️ Got response but with status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  ❌ Connection timed out after 45 seconds")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    print("🧪 Quick Onion Connectivity Test")
    print("=" * 40)
    
    if test_facebook_onion():
        print("\n🎉 SUCCESS: .onion connectivity is working!")
        print("💡 You can now use this URL in your crawler:")
        print("   http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion")
        print("\n🔧 For your crawler, use these settings:")
        print("   - Proxy: http://127.0.0.1:8118")
        print("   - Timeout: 60+ seconds")
        print("   - User-Agent: Standard browser UA")
    else:
        print("\n❌ .onion connectivity still not working")
        print("🔧 This could be due to:")
        print("   - ISP blocking Tor traffic")
        print("   - Network firewall restrictions") 
        print("   - Tor network congestion")
        print("   - Need for Tor bridges")
