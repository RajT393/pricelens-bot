import os
import logging
import requests
from fastapi import APIRouter, Request, Response
from src.affiliate import get_product_by_url
from src.db import get_session, User, Product
import datetime

router = APIRouter()
logger = logging.getLogger("whatsapp_bot")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "pricelens_verify_token")
BASE_URL = "https://graph.facebook.com/v17.0"

def send_whatsapp_message(to: str, text: str, button_url: str = None, image_url: str = None):
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID):
        logger.warning("WhatsApp credentials missing.")
        return False
    endpoint = f"{BASE_URL}/{WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    if button_url:
        payload = {
            "messaging_product":"whatsapp",
            "to": to,
            "type":"interactive",
            "interactive":{
                "type":"button",
                "body":{"text": text},
                "action":{"buttons":[{"type":"url","url":button_url,"title":"🛒 Buy Now"}]}
            }
        }
    else:
        payload = {"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":text}}
    if image_url and not button_url:
        img_payload = {"messaging_product":"whatsapp","to":to,"type":"image","image":{"link":image_url}}
        requests.post(endpoint, headers=headers, json=img_payload, timeout=10)
    r = requests.post(endpoint, headers=headers, json=payload, timeout=10)
    return r.status_code < 300

@router.get("/webhook")
async def webhook_verify(req: Request):
    params = req.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge)
    return Response(content="Invalid verification", status_code=400)

@router.post("/webhook")
async def whatsapp_incoming(req: Request):
    body = await req.json()
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
                    text = text.strip()
                    if text.lower().startswith("/track"):
                        parts = text.split()
                        if len(parts) < 2:
                            send_whatsapp_message(from_num, "Send /track <url>")
                            continue
                        url = parts[1]
                        try:
                            pinfo = get_product_by_url(url)
                        except Exception as e:
                            send_whatsapp_message(from_num, f"Failed to fetch: {e}")
                            continue
                        with get_session() as s:
                            u = s.query(User).filter(User.user_id==from_num, User.platform=="whatsapp").first()
                            if not u:
                                u = User(user_id=from_num, name=from_num, platform="whatsapp"); s.add(u); s.commit()
                            pr = Product(product_id=pinfo.get("product_id"), user_id=from_num, url=url, platform=pinfo.get("platform"),
                                         product_name=pinfo.get("title"), image_url=pinfo.get("image"), current_price=pinfo.get("price"),
                                         prev_price=None, lowest_price=pinfo.get("price"), highest_price=pinfo.get("price"),
                                         affiliate_link=pinfo.get("affiliate_link"), last_checked=datetime.datetime.utcnow(), tracking_status="active")
                            s.add(pr); s.commit(); s.refresh(pr)
                            send_whatsapp_message(from_num, f"✅ Tracking started: {pr.product_name}\nCurrent Price: ₹{pr.current_price}\nID:{pr.id}", pr.affiliate_link, pr.image_url)
                    elif text.lower().startswith("/list"):
                        with get_session() as s:
                            prods = s.query(Product).filter(Product.user_id==from_num, Product.tracking_status=="active").all()
                            if not prods:
                                send_whatsapp_message(from_num, "No tracked items. Send /track <url>")
                                continue
                            for p in prods:
                                send_whatsapp_message(from_num, f"ID:{p.id} | {p.product_name}\n₹{p.current_price}", p.affiliate_link, p.image_url)
                    elif text.lower().startswith("/stop"):
                        parts = text.split()
                        if len(parts) < 2:
                            send_whatsapp_message(from_num, "Usage: /stop <id>")
                            continue
                        pid = int(parts[1])
                        with get_session() as s:
                            p = s.query(Product).filter(Product.id==pid, Product.user_id==from_num).first()
                            if not p:
                                send_whatsapp_message(from_num, "Item not found.")
                                continue
                            p.tracking_status = "stopped"; s.add(p); s.commit()
                            send_whatsapp_message(from_num, f"Stopped tracking item {pid}")
                    else:
                        if text.startswith("http"):
                            try:
                                pinfo = get_product_by_url(text)
                            except Exception as e:
                                send_whatsapp_message(from_num, f"Failed to fetch: {e}")
                                continue
                            with get_session() as s:
                                u = s.query(User).filter(User.user_id==from_num, User.platform=="whatsapp").first()
                                if not u:
                                    u = User(user_id=from_num, name=from_num, platform="whatsapp"); s.add(u); s.commit()
                                pr = Product(product_id=pinfo.get("product_id"), user_id=from_num, url=text, platform=pinfo.get("platform"),
                                             product_name=pinfo.get("title"), image_url=pinfo.get("image"), current_price=pinfo.get("price"),
                                             prev_price=None, lowest_price=pinfo.get("price"), highest_price=pinfo.get("price"),
                                             affiliate_link=pinfo.get("affiliate_link"), last_checked=datetime.datetime.utcnow(), tracking_status="active")
                                s.add(pr); s.commit(); s.refresh(pr)
                                send_whatsapp_message(from_num, f"✅ Tracking started: {pr.product_name}\nCurrent Price: ₹{pr.current_price}\nID:{pr.id}", pr.affiliate_link, pr.image_url)
                        else:
                            send_whatsapp_message(from_num, "Commands: /track <url> | /list | /stop <id>")
    except Exception as e:
        logger.exception("Error in whatsapp webhook: %s", e)
    return {"status": "ok"}