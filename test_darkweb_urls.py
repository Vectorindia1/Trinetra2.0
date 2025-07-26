#!/usr/bin/env python3
"""
Professional Dark Web URL Validator and Connection Tester
Handles common issues in dark web crawling like professionals do
"""

import re
import requests
import time
import random
from urllib.parse import urlparse, urljoin
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DarkWebURLValidator:
    """Professional URL validation for dark web crawling"""
    
    # Valid onion domain patterns (v2 and v3)
    ONION_V2_PATTERN = r'^https?://[a-z2-7]{16}\.onion(/.*)?$'
    ONION_V3_PATTERN = r'^https?://[a-z2-7]{56}\.onion(/.*)?$'
    
    # Professional user agents used by researchers
    PROFESSIONAL_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    # Known working onion test URLs (updated regularly by researchers)
    TEST_URLS = [
        'http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion',  # Facebook
        'http://duckduckgogg42ts72.onion',  # DuckDuckGo (v2)
        'http://3g2upl4pq6kufc4m.onion',    # DuckDuckGo alternative
        'http://zbdshzyky2g6j67b.onion'     # News site
    ]
    
    def __init__(self):
        self.session = self._create_session()
    
    def _create_session(self):
        """Create a robust session with proper retry configuration"""
        session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configure session
        session.headers.update({
            'User-Agent': random.choice(self.PROFESSIONAL_USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Set proxy for Tor
        session.proxies = {
            'http': 'http://127.0.0.1:8118',
            'https': 'http://127.0.0.1:8118'
        }
        
        return session
    
    def validate_url_format(self, url):
        """Validate URL format and structure"""
        if not url or not isinstance(url, str):
            return False, "URL must be a non-empty string"
        
        # Clean the URL
        url = url.strip()
        
        # Check for basic URL structure
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        # Check for .onion domain
        if '.onion' not in url:
            return False, "URL must contain .onion domain"
        
        # Validate onion format (v2 or v3)
        if not (re.match(self.ONION_V2_PATTERN, url, re.IGNORECASE) or 
                re.match(self.ONION_V3_PATTERN, url, re.IGNORECASE)):
            return False, "Invalid onion URL format (must be v2: 16 chars or v3: 56 chars)"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'[^a-z2-7\.]',  # Invalid characters in domain
            r'\.onion\.[^/]', # Domain after .onion
            r'//.*//|///+'    # Multiple slashes
        ]
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, domain):
                return False, f"Suspicious pattern detected in domain: {domain}"
        
        return True, "URL format is valid"
    
    def test_connectivity(self, url, timeout=30):
        """Test if URL is accessible"""
        try:
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            return True, response.status_code, f"Connection successful (HTTP {response.status_code})"
        except requests.exceptions.ConnectionError as e:
            return False, None, f"Connection failed: {str(e)}"
        except requests.exceptions.Timeout:
            return False, None, "Connection timed out"
        except requests.exceptions.RequestException as e:
            return False, None, f"Request failed: {str(e)}"
    
    def advanced_url_test(self, url):
        """Comprehensive URL testing"""
        results = {
            'url': url,
            'format_valid': False,
            'accessible': False,
            'status_code': None,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Format validation
        is_valid, message = self.validate_url_format(url)
        results['format_valid'] = is_valid
        if not is_valid:
            results['errors'].append(message)
            return results
        
        # Connectivity test
        accessible, status_code, conn_message = self.test_connectivity(url)
        results['accessible'] = accessible
        results['status_code'] = status_code
        
        if accessible:
            results['warnings'].append(conn_message)
            results['recommendations'].append("URL appears to be accessible")
        else:
            results['errors'].append(conn_message)
            
            # Add specific recommendations based on error
            if "timed out" in conn_message.lower():
                results['recommendations'].extend([
                    "Try increasing timeout duration",
                    "Check if Tor service is running properly",
                    "Verify Privoxy is configured correctly"
                ])
            elif "connection failed" in conn_message.lower():
                results['recommendations'].extend([
                    "Verify Tor proxy is running on 127.0.0.1:9050",
                    "Check Privoxy is running on 127.0.0.1:8118",
                    "Try using SOCKS5 proxy directly"
                ])
        
        return results

def test_tor_setup():
    """Test if Tor and Privoxy are properly configured"""
    logger.info("🔧 Testing Tor and Privoxy setup...")
    
    # Test Privoxy connection
    try:
        response = requests.get(
            'http://httpbin.org/ip',
            proxies={'http': 'http://127.0.0.1:8118'},
            timeout=10
        )
        logger.info(f"✅ Privoxy working. Your IP: {response.json().get('origin')}")
        return True
    except Exception as e:
        logger.error(f"❌ Privoxy test failed: {e}")
        return False

def get_recommended_test_urls():
    """Get current working test URLs for dark web"""
    return [
        # Facebook - usually reliable
        'http://facebookwkhpilnemxj7asaniu7vnjjbiltxjqhye3mhbshg7kx5tfyd.onion',
        # DuckDuckGo - search engine
        'http://duckduckgogg42ts72.onion',
        # ProPublica - news site
        'http://p53lf57qovyuvwsc6xnrppddxpr23otqjbrqzqacgmjltgqnlq6g2xid.onion',
    ]

def main():
    """Main testing function"""
    print("🕵️ Professional Dark Web URL Validator & Tester")
    print("=" * 60)
    
    # Initialize validator
    validator = DarkWebURLValidator()
    
    # Test system setup
    print("\n🔧 Testing system setup...")
    if not test_tor_setup():
        print("❌ System setup issues detected. Please fix Tor/Privoxy configuration.")
        return
    
    # Test recommended URLs
    print("\n🌐 Testing known working URLs...")
    test_urls = get_recommended_test_urls()
    
    for url in test_urls:
        print(f"\n🔍 Testing: {url}")
        results = validator.advanced_url_test(url)
        
        print(f"  Format Valid: {'✅' if results['format_valid'] else '❌'}")
        print(f"  Accessible: {'✅' if results['accessible'] else '❌'}")
        if results['status_code']:
            print(f"  Status Code: {results['status_code']}")
        
        if results['errors']:
            print("  ❌ Errors:")
            for error in results['errors']:
                print(f"    - {error}")
        
        if results['warnings']:
            print("  ⚠️ Info:")
            for warning in results['warnings']:
                print(f"    - {warning}")
        
        if results['recommendations']:
            print("  💡 Recommendations:")
            for rec in results['recommendations']:
                print(f"    - {rec}")
    
    # Interactive testing
    print("\n" + "=" * 60)
    print("🧪 Interactive URL Testing")
    print("Enter URLs to test (or 'quit' to exit):")
    
    while True:
        url_input = input("\n🔗 Enter URL: ").strip()
        
        if url_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if not url_input:
            continue
        
        print(f"🔍 Testing: {url_input}")
        results = validator.advanced_url_test(url_input)
        
        print(f"  Format Valid: {'✅' if results['format_valid'] else '❌'}")
        print(f"  Accessible: {'✅' if results['accessible'] else '❌'}")
        if results['status_code']:
            print(f"  Status Code: {results['status_code']}")
        
        if results['errors']:
            print("  ❌ Errors:")
            for error in results['errors']:
                print(f"    - {error}")
        
        if results['recommendations']:
            print("  💡 Recommendations:")
            for rec in results['recommendations']:
                print(f"    - {rec}")

if __name__ == "__main__":
    main()
