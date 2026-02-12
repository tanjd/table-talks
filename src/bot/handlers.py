"""Bot command and callback handlers."""

import random
from typing import Any

from telegram import Update
from telegram.ext import Application, ContextTypes

from ..data_loader import Theme, get_questions, get_themes
from .auth import require_auth, verify_secret
from .constants import BOT_SECRET_KEY, CALLBACK_THEME_PREFIX
from .keyboards import navigation_keyboard, theme_keyboard
from .session import format_card, get_session, log_action, track_chat

AppType = Application[Any, Any, Any, Any, Any, Any]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is None:
        return
    app: AppType = context.application  # type: ignore[assignment]
    track_chat(app, update)
    session = get_session(context)
    raw_secret = app.bot_data.get(BOT_SECRET_KEY)
    secret: str | None = raw_secret if isinstance(raw_secret, str) and raw_secret else None
    if secret:
        # Use context.args (parsed /start arguments) so deep links and "/start SECRET" both work
        payload = (context.args[0] if context.args else "").strip()
        if not verify_secret(payload, secret):
            log_action(update, "start_unauthorized")
            from .constants import UNAUTHORIZED_MESSAGE

            await update.message.reply_text(UNAUTHORIZED_MESSAGE)
            return
        session["authorized"] = True
    session["theme_id"] = None
    session["index"] = 0
    session["shuffled_questions"] = []
    log_action(update, "start")
    await update.message.reply_text(
        "Choose a theme to get conversation cards. Each card is one question.",
        reply_markup=theme_keyboard(),
    )


async def send_card(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    shuffled_questions: list[str],
    index: int,
) -> None:
    """Send a question card to the user."""
    if not shuffled_questions:
        text = "No questions in this theme yet."
        markup = theme_keyboard()
    else:
        total = len(shuffled_questions)
        idx = index % total
        text = format_card(shuffled_questions, idx)
        # Show back button only if not on first question
        show_back = idx > 0
        markup = navigation_keyboard(show_back=show_back)
        session = get_session(context)
        session["index"] = idx + 1
        session["shuffled_questions"] = shuffled_questions
    if update.callback_query is not None:
        await update.callback_query.edit_message_text(text=text, reply_markup=markup)
    elif update.message is not None:
        await update.message.reply_text(text, reply_markup=markup)


@require_auth
async def theme_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle theme selection."""
    query = update.callback_query
    if query is None:
        return
    app: AppType = context.application  # type: ignore[assignment]
    track_chat(app, update)
    await query.answer()
    if not query.data or not query.data.startswith(CALLBACK_THEME_PREFIX):
        return
    theme_id = query.data[len(CALLBACK_THEME_PREFIX) :].strip()
    themes: list[Theme] = get_themes()
    if not any(t["id"] == theme_id for t in themes):
        log_action(update, "theme_chosen_invalid", theme_id=theme_id)
        return
    log_action(update, "theme_chosen", theme_id=theme_id)
    questions = get_questions(theme_id)
    shuffled: list[str] = questions.copy()
    random.shuffle(shuffled)
    session = get_session(context)
    session["theme_id"] = theme_id
    session["index"] = 0
    session["shuffled_questions"] = shuffled
    await send_card(update, context, shuffled, 0)


@require_auth
async def next_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle next card navigation."""
    query = update.callback_query
    if query is None:
        return
    app: AppType = context.application  # type: ignore[assignment]
    track_chat(app, update)
    await query.answer()
    session = get_session(context)
    shuffled = session.get("shuffled_questions", [])
    if not shuffled:
        log_action(update, "next_card_no_theme")
        await query.edit_message_text(
            "Choose a theme first.",
            reply_markup=theme_keyboard(),
        )
        return
    log_action(update, "next_card", theme_id=str(session.get("theme_id", "")))
    next_index = session.get("index", 0)
    await send_card(update, context, shuffled, next_index)


@require_auth
async def previous_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle previous card navigation."""
    query = update.callback_query
    if query is None:
        return
    app: AppType = context.application  # type: ignore[assignment]
    track_chat(app, update)
    await query.answer()
    session = get_session(context)
    shuffled = session.get("shuffled_questions", [])
    if not shuffled:
        log_action(update, "previous_card_no_theme")
        await query.edit_message_text(
            "Choose a theme first.",
            reply_markup=theme_keyboard(),
        )
        return
    current_index = session.get("index", 0)
    # Go back: current index points to next card, so go back 2 positions
    prev_index = max(0, current_index - 2)
    log_action(update, "previous_card", theme_id=str(session.get("theme_id", "")))
    await send_card(update, context, shuffled, prev_index)


@require_auth
async def new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle new topic selection."""
    query = update.callback_query
    if query is None:
        return
    app: AppType = context.application  # type: ignore[assignment]
    track_chat(app, update)
    log_action(update, "new_topic")
    await query.answer()
    session = get_session(context)
    session["theme_id"] = None
    session["index"] = 0
    session["shuffled_questions"] = []
    await query.edit_message_text(
        "Choose a theme to get conversation cards. Each card is one question.",
        reply_markup=theme_keyboard(),
    )


@require_auth
async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle session end."""
    query = update.callback_query
    if query is None:
        return
    app: AppType = context.application  # type: ignore[assignment]
    track_chat(app, update)
    log_action(update, "end_session")
    await query.answer()
    session = get_session(context)
    session["theme_id"] = None
    session["index"] = 0
    session["shuffled_questions"] = []
    await query.edit_message_text(
        "Thanks for playing! Send /start to begin a new session.",
    )
