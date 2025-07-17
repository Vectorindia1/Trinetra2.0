#!/usr/bin/env python3

import requests
import socks
import socket
import time

def test_socks5_proxy():
    """Test SOCKS5 proxy connectivity"""
    
    # Test direct connection first
    print("🔍 Testing direct connection...")
    try:
        response = requests.get("http://httpbin.org/ip", timeout=10)
        print(f"✅ Direct connection successful: {response.json()}")
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
    
    # Test HTTP proxy
    print("\n🔍 Testing HTTP proxy (8118)...")
    try:
        proxies = {
            'http': 'http://127.0.0.1:8118',
            'https': 'http://127.0.0.1:8118'
        }
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=15)
        print(f"✅ HTTP proxy successful: {response.json()}")
    except Exception as e:
        print(f"❌ HTTP proxy failed: {e}")
    
    # Test SOCKS5 proxy using requests-socks
    print("\n🔍 Testing SOCKS5 proxy (9050)...")
    try:
        import requests
        session = requests.Session()
        session.proxies = {
            'http': 'socks5://127.0.0.1:9050',
            'https': 'socks5://127.0.0.1:9050'
        }
        response = session.get("http://httpbin.org/ip", timeout=15)
        print(f"✅ SOCKS5 proxy successful: {response.json()}")
    except Exception as e:
        print(f"❌ SOCKS5 proxy failed: {e}")
    
    # Test with raw socket
    print("\n🔍 Testing raw SOCKS5 socket...")
    try:
        # Create a socket and connect through SOCKS5
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        sock.connect(("httpbin.org", 80))
        sock.send(b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n")
        response = sock.recv(1024).decode()
        print(f"✅ Raw SOCKS5 socket successful: {response[:200]}...")
        sock.close()
    except Exception as e:
        print(f"❌ Raw SOCKS5 socket failed: {e}")

if __name__ == "__main__":
    test_socks5_proxy()
