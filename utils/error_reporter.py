import traceback
from datetime import datetime, timezone

async def notify_admin(app, title, exc=None, details=None):
    """Send a compact diagnostic report to ADMIN_ID; never include environment secrets."""
    from config import config
    from utils.logger import get_logger
    log = get_logger("ErrorReporter")
    if exc is not None:
        body = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    else:
        body = details or ""
    body = body[-12000:]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    message = f"🚨 {title}\n🕒 {stamp}\n\n```text\n{body or 'No traceback available'}\n```"
    try:
        await app.bot.send_message(chat_id=config.ADMIN_ID, text=message[:3900], parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        log.exception("Could not send diagnostic message to admin")
