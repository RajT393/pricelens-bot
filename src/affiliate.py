def get_product_by_url(url: str):
    """
    Dummy product fetcher for testing.
    Replace with official Amazon/Flipkart API + affiliate URL conversion later.
    """
    return {
        "platform": "Amazon" if "amazon" in url else "Flipkart",
        "product_id": "123456",
        "title": "Demo Product",
        "image": "https://via.placeholder.com/150",
        "affiliate_url": url,
        "price": 999
    }


'''import os
import re
import requests
from src.utils import extract_amazon_asin, extract_flipkart_id

# This module provides a lightweight wrapper:
# - If official credentials (Amazon PA-API / Flipkart token) are present, user should plug real API calls in the TODOs.
# - Otherwise, the module runs in demo mode and returns example data so the bot remains functional for local testing.

AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG")

FLIPKART_AFFILIATE_ID = os.getenv("FLIPKART_AFFILIATE_ID")
FLIPKART_TOKEN = os.getenv("FLIPKART_TOKEN")

DEMO = not (AMAZON_ACCESS_KEY and AMAZON_SECRET_KEY and AMAZON_ASSOCIATE_TAG) and not (FLIPKART_TOKEN)

def _demo_product(platform, url):
    return {
        "platform": platform,
        "product_id": extract_amazon_asin(url) if platform=='amazon' else extract_flipkart_id(url),
        "title": "Demo Product - Replace with API keys for live data",
        "price": 719,
        "image": "https://via.placeholder.com/400x400.png?text=Product+Image",
        "affiliate_url": _build_affiliate_link(platform, url)
    }

def _build_affiliate_link(platform, url):
    if platform == "amazon" and AMAZON_ASSOCIATE_TAG:
        # Note: For many Amazon product links, appending ?tag=yourtag-21 works to attribute the click.
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}tag={AMAZON_ASSOCIATE_TAG}"
    if platform == "flipkart" and FLIPKART_AFFILIATE_ID:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}affid={FLIPKART_AFFILIATE_ID}"
    return url

def get_product_by_url(url: str):
    platform = "amazon" if "amazon." in url.lower() else ("flipkart" if "flipkart." in url.lower() else "unknown")
    if DEMO:
        return _demo_product(platform, url)
    # If credentials exist, you should implement the official API calls below.
    # Amazon PA-API: you can use the official SDK or construct signed requests. See:
    # https://webservices.amazon.com/paapi5/documentation/
    if platform == "amazon":
        # TODO: implement PA-API call (example placeholder)
        try:
            # Placeholder: fall back to demo product for now
            return _demo_product("amazon", url)
        except Exception as e:
            return _demo_product("amazon", url)
    if platform == "flipkart":
        # TODO: implement Flipkart Affiliate API call
        try:
            # Example placeholder: The Flipkart affiliate API returns product listing for a given id.
            return _demo_product("flipkart", url)
        except Exception:
            return _demo_product("flipkart", url)
    return _demo_product("unknown", url)'''