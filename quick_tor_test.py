#!/usr/bin/env python3

import requests
import time

def test_proxy():
    """Test if Tor+Privoxy proxy chain is working"""
    
    # Test proxy configuration
    proxies = {
        'http': 'http://127.0.0.1:8118',
        'https': 'http://127.0.0.1:8118'
    }
    
    print("🔍 Testing Tor connection via Privoxy proxy...")
    
    try:
        # Test 1: Get our Tor IP
        print("1. Checking Tor IP...")
        response = requests.get(
            'http://httpbin.org/ip',
            proxies=proxies,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            tor_ip = data.get('origin', 'unknown')
            print(f"   ✅ Tor IP: {tor_ip}")
        else:
            print(f"   ❌ Failed to get Tor IP: {response.status_code}")
            return False
            
        # Test 2: Test a known working onion service
        print("2. Testing Facebook's onion service...")
        test_url = "http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion"
        
        response = requests.get(
            test_url,
            proxies=proxies,
            timeout=30,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Successfully connected to {test_url}")
            print(f"   Response length: {len(response.text)} bytes")
            return True
        else:
            print(f"   ⚠️ Got response {response.status_code} from {test_url}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_proxy()
    if success:
        print("\n🎉 Proxy chain is working! Ready for onion crawling.")
    else:
        print("\n❌ Proxy chain issues detected. Check Tor and Privoxy configuration.")
