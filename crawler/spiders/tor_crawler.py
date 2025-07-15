import scrapy
import json
import os
import re
from datetime import datetime
from urllib.parse import urljoin
from tqdm import tqdm
from telegram_alert import send_telegram_alert

# Load keywords
with open("keyword.json") as f:
    KEYWORDS = set(json.load(f).get("india_keywords", []))

# Configs
visited_file = "visited_links.json"
alert_file = "alert_log.json"
non_http_file = "non_http_links.json"
TELEGRAM_BOT_TOKEN = "7764356588:AAFyfqTvVrZ8_MG6B45JuVL1EC-iFZ_4oc4"
TELEGRAM_CHAT_ID = "5188590599"

crawled_pages = 0
non_http_links = []

# Resume support
if os.path.exists(visited_file):
    with open(visited_file) as f:
        visited_links = set(json.load(f))
else:
    visited_links = set()

# Progress bar (set arbitrary high limit since unlimited)
progress_bar = tqdm(total=1000000, desc="🌐 Crawling Progress", unit="page")

class OnionCrawler(scrapy.Spider):
    name = "onion"
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
        "DOWNLOAD_DELAY": 3,
        "RETRY_TIMES": 5,
        "DOWNLOAD_TIMEOUT": 30,
        "COOKIES_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "HTTPERROR_ALLOWED_CODES": [503],
        "HANDLE_HTTPSTATUS_ALL": True,
        "DOWNLOADER_MIDDLEWARES": {
            'crawler.middlewares.socks5_handler.Socks5ProxyMiddleware': 100,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    },
}
 








    def __init__(self, start_url=None, *args, **kwargs):
        super(OnionCrawler, self).__init__(*args, **kwargs)
        if not start_url:
            raise ValueError("⚠ Please provide a start_url using -a start_url=<url>")
        self.start_urls = [start_url]

    def parse(self, response):
        global crawled_pages

        url = response.url
        if url in visited_links:
            return

        visited_links.add(url)
        crawled_pages += 1
        progress_bar.update(1)

        page_text = response.text.lower()
        matched_keywords = [kw for kw in KEYWORDS if re.search(rf"\b{re.escape(kw.lower())}\b", page_text)]

        if matched_keywords:
            alert = {
                "timestamp": str(datetime.now()),
                "url": url,
                "title": response.css('title::text').get() or "No Title",
                "keywords_found": matched_keywords
            }

            # Save alert
            with open(alert_file, "a") as f:
                f.write(json.dumps(alert) + "\n")

            # Send Telegram alert
            message = f"""
🚨 <b>Dark Web Alert Detected</b>
🔗 <b>URL:</b> {alert['url']}
🧠 <b>Title:</b> {alert['title']}
🚨 <b>Keywords:</b> {', '.join(alert['keywords_found'])}
🕒 <b>Timestamp:</b> {alert['timestamp']}
"""
            send_telegram_alert(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

        # Follow links
        for href in response.css("a::attr(href)").getall():
            full_url = urljoin(url, href)

            if full_url.startswith(('http://', 'https://')) and '.onion' in full_url and full_url not in visited_links:
                yield response.follow(full_url, callback=self.parse)

            elif full_url.startswith(('mailto:', 'irc://', 'xmpp:')):
                self.logger.info(f"📩 Found non-HTTP link: {full_url}")
                non_http_links.append({
                    "source": response.url,
                    "type": full_url.split(':')[0],
                    "value": full_url
                })

    def closed(self, reason):
        progress_bar.close()

        with open(visited_file, "w") as f:
            json.dump(list(visited_links), f, indent=2)

        if non_http_links:
            with open(non_http_file, "w") as f:
                json.dump(non_http_links, f, indent=2)

        self.logger.info(f"✅ Crawl complete. {crawled_pages} pages scanned.")
