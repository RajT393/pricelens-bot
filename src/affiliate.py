import os
from src.utils import detect_platform
from src.scraper import scrape_amazon, scrape_flipkart
from urllib.parse import urlparse

AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG")

FLIPKART_AFFILIATE_ID = os.getenv("FLIPKART_AFFILIATE_ID")
FLIPKART_TOKEN = os.getenv("FLIPKART_TOKEN")

class AffiliateError(Exception):
    pass

def has_amazon_credentials():
    return bool(AMAZON_ACCESS_KEY and AMAZON_SECRET_KEY and AMAZON_ASSOCIATE_TAG)

def has_flipkart_credentials():
    return bool(FLIPKART_AFFILIATE_ID and FLIPKART_TOKEN)

def build_affiliate_link(platform: str, original_url: str):
    if platform == "amazon" and AMAZON_ASSOCIATE_TAG:
        sep = "&" if "?" in original_url else "?"
        return f"{original_url}{sep}tag={AMAZON_ASSOCIATE_TAG}"
    if platform == "flipkart" and FLIPKART_AFFILIATE_ID:
        sep = "&" if "?" in original_url else "?"
        return f"{original_url}{sep}affid={FLIPKART_AFFILIATE_ID}"
    return original_url

def fetch_amazon_api(url: str):
    raise AffiliateError("Amazon API integration not implemented. Bot will fallback to scraping.")

def fetch_flipkart_api(url: str):
    raise AffiliateError("Flipkart API integration not implemented. Bot will fallback to scraping.")

def get_product_by_url(url: str):
    platform = detect_platform(url)
    if platform == "amazon":
        if has_amazon_credentials():
            try:
                return fetch_amazon_api(url)
            except Exception:
                pass
        return scrape_amazon(url) | {"affiliate_link": build_affiliate_link("amazon", url)}
    elif platform == "flipkart":
        if has_flipkart_credentials():
            try:
                return fetch_flipkart_api(url)
            except Exception:
                pass
        return scrape_flipkart(url) | {"affiliate_link": build_affiliate_link("flipkart", url)}
    else:
        if "amazon" in url.lower():
            return scrape_amazon(url) | {"affiliate_link": build_affiliate_link("amazon", url)}
        if "flipkart" in url.lower():
            return scrape_flipkart(url) | {"affiliate_link": build_affiliate_link("flipkart", url)}
        return {"title": "Unknown product", "price": None, "image": None, "product_id": None, "affiliate_link": url}