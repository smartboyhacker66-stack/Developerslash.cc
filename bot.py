import os
import asyncio
from aiohttp import web
from serpapi import GoogleSearch
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

ASK_DATE, ASK_TOPIC_QUERY, ASK_TOPIC_DATE = range(3)

WELCOME_TEXT = (
    "Hey there! I’m Rashmi, your personal Share Market Research AI.\n"
    "Built by Aman Shaikh & BITS so you can chill while I track the market to save your portfolio from mini heart attacks! 📈\n\n"
    "🚨 Got an error or need help? Contact Developer Aman Shaikh directly at: https://t.me/BlindTechSupportIN\n\n"
    "© 2026 Aman Shaikh | Blind Indian Tech Support (BITS)"
)

VERSION_TEXT = (
    "📌 Rashmi AI — Version 1.2 Update Notes\n"
    "Released by Aman Shaikh & the BITS Team (Upgraded from v1.1).\n\n"
    "What's New & Fixed in v1.2:\n"
    "• Full English Interface: Complete switch to English queries and news retrieval.\n"
    "• Targeted Topic Research: Custom search support for specific stocks, IPOs, and sectors.\n"
    "• Markdown & Link Fixes: Improved readability and bug fixes for web endpoints.\n"
    "• Engine Stability: Upgraded server lifecycle management for faster responses."
)

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 General Market Update", callback_data="general_date")],
        [InlineKeyboardButton("🔍 Topic Research", callback_data="start_topic")],
        [InlineKeyboardButton("ℹ️ Version 1.2 Info", callback_data="show_version")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=get_main_keyboard(), disable_web_page_preview=True)

async def version_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(VERSION_TEXT, reply_markup=get_main_keyboard())

async def ask_general_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📅 Please enter the date (e.g., 24 Oct 2026 or YYYY-MM-DD):")
    return ASK_DATE

def fetch_market_news(query_term: str):
    report = f"📊 Research Results for: {query_term}\n\n"
    try:
        search = GoogleSearch({
            "q": query_term,
            "tbm": "nws",
            "api_key": SERPAPI_KEY,
            "num": 3
        })
        results = search.get_dict().get("news_results", [])
        if not results:
            return f"❌ No market news found for '{query_term}'."
        for item in results[:3]:
            title = item.get("title", "No Title")
            link = item.get("link", "")
            report += f"• {title}\n🔗 {link}\n\n"
    except Exception as e:
        report += f"Error loading data: {e}"
    return report

async def handle_general_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text
    msg = await update.message.reply_text(f"🔍 Searching market news for {date_str}...")
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, fetch_market_news, f"Indian share market news on {date_str}")
    await msg.edit_text(report, reply_markup=get_main_keyboard(), disable_web_page_preview=True)
    return ConversationHandler.END

async def ask_topic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🎯 Enter the specific topic or stock name (e.g., Jio IPO, Tata Motors):")
    return ASK_TOPIC_QUERY

async def handle_topic_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["topic"] = update.message.text
    await update.message.reply_text(f"📅 Now enter the date for '{context.user_data['topic']}':")
    return ASK_TOPIC_DATE

async def handle_topic_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = context.user_data.get("topic", "Market")
    date_str = update.message.text
    msg = await update.message.reply_text(f"🔍 Searching research for {topic} on {date_str}...")
    query_str = f"{topic} Indian share market news {date_str}"
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, fetch_market_news, query_str)
    await msg.edit_text(report, reply_markup=get_main_keyboard(), disable_web_page_preview=True)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.", reply_markup=get_main_keyboard())
    return ConversationHandler.END

async def health_check(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    bot_app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ask_general_date_callback, pattern="^general_date$"),
            CallbackQueryHandler(ask_topic_callback, pattern="^start_topic$")
        ],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_general_date_input)],
            ASK_TOPIC_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topic_input)],
            ASK_TOPIC_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topic_date_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(version_callback, pattern="^show_version$"))
    bot_app.add_handler(conv_handler)

    try:
        async with bot_app:
            await bot_app.start()
            await bot_app.updater.start_polling()
            await asyncio.Event().wait()
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
