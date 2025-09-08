import os
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from src.db import init_db
from src.tracker import start_scheduler, stop_scheduler
from src.whatsapp_bot import router as whatsapp_router
from src.admin import admin_router

app = FastAPI(title="PriceLens Bot")

app.include_router(whatsapp_router, prefix="/whatsapp")
app.include_router(admin_router, prefix="/admin")


@app.on_event("startup")
async def on_startup():
    init_db()
    # start the scheduler
    start_scheduler()
    # start telegram bot as background asyncio task
    from src.telegram_bot import start_telegram_bot
    asyncio.create_task(start_telegram_bot())


@app.on_event("shutdown")
async def on_shutdown():
    stop_scheduler()


@app.get("/")
async def root():
    return {"message": "PriceLens Bot backend running"}