BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

DOWNLOADER_MIDDLEWARES = {
    "crawler.middlewares.socks5_handler.EnhancedProxyMiddleware": 100,
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": None,  # Disable default proxy middleware
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 3

# ✅ Enhanced timeout and retry settings for Tor crawling
DOWNLOAD_TIMEOUT = 90  # Extended timeout for Tor connections
RETRY_TIMES = 2        # Reduced retries to avoid excessive delays

# Additional proxy and connection settings
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
RANDOMIZE_DOWNLOAD_DELAY = 0.5 * DOWNLOAD_DELAY
