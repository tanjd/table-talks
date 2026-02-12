"""Authorization utilities."""

import functools
import hmac
from collections.abc import Callable, Coroutine
from typing import Any

from telegram import Update
from telegram.ext import Application, ContextTypes

from .constants import BOT_SECRET_KEY, UNAUTHORIZED_MESSAGE
from .session import get_session

AppType = Application[Any, Any, Any, Any, Any, Any]


def is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is authorized to use the bot."""
    app: AppType = context.application  # type: ignore[assignment]
    raw = app.bot_data.get(BOT_SECRET_KEY)
    if not isinstance(raw, str) or not raw:
        return True
    session = get_session(context)
    return session.get("authorized", False)


async def reject_unauthorized_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Reject unauthorized callback queries with an alert."""
    query = update.callback_query
    if query is not None:
        await query.answer(UNAUTHORIZED_MESSAGE, show_alert=True)
        await query.edit_message_text(UNAUTHORIZED_MESSAGE)


def require_auth(
    handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]:
    """Decorator to check authorization before handling callback queries."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_authorized(update, context):
            await reject_unauthorized_callback(update, context)
            return
        await handler(update, context)

    return wrapper


def verify_secret(payload: str, secret: str) -> bool:
    """Verify the provided payload matches the secret using constant-time comparison."""
    if not payload or not secret:
        return False
    return hmac.compare_digest(payload, secret)
