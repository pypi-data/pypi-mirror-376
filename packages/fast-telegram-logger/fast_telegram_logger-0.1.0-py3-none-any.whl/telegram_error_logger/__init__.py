"""
Telegram Error Logger

Usage:
    from telegram_error_logger import TelegramErrorLogger

    logger = TelegramErrorLogger(
        bot_token="your_bot_token_here",
        chat_id="your_chat_id_here"
    )

    app = FastAPI()
    app.add_exception_handler(Exception, logger.exception_handler)
"""

from .main import TelegramErrorLogger

__version__ = "0.1.0"

__all__ = [
    "TelegramErrorLogger",
]

__author__ = "xkat"
__email__ = "dreameryandex.22013@gmail.com"
__description__ = "FastAPI error logging to Telegram"