#!/usr/bin/env python3
"""
Main bot: wires together config, signals, charts, subscription, and runs Telegram handlers.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

# load env
load_dotenv()

from config import settings
from subscription import SubscriptionManager
from signals import SignalEngine
from charts import make_candlestick
from utils import format_signal_text

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# initialize managers
sub_mgr = SubscriptionManager(settings.USERS_DB_PATH)
sig_engine = SignalEngine(settings.TWELVE_DATA_API_KEY)

# keyboards
def main_menu():
    kb = [
        [InlineKeyboardButton("🤖 Get AI Signal", callback_data="menu_signal")],
        [InlineKeyboardButton("📈 Chart", callback_data="menu_chart")],
        [InlineKeyboardButton("💎 Plans & Subscribe", callback_data="menu_plans")],
        [InlineKeyboardButton("ℹ️ My Status", callback_data="menu_status")],
    ]
    return InlineKeyboardMarkup(kb)

def plans_kb():
    kb = []
    for k,v in sub_mgr.PLANS.items():
        kb.append([InlineKeyboardButton(f"{k} — {v['days']}d — {v['price']}", callback_data=f"buy_{k}")])
    kb.append([InlineKeyboardButton("⬅ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(kb)

def quick_pairs_kb():
    pairs = ["EURUSD","GBPUSD","USDJPY","AUDUSD","NZDUSD"]
    kb = [[InlineKeyboardButton(p[:3] + "/" + p[3:], callback_data=f"pair_{p}") ] for p in pairs]
    kb.append([InlineKeyboardButton("⬅ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(kb)

# handlers
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    sub_mgr.ensure_user(user.id, user.username)
    update.message.reply_text(
        f"Hello {user.first_name or user.username}! Welcome to Pro Forex Bot.\nYour 3-day trial is active.",
        reply_markup=main_menu()
    )

def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    uid = query.from_user.id

    if query.data == "menu_signal":
        if not sub_mgr.is_active(uid):
            query.edit_message_text("⛔ Trial expired. Please subscribe for continued access.", reply_markup=plans_kb())
            return
        query.edit_message_text("Choose quick pair or send pair like EUR/USD:", reply_markup=quick_pairs_kb())

    elif query.data == "menu_chart":
        if not sub_mgr.is_active(uid):
            query.edit_message_text("⛔ Trial expired. Please subscribe.", reply_markup=plans_kb())
            return
        query.edit_message_text("Choose quick pair or send pair like EUR/USD:", reply_markup=quick_pairs_kb())

    elif query.data == "menu_plans":
        query.edit_message_text("Choose a plan:", reply_markup=plans_kb())

    elif query.data.startswith("buy_"):
        plan = query.data.split("_",1)[1]
        detail = sub_mgr.PLANS.get(plan)
        msg = (
            f"You selected *{plan}* — {detail['days']} days — {detail['price']}.\n\n"
            f"Pay using:\n• PayPal: `{settings.PAYPAL_EMAIL}`\n• M-Pesa: `{settings.MPESA_PHONE}`\n• Binance BNB: `{settings.BINANCE_BNB}`\n• Binance USDT: `{settings.BINANCE_USDT}`\n\nAfter payment press *I Paid — Notify Admin*."
        )
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ I Paid — Notify Admin", callback_data=f"notify_{plan}")],
            [InlineKeyboardButton("⬅ Back", callback_data="menu_plans")]
        ])
        query.edit_message_text(msg, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

    elif query.data.startswith("notify_"):
        plan = query.data.split("_",1)[1]
        admin_msg = f"📣 Payment notification: @{query.from_user.username} ({query.from_user.id}) requests activation for *{plan}*."
        context.bot.send_message(chat_id=settings.ADMIN_TELEGRAM_ID, text=admin_msg, parse_mode=ParseMode.MARKDOWN)
        query.edit_message_text("✅ Notified admin. Wait for approval.")

    elif query.data == "menu_status":
        txt = sub_mgr.status_text(uid)
        query.edit_message_text(txt)

    elif query.data == "menu_back":
        query.edit_message_text("Back to menu", reply_markup=main_menu())

    elif query.data.startswith("pair_"):
        raw = query.data.split("_",1)[1]
        pair = raw[:3] + "/" + raw[3:]
        # produce both signal + chart
        sig = sig_engine.predict_next(pair)
        if not sig:
            query.edit_message_text("Unable to fetch/generate signal now. Try again shortly.")
            return
        df = sig_engine.fetch_ohlc(pair, interval='1min', outputsize=80)
        chart = make_candlestick(df, pair, sig['signal'], sig['entry'], sig['stop'], sig['tp'])
        context.bot.send_photo(chat_id=uid, photo=chart, caption=format_signal_text(sig))
        query.edit_message_text("Signal sent.", reply_markup=main_menu())

def text_handler(update: Update, context: CallbackContext):
    txt = update.message.text.strip().upper()
    uid = update.message.from_user.id
    if "/" in txt or len(txt) >= 6:
        pair = txt if "/" in txt else (txt[:3] + "/" + txt[3:])
        if not sub_mgr.is_active(uid):
            update.message.reply_text("⛔ Trial/Subscription expired. Please upgrade.", reply_markup=plans_kb())
            return
        sig = sig_engine.predict_next(pair)
        if not sig:
            update.message.reply_text("No reliable signal now. Try later.")
            return
        df = sig_engine.fetch_ohlc(pair, interval='1min', outputsize=80)
        chart = make_candlestick(df, pair, sig['signal'], sig['entry'], sig['stop'], sig['tp'])
        update.message.reply_photo(photo=chart, caption=format_signal_text(sig), parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text("Send pair like EUR/USD or use the menu.", reply_markup=main_menu())

# admin command to approve
def activate(update: Update, context: CallbackContext):
    if update.effective_user.id != settings.ADMIN_TELEGRAM_ID:
        update.message.reply_text("⛔ Only admin can use this.")
        return
    try:
        target = int(context.args[0])
        plan = context.args[1]
        sub_mgr.activate_plan(target, plan)
        update.message.reply_text(f"✅ Activated user {target} for plan {plan}.")
        context.bot.send_message(chat_id=target, text=f"🎉 Your {plan} subscription has been activated by admin.")
    except Exception as e:
        update.message.reply_text("Usage: /activate <user_id> <PlanKey>")

def main():
    token = settings.TELEGRAM_BOT_TOKEN
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))
    dp.add_handler(CommandHandler("activate", activate))

    logger.info("Bot starting (polling)...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()