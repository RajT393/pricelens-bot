from fastapi import FastAPI
import asyncio
from src.telegram_bot import start_telegram_bot
from src.whatsapp_bot import router as whatsapp_router
from src.db import init_db
from src.tracker import start_scheduler, stop_scheduler

app = FastAPI(title="Pricelens Bot")

# Include WhatsApp webhook
app.include_router(whatsapp_router, prefix="/whatsapp")

@app.on_event("startup")
async def startup_event():
    init_db()
    # start Telegram bot in background
    asyncio.create_task(start_telegram_bot())
    # start price tracking scheduler
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()

@app.get("/")
async def root():
    return {"message": "Pricelens Bot backend running"}

'''import os
import threading
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
from src.whatsapp_bot import router as whatsapp_router
from src.telegram_bot import run_telegram_in_thread
#from telegram_bot import run_telegram_in_thread, TELEGRAM_TOKEN
from src.tracker import start_scheduler, stop_scheduler
from src.db import init_db


app = FastAPI(title="Pricelens Bot")

app.include_router(whatsapp_router, prefix="/whatsapp")

@app.on_event("startup")
async def startup_event():
    # initialize DB
    init_db()
    # start telegram bot in background thread (polling)
    run_telegram_in_thread()
    # start background scheduler
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()

@app.get("/")
async def root():
    return {"message": "Pricelens Bot backend running"}'''