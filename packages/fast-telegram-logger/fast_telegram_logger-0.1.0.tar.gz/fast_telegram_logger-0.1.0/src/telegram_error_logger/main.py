from .infrastructure.error_formatter import TelegramFormatter
from .infrastructure.telegram_sender import TelegramSender
from .use_cases.log_error import LogError
from .fastapi.exception_handler import create_exception_handler


class TelegramErrorLogger:


    def __init__(self, bot_token: str, chat_id: str):
        self._sender = TelegramSender(bot_token, chat_id)
        self._formatter = TelegramFormatter()
        self._log_error = LogError(self._sender, self._formatter)
        self._exception_handler = create_exception_handler(self._log_error)

    @property
    def exception_handler(self):
        return self._exception_handler

    async def log_error_manually(self, message: str, level: str = "ERROR"):
        from datetime import datetime
        from .entities.error_message import ErrorMessage
        from .entities.log_level import LogLevel

        error = ErrorMessage(
            level=LogLevel.ERROR if level == "ERROR" else LogLevel.CRITICAL,
            message=message,
            file_path="manual",
            timestamp=datetime.now(),
            stack_trace=None
        )

        return await self._log_error.execute(error)