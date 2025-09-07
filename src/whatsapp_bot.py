from fastapi import APIRouter, Request
import os
import requests
from src.affiliate import get_product_by_url
import src.db

router = APIRouter()
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

@router.get("/webhook")
async def verify(req: Request):
    params = req.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return "Error: verification failed"

@router.post("/webhook")
async def webhook(req: Request):
    body = await req.json()
    # Minimal defensive parsing of WhatsApp incoming messages
    try:
        entries = body.get("entry", [])
        for e in entries:
            for change in e.get("changes", []):
                val = change.get("value", {})
                messages = val.get("messages", [])
                for m in messages:
                    from_num = m.get("from")
                    text = m.get("text", {}).get("body", "")
                    if not text:
                        continue
                    # If user sent a link, track it
                    if text.startswith("http"):
                        p = get_product_by_url(text)
                        item = db.add_tracked_item(user_id=from_num, platform=p.get("platform"),
                                                   product_id=p.get("product_id"), title=p.get("title"),
                                                   image_url=p.get("image"), affiliate_url=p.get("affiliate_url"),
                                                   price=p.get("price"))
                        send_whatsapp_message(from_num, f"✅ Tracking started: {p.get('title')}\n💰 ₹{p.get('price')}", p.get("affiliate_url"))
    except Exception as e:
        print("Error processing whatsapp webhook:", e)
    return {"status": "ok"}

def send_whatsapp_message(to, text, url=None):
    if not WHATSAPP_TOKEN or not PHONE_ID:
        print("WhatsApp credentials missing - cannot send message.")
        return
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        # We'll use a simple text message fallback if template not configured
        "text": {"body": text}
    }
    # If an affiliate URL is present, also send an interactive button message
    if url:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text},
                "action": {"buttons": [{"type": "url", "url": url, "title": "🛒 Buy Now"}]}
            }
        }
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    resp = requests.post(f"https://graph.facebook.com/v17.0/{PHONE_ID}/messages", headers=headers, json=payload)
    if resp.status_code >= 300:
        print("WhatsApp send failed:", resp.status_code, resp.text)