import scrapy
import json
import os
import re
import hashlib
import concurrent.futures
import random
import time
import requests
from datetime import datetime
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
from telegram_alert import send_telegram_alert
from database.models import db_manager, Alert, CrawledPage
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import get_base_url
from scrapy.http import Request

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

# Load keywords
with open("keyword.json") as f:
    KEYWORDS = set(json.load(f).get("india_keywords", []))

# Configs
TELEGRAM_BOT_TOKEN = "7764356588:AAFyfqTvVrZ8_MG6B45JuVL1EC-iFZ_4oc4"
TELEGRAM_CHAT_ID = "5188590599"

# Enhanced User Agents for better bypassing
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
]

# Proxy rotation for better anonymity
TOR_PROXIES = [
    "http://127.0.0.1:8118",
    "http://127.0.0.1:8119",
    "http://127.0.0.1:8120",
    "socks5://127.0.0.1:9050",
    "socks5://127.0.0.1:9051",
    "socks5://127.0.0.1:9052"
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

crawled_pages = 0
non_http_links = []
visited_links = set(link['url'] for link in db_manager.get_crawled_pages(limit=1000000))
failed_requests = {}

# Progress bar (set arbitrary high limit since unlimited)
progress_bar = tqdm(total=1000000, desc="🌐 Crawling Progress", unit="page")

class OnionCrawler(scrapy.Spider):
    name = "onion"
    custom_settings = {
        "USER_AGENT": random.choice(USER_AGENTS),
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8,fr;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        },
        "DOWNLOAD_DELAY": random.uniform(2, 5),
        "RANDOMIZE_DOWNLOAD_DELAY": 0.5,
        "RETRY_TIMES": 8,
        "DOWNLOAD_TIMEOUT": 45,
        "COOKIES_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "HTTPERROR_ALLOWED_CODES": [403, 404, 500, 502, 503, 504, 521, 522, 523, 524],
        "HANDLE_HTTPSTATUS_ALL": True,
        "CONCURRENT_REQUESTS": 16,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 10,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'crawler.middlewares.socks5_handler.EnhancedProxyMiddleware': 100,
        },
        "PROXY_ROTATION_ENABLED": True,
        "USER_AGENT_ROTATION_ENABLED": True,
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super(OnionCrawler, self).__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("⚠ Please provide a start_url using -a start_url=<url>")
        self.start_url = start_url  # Store single start_url
        self.session = requests.Session()
        self.tor_circuit_refresh_counter = 0
        
    def start_requests(self):
        """✅ Force start_requests() to yield explicitly"""
        yield scrapy.Request(
            url=self.start_url,
            callback=self.parse,
            errback=self.errback_handler,
            dont_filter=True
        )

    def parse(self, response):
        global crawled_pages
        
        # ✅ Add parse() logging
        self.logger.info(f"📥 Reached parse(): {response.url}")
        
        # Check if response is text content before processing
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
                        content=response.text[:5000],  # Limit content size
                        keywords=matched_keywords
                    )
                    
                    if ai_analysis:
                        # Store AI analysis results
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
                        
                        # Update threat signature database
                        signature_hash = hashlib.sha256(f"{ai_analysis.threat_level}_{','.join(ai_analysis.threat_categories)}".encode()).hexdigest()[:16]
                        db_manager.update_threat_signature(
                            signature_hash,
                            ai_analysis.threat_level,
                            ai_analysis.suspicious_indicators,
                            ai_analysis.confidence_score
                        )
                        
                        self.logger.info(f"🎯 AI Analysis: {ai_analysis.threat_level} threat detected with {ai_analysis.confidence_score:.2f} confidence")
                        
                except Exception as e:
                    self.logger.error(f"❌ AI analysis failed for {url}: {e}")
                    ai_analysis = None
        
        # Create alert based on keyword detection or AI analysis
        if matched_keywords or (ai_analysis and ai_analysis.threat_level in ['CRITICAL', 'HIGH', 'MEDIUM']):
            # Use AI threat level if available, otherwise use keyword-based level
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

            # Enhanced Telegram alert with AI insights
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

        # Follow links concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []

            try:
                # Only process HTML responses
                if 'text/html' in response.headers.get('Content-Type', b'').decode():
                    for href in response.css("a::attr(href)").getall():
                        full_url = urljoin(url, href)

                        # Filter out unwanted domains and file types
                        if (full_url.startswith(('http://', 'https://')) and 
                            '.onion' in full_url and 
                            full_url not in visited_links and
                            not self._should_skip_url(full_url)):
                            futures.append(executor.submit(self.yield_request, response, full_url))

                        elif full_url.startswith(('mailto:', 'irc://', 'xmpp:')):
                            self.logger.info(f"📩 Found non-HTTP link: {full_url}")
                            non_http_links.append({
                                "source": response.url,
                                "type": full_url.split(':')[0],
                                "value": full_url
                            })
            except Exception as e:
                self.logger.warning(f"Error parsing links from {url}: {e}")
            
            for future in concurrent.futures.as_completed(futures):
                yield future.result()

    def yield_request(self, response, full_url):
        if full_url not in visited_links:
            request = response.follow(full_url, callback=self.parse)
            # Proxy will be handled by middleware
            return request
    
    def errback_handler(self, failure):
        """✅ Add errback_handler() for failed requests"""
        self.logger.error(f"❌ Request failed: {failure.request.url}")
        self.logger.error(f"Reason: {repr(failure)}")
        
        # Log failed links to file
        with open("failed_links.txt", "a") as f:
            f.write(f"{failure.request.url}\n")
    
    def _should_skip_url(self, url):
        """Check if URL should be skipped based on domain or file type"""
        # Skip common search engines and non-relevant domains
        skip_domains = [
            'duckduckgo',
            'google',
            'bing',
            'yahoo',
            'startpage'
        ]
        
        # Skip binary file types
        skip_extensions = [
            '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.exe', '.msi', '.deb', '.rpm',
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
        ]
        
        url_lower = url.lower()
        
        # Check domains
        for domain in skip_domains:
            if domain in url_lower:
                self.logger.info(f"⚠️ Skipping search engine: {url}")
                return True
        
        # Check file extensions
        for ext in skip_extensions:
            if url_lower.endswith(ext):
                self.logger.info(f"⚠️ Skipping binary file: {url}")
                return True
                
        return False
    
    def _is_suspicious_content(self, page_text, url):
        """Detect suspicious content patterns that warrant AI analysis"""
        suspicious_patterns = [
            r'(?i)(buy|sell|order|purchase).*(drug|narcotic|cocaine|heroin|meth|lsd|mdma)',
            r'(?i)(weapon|gun|rifle|pistol|bomb|explosive|grenade)',
            r'(?i)(credit.*card|cvv|dump|fullz|carding|fraud)',
            r'(?i)(hacking.*service|malware|ransomware|ddos.*attack)',
            r'(?i)(child|minor|underage).*(porn|sex|abuse)',
            r'(?i)(human.*trafficking|slave|forced.*labor)',
            r'(?i)(terrorism|terrorist|attack|bomb.*making)',
            r'(?i)(money.*laundering|bitcoin.*mixer|crypto.*tumbler)',
            r'(?i)(assassination|murder.*for.*hire|hitman)',
            r'(?i)(passport|id.*card|social.*security).*(fake|forged)',
            r'bitcoin|monero|cryptocurrency.*exchange.*[0-9a-f]{32,}',  # Crypto addresses
            r'[0-9]{4}.*[0-9]{4}.*[0-9]{4}.*[0-9]{4}',  # Credit card patterns
        ]
        
        # Check URL structure for suspicious patterns
        url_suspicious = any([
            'market' in url.lower(),
            'shop' in url.lower() and '.onion' in url,
            'vendor' in url.lower(),
            'admin' in url.lower(),
            'upload' in url.lower(),
        ])
        
        # Check content for suspicious patterns
        content_suspicious = any(re.search(pattern, page_text) for pattern in suspicious_patterns)
        
        return url_suspicious or content_suspicious
    
    def _determine_threat_level(self, keywords):
        """Determine threat level based on keywords"""
        high_risk = ['bomb', 'terror', 'attack', 'kill', 'explosive', 'weapon', 'assassination', 'murder']
        medium_risk = ['carding', 'hacking', 'drugs', 'malware', 'exploit', 'phishing', 'fraud', 'ransomware']
        
        for keyword in keywords:
            if any(risk in keyword.lower() for risk in high_risk):
                return 'HIGH'
            elif any(risk in keyword.lower() for risk in medium_risk):
                return 'MEDIUM'
        return 'LOW'

    def closed(self, reason):
        progress_bar.close()

        if non_http_links:
            with db_manager.get_cursor() as cursor:
                for link in non_http_links:
                    cursor.execute("""
                        INSERT INTO non_http_links (source_url, link_type, link_value, discovered_at)
                        VALUES (?, ?, ?, ?)
                    """, (link['source'], link['type'], link['value'], datetime.now().isoformat()))

        self.logger.info(f"✅ Crawl complete. {crawled_pages} pages scanned.")
