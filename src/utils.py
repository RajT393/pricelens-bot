import re
from urllib.parse import urlparse

def detect_platform(url: str) -> str:
    u = url.lower()
    if "amazon." in u:
        return "amazon"
    if "flipkart." in u:
        return "flipkart"
    if "ajio." in u:
        return "ajio"
    if "shopsy." in u:
        return "shopsy"
    return "unknown"

def normalize_price_val(p):
    if p is None:
        return None
    s = str(p)
    s = re.sub(r"[^\d\.]", "", s)
    try:
        return float(s) if s != "" else None
    except:
        return None