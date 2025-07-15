import scrapy

class DarkForumSpider(scrapy.Spider):
    name = "dark_forum"
    allowed_domains = ["duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion"]
    start_urls = ["http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/"]

    def parse(self, response):
        self.logger.info(f"Visiting: {response.url}")
        yield {
            "title": response.css("title::text").get(),
            "url": response.url
        }
