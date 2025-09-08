import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from src.affiliate import get_product_by_url
from src.db import get_session, User, Product
import datetime
import asyncio

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

logger = logging.getLogger("telegram_bot")
logging.basicConfig(level=logging.INFO)

async def _reply_start(update: Update):
    text = (
        "🎉 Great to see you! Welcome!\n\n"
        "=> I am PriceLens — a Price Tracker & Alert Bot.\n"
        "=> Send a product URL (Amazon / Flipkart / Ajio / Shopsy) and I'll track price changes and alert you.\n\n"
        "Save Time! Save Money!!\n\nClick /help to get more help."
    )
    await update.message.reply_text(text)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _reply_start(update)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/track <url>  - start tracking (or just send URL)\n"
        "/list - list tracked products\n"
        "/stop - stop all tracking\n"
        "/stop_<product_id> - stop specific item\n"
        "/demovideo - demo link\n"        )
    await update.message.reply_text(text)

async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Send a product URL or use /track <url>")
        return
    url = args[0].strip()
    await handle_new_tracking(update.effective_user, "telegram", url, update)

async def handle_new_tracking(user_obj, platform, url, update_obj=None, reply_func=None):
    try:
        pinfo = get_product_by_url(url)
    except Exception as e:
        text = f"Failed to fetch product details: {e}"
        if update_obj:
            await update_obj.message.reply_text(text)
        return

    uid = str(user_obj.id) if platform == "telegram" else str(user_obj)
    with get_session() as s:
        u = s.query(User).filter(User.user_id == uid, User.platform == platform).first()
        if not u:
            u = User(user_id=uid, name=(user_obj.full_name if platform=="telegram" else uid), platform=platform)
            s.add(u); s.commit()
        pr = Product(
            product_id = pinfo.get("product_id"),
            user_id = uid,
            url = url,
            platform = pinfo.get("platform"),
            product_name = pinfo.get("title"),
            image_url = pinfo.get("image"),
            current_price = pinfo.get("price"),
            prev_price = None,
            lowest_price = pinfo.get("price"),
            highest_price = pinfo.get("price"),
            affiliate_link = pinfo.get("affiliate_link"),
            last_checked = datetime.datetime.utcnow(),
            tracking_status = "active"
        )
        s.add(pr); s.commit(); s.refresh(pr)

        buy_btn = InlineKeyboardButton("🛒 Buy Now", url=pr.affiliate_link or pr.url)
        stop_btn = InlineKeyboardButton("🔴 Stop Tracking", callback_data=f"stop:{pr.id}")
        list_btn = InlineKeyboardButton("📋 Tracked Items", callback_data="list")
        deals_btn = InlineKeyboardButton("🛍️ Today's Deals", callback_data="deals")
        kb = InlineKeyboardMarkup([[buy_btn],[stop_btn, list_btn, deals_btn]])
        msg = (
            f"✅ Tracking started!\n\n"
            f"{pr.product_name}\n\n"
            f"Current Price: ₹{pr.current_price if pr.current_price is not None else 'N/A'}\n\n"
            f"Click here to open: {pr.affiliate_link or pr.url}\n\n"
            f"⏱ Updated at [{pr.last_checked.strftime('%d %b %Y, %H:%M')}]\n\n"
            "😉 I've started tracking this product. I will send you an alert when the price changes!"
        )
        if pr.image_url:
            await update_obj.message.reply_photo(photo=pr.image_url, caption=msg, reply_markup=kb)
        else:
            await update_obj.message.reply_text(msg, reply_markup=kb)

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    with get_session() as s:
        prods = s.query(Product).filter(Product.user_id==uid, Product.tracking_status=="active").all()
        if not prods:
            await update.message.reply_text("You have no tracked items. Send a product URL to start.")
            return
        total = 0
        for p in prods:
            total += 1
            stop_cb = InlineKeyboardButton("🔴 Stop Tracking", callback_data=f"stop:{p.id}")
            buy_cb = InlineKeyboardButton("🛒 Buy Now", url=p.affiliate_link or p.url)
            kb = InlineKeyboardMarkup([[buy_cb],[stop_cb]])
            text = f"{total}. {p.product_name}\nClick here: {p.affiliate_link or p.url}\nID: {p.id}\nCurrent: ₹{p.current_price}"
            if p.image_url:
                await update.message.reply_photo(photo=p.image_url, caption=text, reply_markup=kb)
            else:
                await update.message.reply_text(text, reply_markup=kb)
        await update.message.reply_text(f"🦋 Total Products: {total}")

async def stop_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    with get_session() as s:
        s.query(Product).filter(Product.user_id==uid).update({"tracking_status":"stopped"})
        s.commit()
    await update.message.reply_text("Stopped tracking all your items.")

async def stop_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("stop:"):
        pid = int(data.split(":",1)[1])
        with get_session() as s:
            p = s.query(Product).filter(Product.id==pid).first()
            if not p:
                await query.edit_message_text("Item not found.")
                return
            p.tracking_status = "stopped"
            s.add(p); s.commit()
            await query.edit_message_text(f"Stopped tracking item {pid}")

async def list_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await list_command(update, context)

async def deals_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_session() as s:
        promos = s.query(Product).filter(Product.tracking_status=="active").limit(5).all()
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Today's deals will be here (admin feature).")


async def track_by_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text.startswith("http"):
        await handle_new_tracking(update.effective_user, "telegram", text, update)

async def start_telegram_bot():
    if not TELEGRAM_TOKEN:
        logger.warning("TELEGRAM token missing. Telegram functions disabled.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("track", track_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("stop", stop_all_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), track_by_message))
    app.add_handler(CallbackQueryHandler(stop_callback_handler, pattern=r"^stop:"))
    app.add_handler(CallbackQueryHandler(list_callback_handler, pattern=r"^list$"))
    app.add_handler(CallbackQueryHandler(deals_callback_handler, pattern=r"^deals$"))

    logger.info("Telegram polling started")

    # Instead of run_polling()
    await app.initialize()
    await app.start()
    asyncio.create_task(app.updater.start_polling())
