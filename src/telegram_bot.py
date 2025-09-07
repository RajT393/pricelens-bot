import os
import threading
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from src.affiliate import get_product_by_url
import src.db

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_TOKEN:
    print("Warning: TELEGRAM_BOT_TOKEN is not set. Telegram functionality will not start until you set it in .env")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        """👋 Welcome to Pricelens Bot! Use /track <product-link> to start tracking.
Commands: /track, /list, /stop <id>"""
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n/track <url> - start tracking a product\n/list - list your tracked items\n/stop <id> - stop tracking an item"
    )


async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Please supply a product link. Example: /track https://www.amazon.in/...")
        return
    url = args[0].strip()
    data = get_product_by_url(url)
    item = db.add_tracked_item(
        user_id=update.effective_user.id,
        platform=data.get("platform"),
        product_id=data.get("product_id"),
        title=data.get("title"),
        image_url=data.get("image"),
        affiliate_url=data.get("affiliate_url"),
        price=data.get("price")
    )
    buttons = [[InlineKeyboardButton("🛒 Buy Now", url=data.get("affiliate_url"))]]
    reply_markup = InlineKeyboardMarkup(buttons)
    caption = f"✅ Tracking started: {data.get('title')}\n💰 Current: ₹{data.get('price')}\nID: {item.id}"
    if data.get("image"):
        await update.message.reply_photo(photo=data.get("image"), caption=caption, reply_markup=reply_markup)
    else:
        await update.message.reply_text(caption, reply_markup=reply_markup)


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = db.list_tracked_items(update.effective_user.id)
    if not items:
        await update.message.reply_text("You have no tracked items. Use /track <url> to add.")
        return
    messages = []
    for it in items:
        messages.append(f"ID: {it.id} | {it.title}\nCurrent: ₹{it.current_price} | Lowest: ₹{it.lowest_price} | Highest: ₹{it.highest_price}")
    text = "\n\n".join(messages)
    await update.message.reply_text(text)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /stop <item-id>")
        return
    item_id = args[0]
    ok = db.remove_tracked_item(update.effective_user.id, item_id)
    if ok:
        await update.message.reply_text(f"Stopped tracking item {item_id}")
    else:
        await update.message.reply_text(f"No item with ID {item_id} found in your list.")


async def track_by_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # If user sends a plain link, try to track it automatically
    text = update.message.text.strip()
    if text.startswith("http"):
        # emulate /track
        context.args = [text]
        await track_command(update, context)


def run_telegram():
    if not TELEGRAM_TOKEN:
        print("Telegram token missing - skipping telegram startup.")
        return
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("track", track_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("stop", stop_command))
    # optional: handle plain links sent by user
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_by_message))
    print("Starting Telegram polling...")
    app.run_polling()


def run_telegram_in_thread():
    t = threading.Thread(target=run_telegram, daemon=True)
    t.start()