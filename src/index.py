"""Run the Table Talks bot. Token from BOT_TOKEN env."""

import logging
import os
import secrets
import string
import sys

from dotenv import load_dotenv

load_dotenv()

# Configure logging before importing bot (so startup logs are visible)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
    force=True,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

from .bot import build_application  # noqa: E402
from .health import DEFAULT_HEALTH_PORT, start_health_server  # noqa: E402

logger = logging.getLogger(__name__)

BOT_USERNAME = "TableTalksBot"
SECRET_LENGTH = 5
ALPHANUMERIC = string.ascii_uppercase + string.digits


def _generate_secret() -> str:
    """Return a 5-character alphanumeric code (uppercase + digits)."""
    return "".join(secrets.choice(ALPHANUMERIC) for _ in range(SECRET_LENGTH))


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.critical("BOT_TOKEN not set; exiting")
        print("Error: Set BOT_TOKEN in the environment or .env", file=sys.stderr)
        raise SystemExit(1)
    secret = _generate_secret()
    logger.info("Bot starting (polling) with generated secret")
    sys.stdout.flush()
    sys.stderr.flush()
    app = build_application(token, secret=secret)
    invite_link = f"https://t.me/{BOT_USERNAME}?start={secret}"
    logger.info("Invite link: %s", invite_link)
    health_port = int(os.environ.get("HEALTH_PORT", DEFAULT_HEALTH_PORT))
    start_health_server(port=health_port)
    try:
        app.run_polling(allowed_updates=["message", "callback_query"])
    finally:
        logger.info("Bot stopped. Restart the process to accept messages again.")


if __name__ == "__main__":
    main()
