import scrapy
import json
import os
import re
import hashlib
import concurrent.futures
import random
import time
import requests
import asyncio
import websockets
import base64
from datetime import datetime
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
from telegram_alert import send_telegram_alert
from database.models import db_manager, Alert, CrawledPage
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import get_base_url
from scrapy.http import Request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import real-time notifications
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from realtime_notifier import (
        notify_page_scraped, 
        notify_alert_created, 
        notify_ai_analysis_complete, 
        notify_links_discovered
    )
    REALTIME_ENABLED = True
except ImportError as e:
    print(f"⚠️ Real-time notifications not available: {e}")
    REALTIME_ENABLED = False

# Import AI analysis
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from ai.gemini_analyzer import analyze_with_ai_sync, gemini_analyzer
    AI_ENABLED = True
except ImportError as e:
    print(f"⚠️ AI module not available: {e}")
    AI_ENABLED = False

# Import geolocation service
try:
    from geolocation_service import GeolocationService
    geo_service = GeolocationService(api_key="your_ipstack_api_key")
    GEO_ENABLED = True
except ImportError as e:
    print(f"⚠️ Geolocation service not available: {e}")
    GEO_ENABLED = False

# Load keywords
with open("keyword.json") as f:
    KEYWORDS = set(json.load(f).get("india_keywords", []))

# Configs
TELEGRAM_BOT_TOKEN = "7764356588:AAFyfqTvVrZ8_MG6B45JuVL1EC-iFZ_4oc4"
TELEGRAM_CHAT_ID = "5188590599"

# Comprehensive User Agents for better bypassing
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 12; Mobile; rv:68.0) Gecko/68.0 Firefox/88.0"
]

# Enhanced proxy rotation with multiple fallbacks
TOR_PROXIES = [
    "http://127.0.0.1:8118",
    "socks5://127.0.0.1:9050",
    "http://127.0.0.1:8119",
    "socks5://127.0.0.1:9051",
    "http://127.0.0.1:8120",
    "socks5://127.0.0.1:9052"
]

# Enhanced blocking patterns with more comprehensive detection
BLOCKING_PATTERNS = [
    r'cloudflare',
    r'ddos.*protection',
    r'access.*denied',
    r'blocked.*request',
    r'rate.*limit',
    r'captcha',
    r'security.*check',
    r'please.*wait',
    r'suspicious.*activity',
    r'robot.*check',
    r'human.*verification',
    r'challenge.*solve',
    r'prove.*not.*robot',
    r'blocked.*by.*firewall',
    r'too.*many.*requests',
    r'service.*temporarily.*unavailable',
    r'recaptcha',
    r'hcaptcha',
    r'turnstile'
]

# CAPTCHA service configurations (replace with your API keys)
CAPTCHA_SERVICES = {
    '2captcha': {'api_key': 'your_2captcha_api_key'},
    'anticaptcha': {'api_key': 'your_anticaptcha_api_key'},
    'deathbycaptcha': {'username': 'your_username', 'password': 'your_password'}
}

crawled_pages = 0
non_http_links = []
chatroom_links = []
visited_links = set(link['url'] for link in db_manager.get_crawled_pages(limit=1000000))
failed_requests = {}
session_cookies = {}

# Progress bar
progress_bar = tqdm(total=1000000, desc="🌐 Crawling Progress", unit="page")

chatroom_patterns = [
    r'(irc|xmpp|webchat|discord|telegram|signal|chatroom|channel)\.(.*)'
]

class RobustOnionCrawler(scrapy.Spider):
    name = "robust_onion"
    custom_settings = {
        "USER_AGENT": random.choice(USER_AGENTS),
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8,fr;q=0.7,de;q=0.6",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "DNT": "1",
            "Sec-GPC": "1"
        },
        "DOWNLOAD_DELAY": random.uniform(3, 8),
        "RANDOMIZE_DOWNLOAD_DELAY": 0.8,
        "RETRY_TIMES": 12,
        "DOWNLOAD_TIMEOUT": 90,
        "COOKIES_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "HTTPERROR_ALLOWED_CODES": [403, 404, 429, 500, 502, 503, 504, 521, 522, 523, 524],
        "HANDLE_HTTPSTATUS_ALL": True,
        "CONCURRENT_REQUESTS": 8,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 2,
        "AUTOTHROTTLE_MAX_DELAY": 20,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'crawler.middlewares.socks5_handler.EnhancedProxyMiddleware': 100,
        },
        "PROXY_ROTATION_ENABLED": True,
        "USER_AGENT_ROTATION_ENABLED": True,
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super(RobustOnionCrawler, self).__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("⚠ Please provide a start_url using -a start_url=<url>")
        self.start_url = start_url
        self.session = requests.Session()
        self.tor_circuit_refresh_counter = 0
        self.captcha_solve_attempts = {}
        self.selenium_driver = None
        self.blocked_domains = set()
        
    def _init_selenium_driver(self):
        """Initialize Selenium WebDriver for JavaScript and CAPTCHA handling"""
        if self.selenium_driver:
            return self.selenium_driver
            
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')
            chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:9050')
            
            self.selenium_driver = webdriver.Chrome(options=chrome_options)
            self.selenium_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return self.selenium_driver
        except Exception as e:
            self.logger.error(f"Failed to initialize Selenium driver: {e}")
            return None

    def _solve_2captcha(self, site_key, page_url):
        """Solve reCAPTCHA using 2Captcha service"""
        try:
            import requests
            
            api_key = CAPTCHA_SERVICES['2captcha']['api_key']
            if api_key == 'your_2captcha_api_key':
                return None
                
            # Submit CAPTCHA
            submit_url = "http://2captcha.com/in.php"
            submit_data = {
                'key': api_key,
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url,
                'json': 1
            }
            
            response = requests.post(submit_url, data=submit_data, timeout=30)
            result = response.json()
            
            if result['status'] != 1:
                self.logger.error(f"2Captcha submission failed: {result}")
                return None
                
            captcha_id = result['request']
            self.logger.info(f"CAPTCHA submitted to 2Captcha, ID: {captcha_id}")
            
            # Wait and retrieve solution
            retrieve_url = "http://2captcha.com/res.php"
            for attempt in range(30):  # Wait up to 5 minutes
                time.sleep(10)
                
                retrieve_params = {
                    'key': api_key,
                    'action': 'get',
                    'id': captcha_id,
                    'json': 1
                }
                
                response = requests.get(retrieve_url, params=retrieve_params, timeout=30)
                result = response.json()
                
                if result['status'] == 1:
                    self.logger.info("CAPTCHA solved successfully!")
                    return result['request']
                elif result['error_text'] != 'CAPCHA_NOT_READY':
                    self.logger.error(f"2Captcha error: {result}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"2Captcha solving failed: {e}")
            return None

    def _handle_cloudflare_challenge(self, response):
        """Handle Cloudflare challenges using Selenium"""
        try:
            driver = self._init_selenium_driver()
            if not driver:
                return None
                
            self.logger.info(f"Handling Cloudflare challenge for {response.url}")
            driver.get(response.url)
            
            # Wait for challenge to complete (up to 30 seconds)
            WebDriverWait(driver, 30).until(
                lambda d: "Checking your browser" not in d.page_source
            )
            
            # Get the page content after challenge
            time.sleep(5)  # Additional wait
            return driver.page_source
            
        except Exception as e:
            self.logger.error(f"Cloudflare challenge handling failed: {e}")
            return None

    def _detect_blocking_type(self, response):
        """Detect the type of blocking mechanism"""
        content = response.text.lower()
        
        if 'cloudflare' in content:
            return 'cloudflare'
        elif any(pattern in content for pattern in ['recaptcha', 'captcha']):
            return 'captcha'
        elif 'rate limit' in content or 'too many requests' in content:
            return 'rate_limit'
        elif 'access denied' in content or 'blocked' in content:
            return 'access_denied'
        else:
            return 'unknown'

    def _handle_blocking(self, response):
        """Comprehensive blocking handler"""
        blocking_type = self._detect_blocking_type(response)
        url = response.url
        
        self.logger.warning(f"Blocking detected ({blocking_type}) for {url}")
        
        if blocking_type == 'cloudflare':
            # Try Selenium for Cloudflare
            new_content = self._handle_cloudflare_challenge(response)
            if new_content:
                # Create new response object with solved content
                return scrapy.http.HtmlResponse(
                    url=url,
                    body=new_content.encode('utf-8'),
                    encoding='utf-8'
                )
                
        elif blocking_type == 'captcha':
            # Try CAPTCHA solving
            if url not in self.captcha_solve_attempts:
                self.captcha_solve_attempts[url] = 0
                
            if self.captcha_solve_attempts[url] < 3:
                self.captcha_solve_attempts[url] += 1
                
                # Extract site key for reCAPTCHA
                site_key_match = re.search(r'data-sitekey="([^"]+)"', response.text)
                if site_key_match:
                    site_key = site_key_match.group(1)
                    solution = self._solve_2captcha(site_key, url)
                    if solution:
                        # Submit CAPTCHA solution (implementation depends on site)
                        pass
                        
        elif blocking_type == 'rate_limit':
            # Implement exponential backoff
            domain = urlparse(url).netloc
            wait_time = min(300, 10 * (2 ** self.failed_requests.get(domain, 0)))
            self.logger.info(f"Rate limited, waiting {wait_time} seconds")
            time.sleep(wait_time)
            
        return None

    def start_requests(self):
        """Enhanced start requests with better error handling"""
        yield scrapy.Request(
            url=self.start_url,
            callback=self.parse,
            errback=self.errback_handler,
            dont_filter=True,
            meta={
                'download_timeout': 90,
                'retry_times': 12
            }
        )

    def parse(self, response):
        global crawled_pages

        # Check for blocking patterns first
        if any(re.search(pattern, response.text, re.IGNORECASE) for pattern in BLOCKING_PATTERNS):
            handled_response = self._handle_blocking(response)
            if handled_response:
                response = handled_response
            else:
                self.logger.warning(f"Could not bypass blocking for {response.url}")
                return

        # Extract chatroom links
        detected_chatroom_links = set()
        for link in response.css("a::attr(href)").getall():
            if any(re.search(pattern, link.lower()) for pattern in chatroom_patterns):
                detected_chatroom_links.add(link)

        if detected_chatroom_links:
            self.logger.info(f"🗨️ Chatroom links detected: {detected_chatroom_links}")
            for chatroom_url in detected_chatroom_links:
                chatroom_links.append({
                    'source_url': response.url,
                    'chatroom_url': chatroom_url,
                    'chatroom_type': 'detected'
                })

        # Extract emails and IPs with enhanced patterns
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text)
        ips = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', response.text)
        
        # Extract cryptocurrency addresses
        btc_addresses = re.findall(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', response.text)
        eth_addresses = re.findall(r'\b0x[a-fA-F0-9]{40}\b', response.text)
        
        metadata = {
            'emails': emails,
            'ips': ips,
            'chatrooms': list(detected_chatroom_links),
            'btc_addresses': btc_addresses,
            'eth_addresses': eth_addresses
        }

        # Enhanced geolocation with caching
        if GEO_ENABLED and ips:
            for ip in ips:
                try:
                    geo_data = geo_service.get_geolocation(ip)
                    if geo_data:
                        country = geo_data.get('country_name', 'Unknown')
                        city = geo_data.get('city', 'Unknown')
                        self.logger.info(f"🗺️ IP {ip} located in: {city}, {country}")
                        metadata[f'geo_{ip}'] = {
                            'country': country,
                            'city': city,
                            'latitude': geo_data.get('latitude'),
                            'longitude': geo_data.get('longitude')
                        }
                except Exception as e:
                    self.logger.warning(f"Failed to get geolocation for {ip}: {e}")

        # Standard processing continues...
        self.logger.info(f"📥 Processing: {response.url}")
        
        content_type = response.headers.get('Content-Type', b'').decode().lower()
        if not any(text_type in content_type for text_type in ['text/html', 'text/plain', 'application/xhtml+xml']):
            self.logger.info(f"⚠️ Skipping non-text content: {response.url} ({content_type})")
            return
        
        url = response.url
        if url in visited_links:
            return

        visited_links.add(url)
        crawled_pages += 1
        progress_bar.update(1)

        # Get page text safely
        try:
            page_text = response.text.lower()
        except AttributeError:
            self.logger.warning(f"⚠️ Could not extract text from {response.url}")
            return
            
        matched_keywords = [kw for kw in KEYWORDS if re.search(rf"\b{re.escape(kw.lower())}\b", page_text)]

        # Enhanced threat detection with AI analysis
        content_hash = hashlib.md5(response.text.encode('utf-8')).hexdigest()
        page_title = response.css('title::text').get() or "No Title"
        ai_analysis = None
        
        # Perform AI analysis if keywords detected or high-risk content suspected
        if matched_keywords or self._is_suspicious_content(page_text, url):
            if AI_ENABLED:
                try:
                    self.logger.info(f"🧠 Running AI analysis for: {url}")
                    ai_analysis = analyze_with_ai_sync(
                        url=url,
                        title=page_title,
                        content=response.text[:5000],
                        keywords=matched_keywords
                    )
                    
                    if ai_analysis:
                        ai_data = {
                            'content_hash': content_hash,
                            'url': url,
                            'threat_level': ai_analysis.threat_level,
                            'threat_categories': ai_analysis.threat_categories,
                            'suspicious_indicators': ai_analysis.suspicious_indicators,
                            'illegal_content_detected': ai_analysis.illegal_content_detected,
                            'confidence_score': ai_analysis.confidence_score,
                            'analysis_summary': ai_analysis.analysis_summary,
                            'recommended_actions': ai_analysis.recommended_actions,
                            'ai_reasoning': ai_analysis.ai_reasoning,
                            'threat_signature': gemini_analyzer.create_threat_signature(ai_analysis)
                        }
                        db_manager.insert_ai_analysis(ai_data)
                        
                        signature_hash = hashlib.sha256(f"{ai_analysis.threat_level}_{','.join(ai_analysis.threat_categories)}".encode()).hexdigest()[:16]
                        db_manager.update_threat_signature(
                            signature_hash,
                            ai_analysis.threat_level,
                            ai_analysis.suspicious_indicators,
                            ai_analysis.confidence_score
                        )
                        
                        self.logger.info(f"🎯 AI Analysis: {ai_analysis.threat_level} threat detected with {ai_analysis.confidence_score:.2f} confidence")
                        
                        if REALTIME_ENABLED:
                            notify_ai_analysis_complete(ai_data)
                        
                except Exception as e:
                    self.logger.error(f"❌ AI analysis failed for {url}: {e}")
                    ai_analysis = None
        
        # Create alert based on keyword detection or AI analysis
        if matched_keywords or (ai_analysis and ai_analysis.threat_level in ['CRITICAL', 'HIGH', 'MEDIUM']):
            threat_level = ai_analysis.threat_level if ai_analysis else self._determine_threat_level(matched_keywords)
            
            alert = Alert(
                timestamp=str(datetime.now()),
                url=url,
                title=page_title,
                keywords_found=matched_keywords,
                content_hash=content_hash,
                threat_level=threat_level
            )
            db_manager.insert_alert(alert)
            
            if REALTIME_ENABLED:
                notify_alert_created({
                    "url": alert.url,
                    "title": alert.title,
                    "threat_level": threat_level,
                    "keywords_found": matched_keywords,
                    "timestamp": alert.timestamp
                })

            # Enhanced Telegram alert
            base_message = f"""
🚨 <b>TRINETRA THREAT DETECTED</b>
🔗 <b>URL:</b> {alert.url}
🧠 <b>Title:</b> {alert.title}
🚨 <b>Threat Level:</b> {threat_level}
🕒 <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
"""
            
            if matched_keywords:
                base_message += f"🔍 <b>Keywords:</b> {', '.join(matched_keywords)}\n"
            
            if ai_analysis:
                base_message += f"""
🤖 <b>AI Analysis:</b> {ai_analysis.analysis_summary}
📊 <b>Confidence:</b> {ai_analysis.confidence_score:.1%}
🎯 <b>Categories:</b> {', '.join(ai_analysis.threat_categories[:3])}
"""
                
                if ai_analysis.illegal_content_detected:
                    base_message += "⚠️ <b>ILLEGAL CONTENT DETECTED!</b>\n"
                
                if ai_analysis.recommended_actions:
                    base_message += f"📋 <b>Actions:</b> {', '.join(ai_analysis.recommended_actions[:2])}\n"
            
            send_telegram_alert(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, base_message)
        
        # Store page data
        page_threat_level = ai_analysis.threat_level if ai_analysis else self._determine_threat_level(matched_keywords)
        
        crawled_page = CrawledPage(
            url=url,
            title=page_title,
            content_hash=content_hash,
            timestamp=str(datetime.now()),
            response_code=response.status,
            processing_time=0.0,
            page_size=len(response.text),
            links_found=len(response.css("a").getall()) if 'text/html' in content_type else 0
        )
        db_manager.insert_crawled_page(crawled_page)
        
        if REALTIME_ENABLED:
            notify_page_scraped(
                url=url,
                title=page_title,
                threat_level=page_threat_level,
                keywords=matched_keywords
            )
        
        # Graph node management
        db_manager.upsert_graph_node(
            url=url,
            title=page_title,
            node_type='page',
            threat_level=page_threat_level,
            page_size=len(response.text)
        )

        # Enhanced link following with better error handling
        self._follow_links_robustly(response, url)

    def _follow_links_robustly(self, response, base_url):
        """Enhanced link following with robust error handling"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            try:
                if 'text/html' in response.headers.get('Content-Type', b'').decode():
                    link_position = 0
                    for link_element in response.css("a"):
                        href = link_element.css("::attr(href)").get()
                        if not href:
                            continue
                            
                        full_url = urljoin(base_url, href)
                        link_text = link_element.css("::text").get() or ""
                        link_text = link_text.strip()[:100]
                        
                        # Enhanced link validation
                        if self._is_valid_link(full_url):
                            db_manager.insert_link_relationship(
                                source_url=base_url,
                                target_url=full_url,
                                link_text=link_text,
                                link_position=link_position
                            )
                            
                            if '.onion' in full_url:
                                db_manager.upsert_graph_node(
                                    url=full_url,
                                    title=link_text if link_text else "Untitled",
                                    node_type='page',
                                    threat_level='LOW',
                                    page_size=0
                                )
                        
                        # Follow valid onion links
                        if (full_url.startswith(('http://', 'https://')) and 
                            '.onion' in full_url and 
                            full_url not in visited_links and
                            not self._should_skip_url(full_url)):
                            futures.append(executor.submit(self._yield_request_safely, response, full_url))

                        elif full_url.startswith(('mailto:', 'irc://', 'xmpp:')):
                            self.logger.info(f"📩 Found non-HTTP link: {full_url}")
                            non_http_links.append({
                                "source": response.url,
                                "type": full_url.split(':')[0],
                                "value": full_url
                            })
                        
                        link_position += 1
                        
            except Exception as e:
                self.logger.warning(f"Error parsing links from {base_url}: {e}")
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        yield result
                except Exception as e:
                    self.logger.error(f"Error yielding request: {e}")

    def _is_valid_link(self, url):
        """Enhanced link validation"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            if parsed.netloc in self.blocked_domains:
                return False
            return True
        except:
            return False

    def _yield_request_safely(self, response, full_url):
        """Safely yield requests with enhanced error handling"""
        try:
            if full_url not in visited_links:
                request = response.follow(
                    full_url, 
                    callback=self.parse,
                    errback=self.errback_handler,
                    meta={
                        'download_timeout': 90,
                        'retry_times': 8
                    }
                )
                return request
        except Exception as e:
            self.logger.error(f"Error creating request for {full_url}: {e}")
            return None
    
    def errback_handler(self, failure):
        """Enhanced error handling with blocking detection"""
        url = failure.request.url
        self.logger.error(f"❌ Request failed: {url}")
        self.logger.error(f"Reason: {repr(failure)}")
        
        # Track failed domains for blocking
        domain = urlparse(url).netloc
        if domain not in self.failed_requests:
            self.failed_requests[domain] = 0
        self.failed_requests[domain] += 1
        
        # Block problematic domains after multiple failures
        if self.failed_requests[domain] > 5:
            self.blocked_domains.add(domain)
            self.logger.warning(f"Domain {domain} blocked after {self.failed_requests[domain]} failures")
        
        # Log failed links
        with open("failed_links.txt", "a") as f:
            f.write(f"{url}\n")
    
    def _should_skip_url(self, url):
        """Enhanced URL filtering with better patterns"""
        skip_domains = [
            'duckduckgo', 'google', 'bing', 'yahoo', 'startpage',
            'facebook', 'twitter', 'instagram', 'youtube'
        ]
        
        skip_extensions = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
            '.exe', '.msi', '.deb', '.rpm', '.dmg',
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
        ]
        
        skip_patterns = [
            r'/api/',
            r'/ajax/',
            r'/download/',
            r'/static/',
            r'/assets/',
            r'\.json$',
            r'\.xml$',
            r'\.rss$'
        ]
        
        url_lower = url.lower()
        
        # Check domains
        for domain in skip_domains:
            if domain in url_lower:
                return True
        
        # Check extensions
        for ext in skip_extensions:
            if url_lower.endswith(ext):
                return True
        
        # Check patterns
        for pattern in skip_patterns:
            if re.search(pattern, url_lower):
                return True
                
        return False
    
    def _is_suspicious_content(self, page_text, url):
        """Enhanced suspicious content detection"""
        suspicious_patterns = [
            r'(?i)(buy|sell|order|purchase).*(drug|narcotic|cocaine|heroin|meth|lsd|mdma|fentanyl)',
            r'(?i)(weapon|gun|rifle|pistol|bomb|explosive|grenade|ammunition)',
            r'(?i)(credit.*card|cvv|dump|fullz|carding|fraud|stolen.*data)',
            r'(?i)(hacking.*service|malware|ransomware|ddos.*attack|botnet)',
            r'(?i)(child|minor|underage).*(porn|sex|abuse|exploitation)',
            r'(?i)(human.*trafficking|slave|forced.*labor|kidnap)',
            r'(?i)(terrorism|terrorist|attack|bomb.*making|isis|al.*qaeda)',
            r'(?i)(money.*laundering|bitcoin.*mixer|crypto.*tumbler|darknet.*market)',
            r'(?i)(assassination|murder.*for.*hire|hitman|contract.*kill)',
            r'(?i)(passport|id.*card|social.*security|driver.*license).*(fake|forged|stolen)',
            r'bitcoin|monero|zcash|cryptocurrency.*[0-9a-f]{32,}',
            r'[0-9]{4}.*[0-9]{4}.*[0-9]{4}.*[0-9]{4}',
            r'(?i)(vendor|escrow|market|shop|store).*(tor|onion|darknet)',
            r'(?i)(pgp|encryption|anonymous|untraceable)',
        ]
        
        # Enhanced URL analysis
        url_suspicious = any([
            'market' in url.lower(),
            'shop' in url.lower() and '.onion' in url,
            'vendor' in url.lower(),
            'admin' in url.lower(),
            'upload' in url.lower(),
            'forum' in url.lower() and '.onion' in url,
            'trade' in url.lower(),
            'exchange' in url.lower() and '.onion' in url,
        ])
        
        # Content analysis
        content_suspicious = any(re.search(pattern, page_text) for pattern in suspicious_patterns)
        
        return url_suspicious or content_suspicious
    
    def _determine_threat_level(self, keywords):
        """Enhanced threat level determination"""
        critical_risks = ['bomb', 'terror', 'attack', 'kill', 'murder', 'assassination', 'child', 'minor', 'trafficking']
        high_risks = ['weapon', 'explosive', 'drug', 'narcotic', 'malware', 'ransomware', 'hitman']
        medium_risks = ['carding', 'hacking', 'fraud', 'exploit', 'phishing', 'stolen', 'fake']
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if any(risk in keyword_lower for risk in critical_risks):
                return 'CRITICAL'
            elif any(risk in keyword_lower for risk in high_risks):
                return 'HIGH'
            elif any(risk in keyword_lower for risk in medium_risks):
                return 'MEDIUM'
        return 'LOW'

    def closed(self, reason):
        """Enhanced cleanup with better logging"""
        progress_bar.close()
        
        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
            except:
                pass

        # Store non-HTTP links
        if non_http_links:
            with db_manager.get_cursor() as cursor:
                for link in non_http_links:
                    cursor.execute("""
                        INSERT INTO non_http_links (source_url, link_type, link_value, discovered_at)
                        VALUES (?, ?, ?, ?)
                    """, (link['source'], link['type'], link['value'], datetime.now().isoformat()))

        # Store chatroom links
        if chatroom_links:
            with db_manager.get_cursor() as cursor:
                for chatroom in chatroom_links:
                    cursor.execute("""
                        INSERT INTO chatroom_links (source_url, chatroom_url, chatroom_type)
                        VALUES (?, ?, ?)
                    """, (chatroom['source_url'], chatroom['chatroom_url'], chatroom['chatroom_type']))
            self.logger.info(f"🗨️ Stored {len(chatroom_links)} chatroom links for investigation")

        # Log summary statistics
        self.logger.info(f"✅ Crawl complete. {crawled_pages} pages scanned.")
        self.logger.info(f"📊 Failed domains: {len(self.blocked_domains)}")
        self.logger.info(f"🔍 CAPTCHA solve attempts: {len(self.captcha_solve_attempts)}")
        self.logger.info(f"🚫 Blocked domains: {', '.join(list(self.blocked_domains)[:5])}")
