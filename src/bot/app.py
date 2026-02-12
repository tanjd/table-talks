"""Application building and lifecycle management."""

import asyncio
import logging
from typing import Any

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from .constants import (
    BOT_SECRET_KEY,
    CALLBACK_END_SESSION,
    CALLBACK_NEW_TOPIC,
    CALLBACK_NEXT,
    CALLBACK_PREVIOUS,
    CALLBACK_THEME_PREFIX,
    CHAT_IDS_KEY,
    OFFLINE_MESSAGE,
)
from .handlers import end_session, new_topic, next_card, previous_card, start, theme_chosen

logger = logging.getLogger(__name__)

AppType = Application[Any, Any, Any, Any, Any, Any]


async def on_error(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle errors in bot handlers."""
    err = context.error
    if err is None:
        return
    chat_id = context.bot_data.get("_last_chat_id") if hasattr(context, "bot_data") else None
    logger.exception("Handler error | chat_id=%s | error=%s", chat_id, err)


async def notify_going_offline(app: AppType) -> None:
    """Send 'going offline' to tracked chats with active sessions.

    Runs in post_stop so the bot is still usable.
    """
    raw = app.bot_data.get(CHAT_IDS_KEY)
    chat_ids: set[int] = raw if isinstance(raw, set) else set()  # type: ignore[assignment]
    if not chat_ids:
        logger.info("Shutdown: no chats to notify")
        return
    notified = 0
    skipped = 0
    for cid in chat_ids:
        # Check if chat has an active session
        chat_data = app.chat_data.get(cid)
        has_active_session = False
        if chat_data and isinstance(chat_data, dict):
            # Session is active if user has selected a theme or has questions loaded
            session_data: dict[str, object] = chat_data  # type: ignore[assignment]
            has_active_session = bool(
                session_data.get("theme_id") or session_data.get("shuffled_questions")
            )

        if not has_active_session:
            skipped += 1
            logger.debug("Shutdown: skipping chat_id=%s (no active session)", cid)
            continue

        try:
            await app.bot.send_message(chat_id=cid, text=OFFLINE_MESSAGE)
            notified += 1
        except Exception as e:
            logger.warning("Shutdown: failed to notify chat_id=%s: %s", cid, e)
    # Let the send requests flush before shutdown tears down the HTTP client
    if notified:
        await asyncio.sleep(1.0)
    logger.info(
        "Shutdown: notified %d chat(s) that bot is going offline "
        "(skipped %d without active sessions)",
        notified,
        skipped,
    )


def build_application(
    token: str,
    secret: str | None = None,
    env: str | None = None,
) -> AppType:
    """Build and configure the Telegram bot application."""
    app: AppType = (
        Application.builder()
        .token(token)
        .post_stop(notify_going_offline)  # type: ignore[arg-type]
        .build()
    )
    app.bot_data[CHAT_IDS_KEY] = set()
    app.bot_data[BOT_SECRET_KEY] = secret.strip() if secret and secret.strip() else None
    if env:
        app.bot_data["env"] = env
        logger.info("Application built for %s environment", env)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(theme_chosen, pattern=f"^{CALLBACK_THEME_PREFIX}"))
    app.add_handler(CallbackQueryHandler(next_card, pattern=f"^{CALLBACK_NEXT}$"))
    app.add_handler(CallbackQueryHandler(previous_card, pattern=f"^{CALLBACK_PREVIOUS}$"))
    app.add_handler(CallbackQueryHandler(new_topic, pattern=f"^{CALLBACK_NEW_TOPIC}$"))
    app.add_handler(CallbackQueryHandler(end_session, pattern=f"^{CALLBACK_END_SESSION}$"))
    app.add_error_handler(on_error)
    return app
