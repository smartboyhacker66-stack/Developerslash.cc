import os
import asyncio
from aiohttp import web
from serpapi import GoogleSearch
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

ASK_DATE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "हे यूजर मैं एक एआई एजेंट हूं मुझे बनाया है अमन शेख ने\n"
        "कॉपीराइट 2026 अमन शेख ब्लाइंड इंडियन टेक सपोर्ट टीम भविष्य तक"
    )
    keyboard = [[InlineKeyboardButton("अपडेट रिसर्च", callback_data="ask_date")]]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def ask_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📅 कृपया तारीख दर्ज करें (जैसे: 24 Oct 2026 या YYYY-MM-DD):")
    return ASK_DATE

def fetch_date_data(date_str: str):
    report = f"📊 **शेयर मार्केट अपडेट ({date_str})**\n\n"
    try:
        search = GoogleSearch({
            "q": f"Indian share market news on {date_str}",
            "tbm": "nws",
            "api_key": SERPAPI_KEY,
            "num": 3
        })
        results = search.get_dict().get("news_results", [])
        if not results:
            return f"❌ {date_str} के लिए कोई मार्केट न्यूज़ नहीं मिली।"
        for item in results[:3]:
            report += f"• {item.get('title')}\n🔗 {item.get('link')}\n\n"
    except Exception as e:
        report += f"डेटा लोड करने में त्रुटि: {e}"
    return report

async def handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_str = update.message.text
    msg = await update.message.reply_text(f"🔍 {date_str} का डेटा सर्च हो रहा है...")
    loop = asyncio.get_running_loop()
    report = await loop.run_in_executor(None, fetch_date_data, date_str)
    keyboard = [[InlineKeyboardButton("अपडेट रिसर्च", callback_data="ask_date")]]
    await msg.edit_text(report, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("प्रक्रिया रद्द कर दी गई है।")
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
        entry_points=[CallbackQueryHandler(ask_date_callback, pattern="^ask_date$")],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(conv_handler)

    async with bot_app:
        await bot_app.start()
        await bot_app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
