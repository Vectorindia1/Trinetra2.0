BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

DOWNLOADER_MIDDLEWARES = {
    "crawler.middlewares.socks5_handler.Socks5ProxyMiddleware": 100,
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 3
