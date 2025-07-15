class Socks5ProxyMiddleware:
    def process_request(self, request, spider):
        if ".onion" in request.url:
            request.meta['proxy'] = "http://127.0.0.1:8118"
