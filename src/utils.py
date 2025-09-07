import re
from urllib.parse import urlparse, parse_qs

def detect_platform(url: str):
    url = url.lower()
    if "amazon." in url:
        return "amazon"
    if "flipkart." in url:
        return "flipkart"
    return "unknown"

def extract_amazon_asin(url: str):
    # Try to extract ASIN from common amazon url patterns
    # Examples:
    # https://www.amazon.in/dp/B08J5F3G18
    # https://www.amazon.in/gp/product/B08J5F3G18
    m = re.search(r"/dp/([A-Z0-9]{10})", url)
    if not m:
        m = re.search(r"/gp/product/([A-Z0-9]{10})", url)
    if m:
        return m.group(1)
    # fallback: check query params
    parsed = urlparse(url)
    q = parse_qs(parsed.query)
    if 'asin' in q:
        return q['asin'][0]
    return None

def extract_flipkart_id(url: str):
    # Flipkart product slug sometimes contains /p/ and query strings
    # We'll try to return a stable fingerprint (the path)
    parsed = urlparse(url)
    path = parsed.path
    # try to capture last segment
    parts = [p for p in path.split('/') if p]
    if parts:
        return parts[-1]
    return path