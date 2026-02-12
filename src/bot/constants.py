"""Constants used across the bot."""

# Callback data prefixes/patterns
CALLBACK_THEME_PREFIX = "theme:"
CALLBACK_NEXT = "next"
CALLBACK_PREVIOUS = "previous"
CALLBACK_NEW_TOPIC = "new_topic"
CALLBACK_END_SESSION = "end_session"

# Bot data keys
CHAT_IDS_KEY = "chat_ids"
BOT_SECRET_KEY = "bot_secret"

# Messages
OFFLINE_MESSAGE = "The bot is going offline. Try again later."
UNAUTHORIZED_MESSAGE = (
    "Send /start followed by the secret to use this bot. Ask the owner for the secret."
)
