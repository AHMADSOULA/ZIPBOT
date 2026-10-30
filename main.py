from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import config
from bot import handlers
from database.db import init_db
from utils.logger import get_logger
from utils.helpers import extract_urls
from utils.error_reporter import notify_admin

log = get_logger("Main")

async def post_init(app):
    await init_db()
    from database import db
    await db.register_user(config.ADMIN_ID, "ADMIN")
    log.info("Bot startup completed")
    try:
        await app.bot.send_message(chat_id=config.ADMIN_ID, text="🟢 البوت بدأ التشغيل على الاستضافة.")
    except Exception:
        log.exception("Startup notification failed")

async def post_stop(app):
    log.warning("Bot stopped gracefully")
    try:
        await app.bot.send_message(chat_id=config.ADMIN_ID, text="🟠 البوت توقف بشكل طبيعي على الاستضافة.")
    except Exception:
        log.exception("Shutdown notification failed")

async def error_handler(update, context):
    err = context.error
    log.error("Unhandled Telegram update exception", exc_info=(type(err), err, err.__traceback__) if err else None)
    await notify_admin(context.application, "خطأ غير معالج داخل البوت", exc=err)

async def route_text(update, context):
    text = update.message.text or ""
    if await handlers.handle_admin_input(update, context, text):
        return
    if extract_urls(text):
        await handlers.handle_url(update, context)
        return
    await update.message.reply_text("ℹ️ أرسل /start للبدء.")

def main():
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it in Fly.io Secrets.")
    app = (Application.builder().token(config.BOT_TOKEN).post_init(post_init).post_stop(post_stop).build())
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.help_cmd))
    app.add_handler(CommandHandler("status", handlers.status_cmd))
    app.add_handler(CommandHandler("cancel", handlers.cancel_cmd))
    app.add_handler(CommandHandler("request", handlers.request_cmd))
    app.add_handler(CallbackQueryHandler(handlers.button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))
    log.info("Starting Telegram polling")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
