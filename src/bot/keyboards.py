"""Keyboard builders for the bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..data_loader import Theme, get_themes
from .constants import (
    CALLBACK_END_SESSION,
    CALLBACK_NEW_TOPIC,
    CALLBACK_NEXT,
    CALLBACK_PREVIOUS,
    CALLBACK_THEME_PREFIX,
)


def theme_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard with theme selection buttons."""
    themes: list[Theme] = get_themes()
    buttons = [
        [InlineKeyboardButton(t["label"], callback_data=f"{CALLBACK_THEME_PREFIX}{t['id']}")]
        for t in themes
    ]
    return InlineKeyboardMarkup(buttons)


def navigation_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Build keyboard with navigation and action buttons."""
    buttons: list[list[InlineKeyboardButton]] = []
    # Navigation row with back and next
    nav_row: list[InlineKeyboardButton] = []
    if show_back:
        nav_row.append(InlineKeyboardButton("← Back", callback_data=CALLBACK_PREVIOUS))
    nav_row.append(InlineKeyboardButton("Next →", callback_data=CALLBACK_NEXT))
    buttons.append(nav_row)
    # Other actions
    buttons.append([InlineKeyboardButton("New topic", callback_data=CALLBACK_NEW_TOPIC)])
    buttons.append([InlineKeyboardButton("End session", callback_data=CALLBACK_END_SESSION)])
    return InlineKeyboardMarkup(buttons)
