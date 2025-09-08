import requests
from bs4 import BeautifulSoup
from src.utils import normalize_price_val
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " 
                  "AppleWebKit/537.36 (KHTML, like Gecko) " 
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9"
}

def get_page(url, timeout=15):
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text

def scrape_amazon(url):
    html = get_page(url)
    soup = BeautifulSoup(html, "html.parser")

    title = None
    selectors = [
        ("span", {"id": "productTitle"}),
        ("span", {"class": "a-size-large product-title-word-break"}),
        ("span", {"class": "a-size-large a-color-base a-text-normal"}),
    ]
    for tag, attrs in selectors:
        el = soup.find(tag, attrs=attrs)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break

    price = None
    price_selectors = [
        ("span", {"id": "priceblock_ourprice"}),
        ("span", {"id": "priceblock_dealprice"}),
        ("span", {"class": "a-price-whole"}),
        ("span", {"class": "a-offscreen"}),
    ]
    for tag, attrs in price_selectors:
        el = soup.find(tag, attrs=attrs)
        if el:
            price = el.get_text(strip=True)
            break
    if not price:
        candidate = soup.find(text=re.compile(r"₹\s*\d"))
        if candidate:
            price = candidate.strip()

    image = None
    img_selectors = [
        ("img", {"id": "landingImage"}),
        ("img", {"id": "imgBlkFront"}),
        ("img", {"class": "a-dynamic-image"}),
    ]
    for tag, attrs in img_selectors:
        el = soup.find(tag, attrs=attrs)
        if el and el.get("src"):
            image = el.get("src")
            break

    asin = None
    m = re.search(r"/dp/([A-Z0-9]{10})", url)
    if not m:
        m = re.search(r"/gp/product/([A-Z0-9]{10})", url)
    if m:
        asin = m.group(1)

    return {
        "title": title or "Unknown Amazon product",
        "price": normalize_price_val(price),
        "image": image,
        "product_id": asin
    }

def scrape_flipkart(url):
    html = get_page(url)
    soup = BeautifulSoup(html, "html.parser")

    title = None
    el = soup.find("span", {"class": "B_NuCI"})
    if el:
        title = el.get_text(strip=True)
    else:
        el = soup.find("span", {"class": "_35KyD6"})
        if el:
            title = el.get_text(strip=True)

    price = None
    price_el = soup.find("div", {"class": "_30jeq3 _16Jk6d"})
    if not price_el:
        price_el = soup.find("div", {"class": "_30jeq3"})
    if price_el:
        price = price_el.get_text(strip=True)
    else:
        candidate = soup.find(text=re.compile(r"₹\s*\d"))
        if candidate:
            price = candidate.strip()

    image = None
    img = soup.find("img", {"class": "_396cs4 _2amPTt _3qGmMb "})
    if img and img.get("src"):
        image = img.get("src")
    else:
        img2 = soup.find("img", {"class": "_2r_T1I"})
        if img2 and img2.get("src"):
            image = img2.get("src")

    pid = None
    parsed = re.search(r"/p/([^?/]*)", url)
    if parsed:
        pid = parsed.group(1)

    return {
        "title": title or "Unknown Flipkart product",
        "price": normalize_price_val(price),
        "image": image,
        "product_id": pid
    }