import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from src.db import get_session, Product, User, PriceHistory
from src.affiliate import get_product_by_url
from src.utils import normalize_price_val
import datetime
import requests

logger = logging.getLogger("tracker")
logger.setLevel(logging.INFO)

SCHED = BackgroundScheduler()
INTERVAL_SECONDS = int(os.getenv("PRICE_CHECK_INTERVAL_SECONDS", "300"))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
BASE_WAPI = "https://graph.facebook.com/v17.0"

def send_telegram_message(chat_id: str, text: str):
    if not TELEGRAM_TOKEN:
        logger.warning("No telegram token for notify")
        return
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode":"Markdown"}
    try:
        r = requests.post(api, json=payload, timeout=10)
        if r.status_code >= 300:
            logger.warning("Telegram notify failed %s", r.text)
    except Exception as e:
        logger.exception("Telegram notify error: %s", e)

def send_whatsapp_message(to: str, text: str, button_url: str = None):
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID):
        logger.warning("WhatsApp creds missing")
        return
    endpoint = f"{BASE_WAPI}/{WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    if button_url:
        payload = {
            "messaging_product":"whatsapp",
            "to": to,
            "type":"interactive",
            "interactive":{"type":"button","body":{"text":text},"action":{"buttons":[{"type":"url","url":button_url,"title":"🛒 Buy Now"}]}}}
    else:
        payload = {"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":text}}
    try:
        r = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        if r.status_code >= 300:
            logger.warning("WhatsApp notify failed %s", r.text)
    except Exception as e:
        logger.exception("WhatsApp notify error: %s", e)

def suggestion_text(new_price, lowest, highest):
    try:
        if new_price is None:
            return "OK deal"
        if lowest is None:
            lowest = new_price
        if highest is None:
            highest = new_price
        if float(new_price) <= float(lowest):
            return "BUY NOW — Lowest price!"
        if float(new_price) >= float(highest):
            return "WAIT — Price at (near) highest"
        if float(new_price) <= float(lowest) * 1.02:
            return "Good deal — consider buying"
        return "OK deal"
    except:
        return "OK deal"

def check_prices_job():
    logger.info("Running price check job...")
    with get_session() as s:
        prods = s.query(Product).filter(Product.tracking_status=="active").all()
        for p in prods:
            try:
                info = get_product_by_url(p.url)
                new_price = info.get("price")
                if new_price is None:
                    logger.debug("No price for product %s", p.id)
                    continue
                old_price = float(p.current_price) if p.current_price is not None else None
                new_price_f = float(new_price)
                if old_price is None or new_price_f != old_price:
                    p.prev_price = old_price
                    p.current_price = new_price_f
                    if p.lowest_price is None or new_price_f < float(p.lowest_price):
                        p.lowest_price = new_price_f
                    if p.highest_price is None or new_price_f > float(p.highest_price):
                        p.highest_price = new_price_f
                    p.last_checked = datetime.datetime.utcnow()
                    s.add(p); s.commit()
                    hist = PriceHistory(product_id=p.id, price=new_price_f, checked_at=datetime.datetime.utcnow())
                    s.add(hist); s.commit()
                    if p.prev_price is None:
                        delta_text = ""
                    else:
                        diff = new_price_f - float(p.prev_price)
                        sign = "increased" if diff > 0 else "decreased"
                        delta_text = f"The Product Price has {sign} by ₹{abs(int(diff))}.\n\n"
                    msg = (
                        f"{delta_text}"
                        f"☀️ *{p.product_name}*\n\n"
                        f"Previous price: ₹{int(p.prev_price) if p.prev_price is not None else 'N/A'}\n"
                        f"Current price: ₹{int(p.current_price)}\n\n"
                        f"Click here: {p.affiliate_link or p.url}\n\n"
                        f"⏱ Updated at [{p.last_checked.strftime('%d %b %Y, %H:%M')}]\n\n"
                        f"{suggestion_text(p.current_price, p.lowest_price, p.highest_price)}"
                    )
                    user = s.query(User).filter(User.user_id==p.user_id).first()
                    if user and user.platform == "telegram":
                        send_telegram_message(p.user_id, msg)
                    else:
                        send_whatsapp_message(p.user_id, msg, button_url=p.affiliate_link or p.url)
            except Exception as e:
                logger.exception("Error while checking product %s: %s", p.id, e)

def start_scheduler():
    if SCHED.get_jobs():
        return
    SCHED.add_job(check_prices_job, 'interval', seconds=INTERVAL_SECONDS, id='price_check', max_instances=1)
    SCHED.start()
    logger.info("Scheduler started with interval %s seconds", INTERVAL_SECONDS)

def stop_scheduler():
    try:
        SCHED.shutdown(wait=False)
    except Exception:
        pass