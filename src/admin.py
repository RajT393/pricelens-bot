from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from src.db import get_session, Promotion, User
from src.tracker import send_telegram_message, send_whatsapp_message
import os

admin_router = APIRouter()
ADMIN_TOKEN = os.getenv("ADMIN_TELEGRAM_ID")

class PromoSchema(BaseModel):
    title: str
    message: str
    link: str = None
    platform: str = None
    area_code: str = None
    active: bool = True

@admin_router.post("/promotions")
async def create_promo(payload: PromoSchema, req: Request):
    token = req.headers.get("x-admin-token")
    if not token or token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    with get_session() as s:
        promo = Promotion(title=payload.title, message=payload.message, link=payload.link,
                          platform=payload.platform, area_code=payload.area_code, active=payload.active)
        s.add(promo); s.commit(); s.refresh(promo)
        if promo.active:
            q = s.query(User)
            if promo.platform:
                q = q.filter(User.platform == promo.platform)
            if promo.area_code:
                q = q.filter(User.location_area_code == promo.area_code)
            users = q.all()
            for u in users:
                if u.platform == "telegram":
                    send_telegram_message(u.user_id, f"🎉 {promo.title}\n\n{promo.message}\n{promo.link or ''}")
                else:
                    send_whatsapp_message(u.user_id, f"🎉 {promo.title}\n\n{promo.message}\n{promo.link or ''}")
        return {"status": "ok", "promo_id": promo.id}