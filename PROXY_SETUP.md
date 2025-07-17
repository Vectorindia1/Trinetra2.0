# Enhanced Darknet Crawler with SOCKS5 Support

## Overview

Your darknet crawler now supports both **HTTP** and **SOCKS5** proxy connections through Tor, enabling comprehensive crawling of .onion domains and regular websites.

## Features

### ✅ **Multi-Proxy Support**
- **SOCKS5 Proxy**: `socks5://127.0.0.1:9050` (Primary for .onion domains)
- **SOCKS5 Proxy**: `socks5://127.0.0.1:9051` (Secondary)  
- **HTTP Proxy**: `http://127.0.0.1:8118` (Fallback)

### ✅ **Smart Proxy Selection**
- **Automatic SOCKS5 for .onion domains**: For maximum compatibility with Tor hidden services
- **Proxy rotation**: Automatically rotates between available proxies
- **Fallback mechanism**: Falls back to HTTP proxy if SOCKS5 fails

### ✅ **Enhanced Middleware**
- **Dynamic proxy assignment**: Each request gets an appropriate proxy
- **User-Agent rotation**: Randomizes user agents for better anonymity
- **Blocking pattern detection**: Detects and handles anti-bot measures
- **Automatic retry**: Rotates proxies on connection failures

## Configuration

### Proxy Settings
The crawler automatically configures these proxies:
```python
TOR_PROXIES = [
    "socks5://127.0.0.1:9050",  # Primary SOCKS5 
    "socks5://127.0.0.1:9051",  # Secondary SOCKS5
    "http://127.0.0.1:8118"     # HTTP proxy
]
```

### Middleware Configuration
```python
DOWNLOADER_MIDDLEWARES = {
    'crawler.middlewares.socks5_handler.EnhancedProxyMiddleware': 100,
}
PROXY_ROTATION_ENABLED = True
USER_AGENT_ROTATION_ENABLED = True
```

## Usage

### Basic Usage
```bash
cd /home/vector/darknet_crawler
./run_all.sh http://your-onion-site.onion
```

### Manual Scrapy Command
```bash
cd /home/vector/darknet_crawler
source tor-env/bin/activate
scrapy runspider crawler/spiders/tor_crawler.py -a start_url="http://your-onion-site.onion"
```

### Test the Setup
```bash
cd /home/vector/darknet_crawler
source tor-env/bin/activate
python test_socks5.py
```

## Proxy Behavior

### For .onion Domains
1. **Primary**: Uses SOCKS5 proxy (`socks5://127.0.0.1:9050`)
2. **Secondary**: Uses SOCKS5 proxy (`socks5://127.0.0.1:9051`)
3. **Fallback**: Uses HTTP proxy (`http://127.0.0.1:8118`)

### For Regular Domains
1. **Rotates** between all available proxies
2. **Maintains anonymity** through Tor network
3. **Handles blocking** with proxy rotation

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure Tor service is running: `systemctl status tor`
   - Check if ports are open: `netstat -tlnp | grep -E "(9050|8118)"`

2. **DNS Lookup Failed**
   - Verify SOCKS5 proxy is working: `python test_socks5.py`
   - Check Tor configuration: `/etc/tor/torrc`

3. **Proxy Rotation Issues**
   - Check middleware is loaded in spider settings
   - Verify proxy list contains only available ports

### Testing Commands

```bash
# Test direct SOCKS5 connection
curl --socks5-hostname 127.0.0.1:9050 http://httpbin.org/ip

# Test HTTP proxy
curl --proxy http://127.0.0.1:8118 http://httpbin.org/ip

# Test the crawler
python test_socks5.py
```

## Security Features

### 🔒 **Enhanced Anonymity**
- Multiple proxy rotation
- Random user agent rotation
- Request timing randomization
- Circuit refresh capabilities

### 🛡️ **Anti-Detection**
- Blocking pattern detection
- Automatic retry mechanisms
- Realistic request headers
- Browser-like behavior simulation

## Performance Optimization

### Settings for Production
```python
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 2-5 seconds (randomized)
AUTOTHROTTLE_ENABLED = True
RETRY_TIMES = 8
```

### Settings for Testing
```python
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 2
RETRY_TIMES = 3
DOWNLOAD_TIMEOUT = 20
```

## Monitoring

### Check Proxy Status
```bash
# Check if Tor is running
ps aux | grep tor

# Check listening ports
netstat -tlnp | grep -E "(9050|8118|9051)"

# Check Tor logs
journalctl -u tor@default -f
```

### View Crawler Logs
```bash
# View real-time logs
tail -f crawler.log

# View proxy usage
grep "Using proxy" crawler.log
```

## Next Steps

1. **Test with known .onion sites** to verify functionality
2. **Monitor proxy rotation** in logs
3. **Adjust concurrency** based on target site behavior
4. **Implement additional blocking detection** patterns as needed

The crawler now provides comprehensive support for both HTTP and SOCKS5 proxies, ensuring maximum compatibility with all types of Tor hidden services and regular websites.
