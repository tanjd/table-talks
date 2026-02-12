"""Table Talks Telegram bot: theme selection and question cards with skip."""

import asyncio
import hmac
import logging
import random
from typing import Any, TypedDict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from .data_loader import Theme, get_questions, get_themes


# Session state stored in context.chat_data (persisted per chat)
class SessionDict(TypedDict, total=False):
    theme_id: str | None
    index: int
    shuffled_questions: list[str]
    authorized: bool


AppType = Application[Any, Any, Any, Any, Any, Any]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

CALLBACK_THEME_PREFIX = "theme:"
CALLBACK_NEXT = "next"
CALLBACK_NEW_TOPIC = "new_topic"
CALLBACK_END_SESSION = "end_session"

CHAT_IDS_KEY = "chat_ids"
BOT_SECRET_KEY = "bot_secret"
OFFLINE_MESSAGE = "The bot is going offline. Try again later."
UNAUTHORIZED_MESSAGE = (
    "Send /start followed by the secret to use this bot. Ask the owner for the secret."
)


def _log(update: Update, action: str, **extra: str | int) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    user_id = update.effective_user.id if update.effective_user else None
    parts = [f"chat_id={chat_id}", f"user_id={user_id}", f"action={action}"]
    for k, v in extra.items():
        parts.append(f"{k}={v}")
    logger.info(" | ".join(parts))


def _track_chat(application: AppType, update: Update) -> None:
    if update.effective_chat is None:
        return
    chat_id: int = update.effective_chat.id
    chat_ids: set[int] = application.bot_data.setdefault(CHAT_IDS_KEY, set())
    chat_ids.add(chat_id)
    # for error handler context
    application.bot_data["_last_chat_id"] = chat_id


def _theme_keyboard() -> InlineKeyboardMarkup:
    themes: list[Theme] = get_themes()
    buttons = [
        [InlineKeyboardButton(t["label"], callback_data=f"{CALLBACK_THEME_PREFIX}{t['id']}")]
        for t in themes
    ]
    return InlineKeyboardMarkup(buttons)


def _next_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Skip → Next card", callback_data=CALLBACK_NEXT)],
            [InlineKeyboardButton("New topic", callback_data=CALLBACK_NEW_TOPIC)],
            [InlineKeyboardButton("End session", callback_data=CALLBACK_END_SESSION)],
        ]
    )


def _get_session(context: ContextTypes.DEFAULT_TYPE) -> SessionDict:
    if context.chat_data is None:
        raise RuntimeError("chat_data is required (PTB application default)")
    chat_data: SessionDict = context.chat_data  # type: ignore[assignment]
    if "theme_id" not in chat_data:
        chat_data["theme_id"] = None
        chat_data["index"] = 0
        chat_data["shuffled_questions"] = []
    return chat_data


def _is_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    app: AppType = context.application  # type: ignore[assignment]
    raw = app.bot_data.get(BOT_SECRET_KEY)
    if not isinstance(raw, str) or not raw:
        return True
    session = _get_session(context)
    return session.get("authorized", False)


async def _reject_unauthorized_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query
    if query is not None:
        await query.answer(UNAUTHORIZED_MESSAGE, show_alert=True)
        await query.edit_message_text(UNAUTHORIZED_MESSAGE)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    app: AppType = context.application  # type: ignore[assignment]
    _track_chat(app, update)
    session = _get_session(context)
    raw_secret = app.bot_data.get(BOT_SECRET_KEY)
    secret: str | None = raw_secret if isinstance(raw_secret, str) and raw_secret else None
    if secret:
        # Use context.args (parsed /start arguments) so deep links and "/start SECRET" both work
        payload = (context.args[0] if context.args else "").strip()
        if not payload or not hmac.compare_digest(payload, secret):
            _log(update, "start_unauthorized")
            await update.message.reply_text(UNAUTHORIZED_MESSAGE)
            return
        session["authorized"] = True
    session["theme_id"] = None
    session["index"] = 0
    session["shuffled_questions"] = []
    _log(update, "start")
    await update.message.reply_text(
        "Choose a theme to get conversation cards. Each card is one question.",
        reply_markup=_theme_keyboard(),
    )


def _format_card(questions: list[str], index: int) -> str:
    """Format one question with 'Question N of M'."""
    total = len(questions)
    idx = index % total
    one_based = idx + 1
    return f"Question {one_based} of {total}\n\n{questions[idx]}"


async def send_card(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    shuffled_questions: list[str],
    index: int,
) -> None:
    if not shuffled_questions:
        text = "No questions in this theme yet."
        markup = _theme_keyboard()
    else:
        total = len(shuffled_questions)
        idx = index % total
        text = _format_card(shuffled_questions, idx)
        markup = _next_keyboard()
        session = _get_session(context)
        session["index"] = idx + 1
        session["shuffled_questions"] = shuffled_questions
    if update.callback_query is not None:
        await update.callback_query.edit_message_text(text=text, reply_markup=markup)
    elif update.message is not None:
        await update.message.reply_text(text, reply_markup=markup)


async def theme_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    if not _is_authorized(update, context):
        await _reject_unauthorized_callback(update, context)
        return
    app: AppType = context.application  # type: ignore[assignment]
    _track_chat(app, update)
    await query.answer()
    if not query.data or not query.data.startswith(CALLBACK_THEME_PREFIX):
        return
    theme_id = query.data[len(CALLBACK_THEME_PREFIX) :].strip()
    themes: list[Theme] = get_themes()
    if not any(t["id"] == theme_id for t in themes):
        _log(update, "theme_chosen_invalid", theme_id=theme_id)
        return
    _log(update, "theme_chosen", theme_id=theme_id)
    questions = get_questions(theme_id)
    shuffled: list[str] = questions.copy()
    random.shuffle(shuffled)
    session = _get_session(context)
    session["theme_id"] = theme_id
    session["index"] = 0
    session["shuffled_questions"] = shuffled
    await send_card(update, context, shuffled, 0)


async def next_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    if not _is_authorized(update, context):
        await _reject_unauthorized_callback(update, context)
        return
    app: AppType = context.application  # type: ignore[assignment]
    _track_chat(app, update)
    await query.answer()
    session = _get_session(context)
    shuffled = session.get("shuffled_questions", [])
    if not shuffled:
        _log(update, "next_card_no_theme")
        await query.edit_message_text(
            "Choose a theme first.",
            reply_markup=_theme_keyboard(),
        )
        return
    _log(update, "next_card", theme_id=str(session.get("theme_id", "")))
    next_index = session.get("index", 0)
    await send_card(update, context, shuffled, next_index)


async def new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    if not _is_authorized(update, context):
        await _reject_unauthorized_callback(update, context)
        return
    app: AppType = context.application  # type: ignore[assignment]
    _track_chat(app, update)
    _log(update, "new_topic")
    await query.answer()
    session = _get_session(context)
    session["theme_id"] = None
    session["index"] = 0
    session["shuffled_questions"] = []
    await query.edit_message_text(
        "Choose a theme to get conversation cards. Each card is one question.",
        reply_markup=_theme_keyboard(),
    )


async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    if not _is_authorized(update, context):
        await _reject_unauthorized_callback(update, context)
        return
    app: AppType = context.application  # type: ignore[assignment]
    _track_chat(app, update)
    _log(update, "end_session")
    await query.answer()
    session = _get_session(context)
    session["theme_id"] = None
    session["index"] = 0
    session["shuffled_questions"] = []
    await query.edit_message_text(
        "Thanks for playing! Send /start to begin a new session.",
    )


async def _on_error(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    err = context.error
    if err is None:
        return
    chat_id = context.bot_data.get("_last_chat_id") if hasattr(context, "bot_data") else None
    logger.exception("Handler error | chat_id=%s | error=%s", chat_id, err)


async def _notify_going_offline(app: AppType) -> None:
    """Send 'going offline' to tracked chats. Runs in post_stop so the bot is still usable."""
    raw = app.bot_data.get(CHAT_IDS_KEY)
    chat_ids: set[int] = raw if isinstance(raw, set) else set()  # type: ignore[assignment]
    if not chat_ids:
        logger.info("Shutdown: no chats to notify")
        return
    notified = 0
    for cid in chat_ids:
        try:
            await app.bot.send_message(chat_id=cid, text=OFFLINE_MESSAGE)
            notified += 1
        except Exception as e:
            logger.warning("Shutdown: failed to notify chat_id=%s: %s", cid, e)
    # Let the send requests flush before shutdown tears down the HTTP client
    if notified:
        await asyncio.sleep(1.0)
    logger.info("Shutdown: notified %d chat(s) that bot is going offline", notified)


def build_application(
    token: str,
    secret: str | None = None,
) -> AppType:
    app: AppType = (
        Application.builder()
        .token(token)
        .post_stop(_notify_going_offline)  # type: ignore[arg-type]
        .build()
    )
    app.bot_data[CHAT_IDS_KEY] = set()
    app.bot_data[BOT_SECRET_KEY] = secret.strip() if secret and secret.strip() else None
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(theme_chosen, pattern=f"^{CALLBACK_THEME_PREFIX}"))
    app.add_handler(CallbackQueryHandler(next_card, pattern=f"^{CALLBACK_NEXT}$"))
    app.add_handler(CallbackQueryHandler(new_topic, pattern=f"^{CALLBACK_NEW_TOPIC}$"))
    app.add_handler(CallbackQueryHandler(end_session, pattern=f"^{CALLBACK_END_SESSION}$"))
    app.add_error_handler(_on_error)
    return app
