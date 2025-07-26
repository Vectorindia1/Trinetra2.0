#!/usr/bin/env python3

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys
import os
import subprocess
import psutil
import time

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.spiders.robust_tor_crawler import RobustOnionCrawler

def check_tor_services():
    """Check if Tor and Privoxy services are running"""
    print("🔍 Checking Tor and Privoxy services...")
    
    tor_running = False
    privoxy_running = False
    
    # Check for Tor process
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'tor' in proc.info['name'].lower():
                tor_running = True
                print(f"✅ Tor process found: PID {proc.info['pid']}")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Check for Privoxy process
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'privoxy' in proc.info['name'].lower():
                privoxy_running = True
                print(f"✅ Privoxy process found: PID {proc.info['pid']}")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not tor_running:
        print("⚠️ Tor not detected. Starting Tor service...")
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'tor'], check=True)
            time.sleep(5)
            print("✅ Tor service started")
        except subprocess.CalledProcessError:
            print("❌ Failed to start Tor service")
            return False
    
    if not privoxy_running:
        print("⚠️ Privoxy not detected. Starting Privoxy service...")
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'privoxy'], check=True)
            time.sleep(3)
            print("✅ Privoxy service started")
        except subprocess.CalledProcessError:
            print("❌ Failed to start Privoxy service")
            return False
    
    return True

def test_proxy_connections():
    """Test proxy connections"""
    print("\n🌐 Testing proxy connections...")
    
    import requests
    
    proxies_to_test = [
        "http://127.0.0.1:8118",
        "socks5://127.0.0.1:9050"
    ]
    
    for proxy in proxies_to_test:
        try:
            if proxy.startswith('socks5'):
                # For SOCKS5, we need different handling
                proxies = {'http': proxy, 'https': proxy}
            else:
                proxies = {'http': proxy, 'https': proxy}
            
            response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=15)
            if response.status_code == 200:
                print(f"✅ {proxy} - Working (IP: {response.json().get('origin', 'unknown')})")
            else:
                print(f"❌ {proxy} - Failed (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ {proxy} - Error: {e}")

def test_robust_onion_crawler():
    """Test the enhanced robust crawler with .onion domains"""
    
    # Test URLs (some may be down, that's expected)
    test_urls = [
        "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion",
        "http://3g2upl4pq6kufc4m.onion",  # DuckDuckGo alternative
        "http://httpbin.org/ip",  # Regular site for comparison
    ]
    
    print("🚀 Testing Enhanced Robust Onion Crawler")
    print("=" * 60)
    
    # Check prerequisites
    if not check_tor_services():
        print("❌ Required services not available. Exiting.")
        return
    
    # Test proxy connections
    test_proxy_connections()
    
    # Configure enhanced settings for robustness
    settings = get_project_settings()
    settings.update({
        'LOG_LEVEL': 'INFO',
        'CLOSESPIDER_TIMEOUT': 60,  # Stop after 1 minute
        'CLOSESPIDER_PAGECOUNT': 10,  # Stop after 10 pages
        'CONCURRENT_REQUESTS': 4,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.8,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 8,
        'DOWNLOAD_TIMEOUT': 60,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 15,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'PROXY_ROTATION_ENABLED': True,
        'USER_AGENT_ROTATION_ENABLED': True,
        'HTTPERROR_ALLOWED_CODES': [403, 404, 429, 500, 502, 503, 504],
    })
    
    for url in test_urls:
        print(f"\\n🔍 Testing: {url}")
        print("-" * 50)
        
        # Create crawler process
        process = CrawlerProcess(settings)
        
        try:
            # Start the crawler
            print(f"🚀 Starting robust crawler for {url}...")
            process.crawl(RobustOnionCrawler, start_url=url)
            process.start()
            
            print(f"✅ Robust crawler completed for {url}")
            
        except Exception as e:
            print(f"❌ Error crawling {url}: {e}")
        
        # Allow reactor to reset
        time.sleep(2)

def run_captcha_test():
    """Test CAPTCHA detection and handling capabilities"""
    print("\\n🧩 Testing CAPTCHA Detection...")
    
    # Test CAPTCHA detection patterns
    test_content = """
    <html>
        <div class="cf-browser-verification">
            <div class="cf-challenge-running">Checking your browser before accessing</div>
        </div>
        <div class="g-recaptcha" data-sitekey="6LfW0QMTAAAAAEriKE8KiXFxPpMDKg0vXE9L_VWk"></div>
    </html>
    """
    
    from crawler.spiders.robust_tor_crawler import BLOCKING_PATTERNS
    
    blocking_detected = any(re.search(pattern, test_content.lower(), re.IGNORECASE) 
                          for pattern in BLOCKING_PATTERNS)
    
    if blocking_detected:
        print("✅ CAPTCHA/blocking patterns detected successfully")
    else:
        print("❌ CAPTCHA/blocking detection failed")
    
    # Test reCAPTCHA site key extraction
    import re
    site_key_match = re.search(r'data-sitekey="([^"]+)"', test_content)
    if site_key_match:
        print(f"✅ Site key extracted: {site_key_match.group(1)}")
    else:
        print("❌ Site key extraction failed")

def display_crawler_features():
    """Display the enhanced features of the robust crawler"""
    print("\\n🛡️ Enhanced Robust Crawler Features:")
    print("=" * 50)
    print("✅ Advanced User-Agent Rotation (12+ agents)")
    print("✅ Enhanced Proxy Rotation with Fallbacks")
    print("✅ CAPTCHA Detection & 2Captcha Integration")
    print("✅ Cloudflare Challenge Handling via Selenium")
    print("✅ Comprehensive Blocking Pattern Detection")
    print("✅ Enhanced Suspicious Content Analysis")
    print("✅ Cryptocurrency Address Extraction")
    print("✅ Advanced Error Handling & Recovery")
    print("✅ Domain Blocking After Multiple Failures")
    print("✅ Enhanced Link Validation & Filtering")
    print("✅ Selenium WebDriver Integration")
    print("✅ Session Management & Cookie Persistence")
    print("✅ Exponential Backoff for Rate Limiting")
    print("✅ Enhanced Geolocation with Caching")
    print("✅ Improved Metadata Extraction")

if __name__ == "__main__":
    print("🧪 Enhanced Robust Tor Crawler Test Suite")
    print("=" * 60)
    
    # Display features
    display_crawler_features()
    
    # Run CAPTCHA test
    run_captcha_test()
    
    # Main crawler test
    test_robust_onion_crawler()
    
    print("\\n🎉 Test suite completed!")
    print("Check logs and failed_links.txt for detailed results.")
