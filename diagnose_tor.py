#!/usr/bin/env python3

import subprocess
import requests
import socket
import time

def test_tor_bootstrap():
    """Check if Tor has properly bootstrapped"""
    print("🔍 Checking Tor bootstrap status...")
    try:
        result = subprocess.run(['sudo', 'journalctl', '-u', 'tor@default', '-n', '5'], 
                              capture_output=True, text=True)
        if "Bootstrapped 100%" in result.stdout:
            print("   ✅ Tor has bootstrapped successfully")
            return True
        else:
            print("   ❌ Tor has not fully bootstrapped")
            return False
    except Exception as e:
        print(f"   ❌ Error checking bootstrap: {e}")
        return False

def test_tor_port():
    """Test if Tor SOCKS port is listening"""
    print("\\n🔍 Testing Tor SOCKS port 9050...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 9050))
        sock.close()
        
        if result == 0:
            print("   ✅ Port 9050 is listening")
            return True
        else:
            print("   ❌ Port 9050 is not accessible")
            return False
    except Exception as e:
        print(f"   ❌ Error testing port: {e}")
        return False

def test_regular_internet():
    """Test regular internet without proxy"""
    print("\\n🔍 Testing regular internet connection...")
    try:
        response = requests.get('http://httpbin.org/ip', timeout=10)
        if response.status_code == 200:
            data = response.json()
            real_ip = data.get('origin', 'unknown')
            print(f"   ✅ Regular connection works - IP: {real_ip}")
            return True, real_ip
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def test_tor_circuit():
    """Test if Tor can build circuits for regular sites"""
    print("\\n🔍 Testing Tor circuit building...")
    
    proxies = {'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'}
    
    try:
        print("   Attempting to get IP through Tor...")
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            tor_ip = data.get('origin', 'unknown')
            print(f"   ✅ Tor circuits work - Tor IP: {tor_ip}")
            return True, tor_ip
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False, None
            
    except requests.exceptions.ConnectTimeout:
        print("   ❌ Connection timeout - Tor may not be building circuits")
        return False, None
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        return False, None

def diagnose_onion_issue():
    """Diagnose why onion services aren't working"""
    print("\\n🔍 Diagnosing onion service issues...")
    
    # Check Tor logs for specific errors
    try:
        result = subprocess.run(['sudo', 'journalctl', '-u', 'tor@default', '--since', '5 minutes ago'], 
                              capture_output=True, text=True)
        
        logs = result.stdout.lower()
        
        issues = []
        if "invalid hostname" in logs:
            issues.append("Invalid hostname errors (DNS resolution issues)")
        if "waiting for circuit" in logs:
            issues.append("Circuit building problems")
        if "waiting for rendezvous desc" in logs:
            issues.append("Hidden service descriptor issues")
        if "openssl" in logs and "error" in logs:
            issues.append("OpenSSL/TLS errors")
        
        if issues:
            print("   ⚠️ Found these issues:")
            for issue in issues:
                print(f"     - {issue}")
        else:
            print("   🤔 No obvious errors in recent logs")
            
    except Exception as e:
        print(f"   ❌ Could not analyze logs: {e}")

def main():
    print("🕷️ TOR CONNECTIVITY DIAGNOSIS")
    print("=" * 50)
    
    # Step 1: Check Tor service
    bootstrap_ok = test_tor_bootstrap()
    
    # Step 2: Check SOCKS port
    port_ok = test_tor_port()
    
    # Step 3: Test regular internet
    internet_ok, real_ip = test_regular_internet()
    
    # Step 4: Test Tor circuits
    tor_ok, tor_ip = test_tor_circuit()
    
    # Step 5: Diagnose onion issues
    diagnose_onion_issue()
    
    print("\\n" + "=" * 50)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    if not bootstrap_ok:
        print("❌ PRIMARY ISSUE: Tor service not bootstrapped properly")
        print("   SOLUTION: Restart Tor, check configuration")
    elif not port_ok:
        print("❌ PRIMARY ISSUE: Tor SOCKS port not accessible")
        print("   SOLUTION: Check Tor configuration, restart service")
    elif not internet_ok:
        print("❌ PRIMARY ISSUE: No internet connectivity")
        print("   SOLUTION: Check network connection")
    elif not tor_ok:
        print("❌ PRIMARY ISSUE: Tor cannot build circuits")
        print("   POSSIBLE CAUSES:")
        print("   - ISP blocks Tor traffic")
        print("   - Firewall blocking Tor")
        print("   - Need to use bridges")
        print("   SOLUTION: Try configuring Tor bridges")
    else:
        print("⚠️ ISSUE: Basic Tor works, but onion services don't")
        print("   This suggests:")
        print("   - Hidden service issues")
        print("   - V2 onion deprecation")
        print("   - Network filtering of .onion traffic")
        
        print("\\n🔧 RECOMMENDED ACTIONS:")
        print("   1. Try newer V3 onion addresses")
        print("   2. Use Tor bridges")
        print("   3. Test from different network")
        
    if tor_ok and real_ip and tor_ip:
        print(f"\\n✅ WORKING CONFIGURATION:")
        print(f"   Real IP: {real_ip}")
        print(f"   Tor IP:  {tor_ip}")
        print(f"   Proxy:   socks5h://127.0.0.1:9050")

if __name__ == "__main__":
    main()
