# Pricelens Bot - Price Tracker (Telegram + WhatsApp ready)

**What this package contains**
- A single Python project (FastAPI backend) that:
  - Runs a Telegram bot (polling) for `/track`, `/list`, `/stop` commands.
  - Exposes a WhatsApp Cloud API webhook endpoint to accept product links.
  - Uses Amazon Product Advertising API & Flipkart Affiliate API *if credentials are provided*.
  - Defaults to a local SQLite database (data/pricelens.db) so you can run immediately.
  - A scheduled price-checker (APScheduler) that notifies users on price drops.

**Important**
- Official APIs (Amazon PA-API and Flipkart affiliate) are preferred. If you do not supply keys,
  the bot runs in *demo mode* and returns sample product data. This avoids scraping.
- Before deploying publicly, obtain and configure the affiliate/API keys so actual prices and
  affiliate links are used.

## Quick start (local testing)
1. Unzip the package:
   ```bash
   unzip pricelens-bot.zip
   cd pricelens-bot
   ```

2. Create and edit `.env`:
   ```bash
   cp .env.example .env
   # edit .env and paste your credentials and tokens
   ```

3. Create a virtualenv and install:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Run the app (development):
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   - Telegram bot will start in background (polling).
   - WhatsApp webhook endpoints are at `POST /whatsapp/webhook` and `GET /whatsapp/webhook` for verification.

5. Try Telegram:
   - Open Telegram and talk to your bot (use the token you configured).
   - Commands:
     - `/start` - welcome
     - `/track <product-url>` - start tracking
     - `/list` - list your tracked items
     - `/stop <item-id>` - stop tracking an item

6. WhatsApp:
   - Set the webhook URL on the Meta for Developers dashboard to:
     `https://<your-deployment-url>/whatsapp/webhook`
   - Use the verify token you put into `.env`.

## Deploying
- Push to GitHub and connect to Render / Railway / Fly / Supabase Edge Functions.
- If using Render / Railway, set the start command to:
  ```
  uvicorn src.main:app --host 0.0.0.0 --port $PORT
  ```
- Add environment variables in the host's dashboard (copy from `.env`).
- Make sure port and webhooks are reachable (https).

## How this package handles affiliate links
- If you set `AMAZON_ASSOCIATE_TAG`, the package will append the tag to product URLs returned by the internal helper.
- If you set Flipkart credentials, Flipkart affiliate link parameters will be appended similarly.
- For full production reliability, you should integrate the official Amazon PA-API (see `src/affiliate.py` where placeholders are included).

## Next steps after download (step-by-step)
1. Fill `.env` with your real tokens and affiliate IDs.
2. Install dependencies.
3. Run locally and test flows on Telegram. Test WhatsApp with the Cloud API test number and webhook.
4. Once stable, push to GitHub and deploy to Render/Railway and set environment variables there.
5. Monitor affiliate dashboards (Amazon Associates / Flipkart Affiliate) for earnings.

## Notes & Caveats
- This project defaults to using a local SQLite DB for simplicity and immediate testing.
- For production, use Supabase/Postgres or any managed Postgres. Set `DATABASE_URL` env var.
- This package intentionally avoids scraping as primary; scraping modules can be added later as a fallback.