#!/usr/bin/env python3

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler.spiders.tor_crawler import OnionCrawler

def test_onion_crawler():
    """Test the crawler with .onion domains"""
    
    # Test URLs (some may be down, that's expected)
    test_urls = [
        "http://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion",
        "http://httpbin.org/ip",  # Regular site for comparison
    ]
    
    print("🧪 Testing Enhanced Onion Crawler with SOCKS5 Support")
    print("=" * 60)
    
    # Configure settings
    settings = get_project_settings()
    settings.update({
        'LOG_LEVEL': 'INFO',
        'CLOSESPIDER_TIMEOUT': 30,  # Stop after 30 seconds
        'CLOSESPIDER_PAGECOUNT': 5,  # Stop after 5 pages
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 3,
        'DOWNLOAD_TIMEOUT': 20,
    })
    
    for url in test_urls:
        print(f"\n🔍 Testing: {url}")
        print("-" * 40)
        
        # Create crawler process
        process = CrawlerProcess(settings)
        
        try:
            # Start the crawler
            process.crawl(OnionCrawler, start_url=url)
            process.start()
            
            print(f"✅ Crawler completed for {url}")
            
        except Exception as e:
            print(f"❌ Error crawling {url}: {e}")
        
        # Reset the reactor for next test
        if hasattr(process, 'reactor'):
            process.reactor.stop()

if __name__ == "__main__":
    test_onion_crawler()
