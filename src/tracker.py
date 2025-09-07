import threading
import time
import src.db as db

scheduler_running = False

def start_scheduler():
    global scheduler_running
    scheduler_running = True
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()

def stop_scheduler():
    global scheduler_running
    scheduler_running = False

def run_scheduler():
    while scheduler_running:
        for item in db.tracked_items:
            # dummy update, later use API to check price
            item.current_price = item.current_price
        time.sleep(1800)  # 30 mins


'''import os
import time
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from src.db import list_tracked_items, update_prices
from src.affiliate import get_product_by_url

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

scheduler = BackgroundScheduler()
INTERVAL_MINUTES = int(os.getenv("PRICE_CHECK_INTERVAL_MINUTES", "60"))

def notify_telegram_chat(chat_id, text, url=None):
    if not TELEGRAM_TOKEN:
        print("No telegram token - cannot notify telegram.")
        return
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if url:
        payload["text"] = f"{text}\n\nBuy: {url}"
    r = requests.post(api, json=payload)
    if r.status_code >= 300:
        print("Telegram notify failed:", r.status_code, r.text)

def notify_whatsapp(phone, text, url=None):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        print("WhatsApp creds missing - cannot notify WhatsApp.")
        return
    # Reuse whatsapp_bot send endpoint format
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive" if url else "text",
    }
    if url:
        payload["interactive"] = {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": [{"type": "url", "url": url, "title": "🛒 Buy Now"}]}
        }
    else:
        payload["text"] = {"body": text}
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    resp = requests.post(f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages", headers=headers, json=payload)
    if resp.status_code >= 300:
        print("WhatsApp notify failed:", resp.status_code, resp.text)

def check_all_prices():
    print("Running scheduled price check for tracked items...")
    items = list_tracked_items_all()
    for it in items:
        try:
            # use affiliate API/wrapper to fetch fresh data by url (we stored affiliate_url)
            data = get_product_by_url(it.affiliate_url or it.image_url or "")
            new_price = data.get("price")
            updated = update_prices(it.id, new_price)
            if updated:
                item, changed = updated
                if changed and item.current_price and item.lowest_price and float(item.current_price) <= float(item.lowest_price):
                    # Notify user
                    msg = f"📉 Price dropped for {item.title}! Now ₹{item.current_price} (lowest: ₹{item.lowest_price})"
                    # If user_id looks numeric (telegram), notify via telegram, else treat as whatsapp phone
                    if str(item.user_id).isdigit():
                        notify_telegram_chat(item.user_id, msg, item.affiliate_url)
                    else:
                        notify_whatsapp(item.user_id, msg, item.affiliate_url)
        except Exception as e:
            print("Error checking item", it.id, e)

# Helper to get all items (direct DB query here to avoid circular imports)
from db import SessionLocal, TrackedItem
def list_tracked_items_all():
    db = SessionLocal()
    try:
        return db.query(TrackedItem).all()
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(check_all_prices, 'interval', minutes=INTERVAL_MINUTES, id='price_check', replace_existing=True)
    scheduler.start()
    print(f"Scheduler started. Checking every {INTERVAL_MINUTES} minutes.")

def stop_scheduler():
    scheduler.shutdown(wait=False)'''