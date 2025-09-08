# PriceLens - Price Tracker Bot (Telegram + WhatsApp)

This package is a ready-to-run PriceLens bot that scrapes product pages (Amazon/Flipkart etc.)
to track prices and send immediate alerts to users on price changes. It automatically uses
official APIs if you provide keys (Amazon PA-API / Flipkart) and falls back to scraping otherwise.

## What's included
- FastAPI backend
- Telegram bot (python-telegram-bot, polling)
- WhatsApp webhook (Meta Cloud API) integration
- Scrapers for Amazon and Flipkart (BeautifulSoup)
- PostgreSQL (Supabase) via SQLAlchemy
- APScheduler price checker that notifies users immediately on price change
- Admin endpoint to broadcast promotions

## Quick start (Windows 11)
1. Install Python 3.10+ and Git.
2. Unzip this project and open PowerShell in the project root.
3. Create virtualenv and install deps:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill values (DATABASE_URL and TELEGRAM_BOT_TOKEN are required to run).
5. Run the app:
   ```powershell
   uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
   ```
6. Open Telegram, start your bot, send a product URL to track.

## Deploying
- Recommended: use Supabase (Postgres) for DATABASE_URL, Railway or Render for hosting.
- Set environment variables in the host dashboard and deploy from GitHub.

## Affiliate links
- Add your Amazon Associate Tag in `.env` as AMAZON_ASSOCIATE_TAG.
- Add your Flipkart affiliate ID as FLIPKART_AFFILIATE_ID.
- The bot will append your tags to "Buy Now" links automatically.

## Notes
- Amazon PA-API access requires 3 qualifying sales in 180 days; until then the bot will use scraping.
- For WhatsApp webhook testing, use ngrok to expose your local server and set webhook URL in Meta app.