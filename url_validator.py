
def clean_and_validate_onion_url(url):
    """Clean and validate onion URL for dark web crawling"""
    import re
    
    if not url or not isinstance(url, str):
        return None, "URL must be a non-empty string"
    
    # Clean the URL
    url = url.strip().replace('\n', '').replace('\r', '').replace('\t', '')
    
    # Fix protocol
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    # Validate onion format
    onion_v2_pattern = r'^https?://[a-z2-7]{16}\.onion(/.*)?$'
    onion_v3_pattern = r'^https?://[a-z2-7]{56}\.onion(/.*)?$'
    
    if not (re.match(onion_v2_pattern, url, re.IGNORECASE) or 
            re.match(onion_v3_pattern, url, re.IGNORECASE)):
        return None, "Invalid onion URL format"
    
    return url, "URL is valid"
