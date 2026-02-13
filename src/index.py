"""Run the Table Talks bot. Token from BOT_TOKEN env."""

import logging
import os
import secrets
import string
import sys
from datetime import datetime

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
    # Determine environment and select appropriate token
    env = os.environ.get("ENV", "").lower()
    token_dev = os.environ.get("BOT_TOKEN_DEV")
    token_prd = os.environ.get("BOT_TOKEN")

    if env == "dev":
        token = token_dev
        env_name = "dev"
    else:
        token = token_prd
        env_name = "prd" if env == "prd" else "prd (default)"

    if not token:
        logger.critical("Bot token not set for environment '%s'; exiting", env_name)
        print(
            "Error: Set BOT_TOKEN (production) or BOT_TOKEN_DEV in the environment or .env",
            file=sys.stderr,
        )
        raise SystemExit(1)

    secret = _generate_secret()
    logger.info("Bot starting (polling) in %s environment with generated secret", env_name)
    invite_link = f"https://t.me/{BOT_USERNAME}?start={secret}"
    logger.info("Invite link: %s", invite_link)
    sys.stdout.flush()
    sys.stderr.flush()

    # Load optional configuration for home page
    creator_id_str = os.environ.get("CREATOR_USER_ID")
    creator_user_id = int(creator_id_str) if creator_id_str and creator_id_str.isdigit() else None

    bot_version = os.environ.get("BOT_VERSION")
    coffee_link = os.environ.get("COFFEE_LINK")

    # Capture deployment time
    deployment_time = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    app = build_application(
        token,
        secret=secret,
        env=env_name,
        creator_user_id=creator_user_id,
        bot_version=bot_version,
        coffee_link=coffee_link,
        deployment_time=deployment_time,
    )
    health_port = int(os.environ.get("HEALTH_PORT", DEFAULT_HEALTH_PORT))
    start_health_server(port=health_port)
    try:
        app.run_polling(allowed_updates=["message", "callback_query"])
    finally:
        logger.info("Bot stopped. Restart the process to accept messages again.")


if __name__ == "__main__":
    main()
