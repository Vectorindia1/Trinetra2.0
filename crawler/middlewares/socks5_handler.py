import random
import time
import re
import logging
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.http import Request
from twisted.internet.error import DNSLookupError, ConnectionRefusedError, TimeoutError

# Proxy configurations for Tor (only available ports)
TOR_PROXIES = [
    "http://127.0.0.1:8118",   # Privoxy HTTP proxy for Tor - supports both HTTP and HTTPS
]

# SOCKS5 proxy only for HTTP .onion sites (not HTTPS)
TOR_SOCKS5_PROXY = "socks5://127.0.0.1:9050"

# Backup clearnet proxies if needed
CLEARNET_PROXIES = [
    "http://127.0.0.1:8118",
]

# Enhanced User Agents for better bypassing
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36"
]

# Common blocking patterns to detect and handle
BLOCKING_PATTERNS = [
    r'cloudflare',
    r'ddos.*protection',
    r'access.*denied',
    r'blocked.*request',
    r'rate.*limit',
    r'captcha',
    r'security.*check',
    r'please.*wait',
    r'suspicious.*activity'
]

# Patterns to ignore (these are not blocking patterns but technical errors)
IGNORE_PATTERNS = [
    r'socks5.*request.*failed',
    r'forwarding.*failure',
    r'tor.*is.*not.*an.*http.*proxy',
    r'privoxy.*unable.*to.*socks5t-forward'
]

class EnhancedProxyMiddleware(HttpProxyMiddleware):
    def __init__(self, settings):
        super().__init__()
        self.proxy_rotation_enabled = settings.getbool('PROXY_ROTATION_ENABLED', True)
        self.user_agent_rotation_enabled = settings.getbool('USER_AGENT_ROTATION_ENABLED', True)
        self.logger = logging.getLogger(__name__)
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
    
    def _test_proxy_connection(self, proxy_url):
        """Test if proxy is working"""
        try:
            import requests
            proxies = {'http': proxy_url, 'https': proxy_url}
            response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Proxy test failed for {proxy_url}: {e}")
            return False
        
    def process_request(self, request, spider):
        # Skip if proxy is already set
        if 'proxy' in request.meta:
            return None
            
        # 🔥 Enhanced proxy logic with proper HTTPS support
        if ".onion" in request.url:
            # Use HTTP proxy through Privoxy for both HTTP and HTTPS .onion traffic
            proxy_url = "http://127.0.0.1:8118"
            
            # Privoxy can handle both HTTP and HTTPS through Tor
            request.meta['proxy'] = proxy_url
            request.meta['download_timeout'] = 60
            request.meta['dont_cache'] = True
            
            # Force HTTP version for better compatibility
            if request.url.startswith('https://'):
                spider.logger.debug(f"🔒 Using HTTPS through Privoxy: {proxy_url} for {request.url}")
            else:
                spider.logger.debug(f"🌐 Using HTTP through Privoxy: {proxy_url} for {request.url}")
        else:
            # 🔥 Remove proxy for clearnet/surface web traffic
            request.meta.pop('proxy', None)
            spider.logger.debug(f"🚀 Direct connection (no proxy) for surface web: {request.url}")
        
        # Rotate user agent for each request
        if self.user_agent_rotation_enabled:
            request.headers['User-Agent'] = random.choice(USER_AGENTS)
            
        # Add additional headers for better anonymity
        request.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
            
        return None
        
    def process_response(self, request, response, spider):
        # Only check for blocking patterns in successful responses (status 200)
        if response.status == 200 and hasattr(response, 'text'):
            response_text = response.text.lower()
            
            # Check if this is a technical error that should be ignored
            if any(re.search(pattern, response_text, re.IGNORECASE) for pattern in IGNORE_PATTERNS):
                spider.logger.warning(f"Technical error detected for {request.url} - not retrying")
                return response
                
            # Only retry for actual blocking patterns in successful responses
            if any(re.search(pattern, response_text, re.IGNORECASE) for pattern in BLOCKING_PATTERNS):
                spider.logger.warning(f"Blocking pattern detected for {request.url}, rotating proxy...")
                
                # For .onion domains, always use Privoxy (don't rotate to SOCKS5)
                if ".onion" in request.url:
                    request.meta['proxy'] = "http://127.0.0.1:8118"
                    spider.logger.info(f"Retrying .onion request with Privoxy for {request.url}")
                else:
                    # Rotate proxy for clearnet sites
                    new_proxy = random.choice(TOR_PROXIES)
                    request.meta['proxy'] = new_proxy
                    
                request.headers['User-Agent'] = random.choice(USER_AGENTS)
                
                # Add delay to avoid rate limiting
                time.sleep(random.uniform(2, 5))
                
                # Return the original request to retry
                return request
                
        return response
    
    def process_exception(self, request, exception, spider):
        """Handle proxy-related exceptions"""
        from twisted.internet.error import DNSLookupError, ConnectionRefusedError, TimeoutError
        from scrapy.core.downloader.handlers.http11 import TunnelError
        
        if isinstance(exception, (DNSLookupError, ConnectionRefusedError, TimeoutError, TunnelError)):
            spider.logger.warning(f"Connection error for {request.url}: {exception}")
            
            # For .onion domains, always stick with Privoxy for HTTPS support
            if ".onion" in request.url:
                current_proxy = request.meta.get('proxy', '')
                
                # 🔥 CRITICAL: Never use SOCKS5 for HTTPS .onion requests
                # Always force Privoxy for all .onion domains
                if 'socks5' in current_proxy:
                    spider.logger.error(f"❌ SOCKS5 proxy detected for HTTPS .onion - switching to Privoxy: {request.url}")
                    request.meta['proxy'] = "http://127.0.0.1:8118"
                    request.meta['download_timeout'] = 90
                    spider.logger.info(f"🔄 Forcing Privoxy for HTTPS .onion: {request.url}")
                    return request
                
                # If we're already using Privoxy, don't retry to avoid infinite loops
                if current_proxy == "http://127.0.0.1:8118":
                    spider.logger.error(f"Privoxy connection failed for {request.url}, not retrying")
                    return None
                    
                # Ensure we're using Privoxy for all .onion requests
                request.meta['proxy'] = "http://127.0.0.1:8118"
                request.meta['download_timeout'] = 90  # Increase timeout
                spider.logger.info(f"Retrying with Privoxy proxy for {request.url}")
                return request
                    
        return None
