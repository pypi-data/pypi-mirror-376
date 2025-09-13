import traceback
from datetime import datetime
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from ..entities.error_message import ErrorMessage
from ..entities.log_level import LogLevel
from ..use_cases.log_error import LogError


def create_exception_handler(log_error: LogError):

    async def exception_handler(request: Request, exc: Exception) -> Response:
        level = _determine_error_level(exc)

        error_message = ErrorMessage(
            level=level,
            message=str(exc) or f"{type(exc).__name__}: No message",
            file_path=_extract_file_path(exc),
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc()
        )

        try:
            await log_error.execute(error_message)
        except Exception:
            pass

        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": "An error occurred while processing your request"}
        )

    return exception_handler


def _determine_error_level(exc: Exception) -> LogLevel:
    critical_exceptions = (
        ConnectionError,
        OSError,
        MemoryError,
        SystemExit,
        KeyboardInterrupt
    )

    if isinstance(exc, critical_exceptions):
        return LogLevel.CRITICAL
    else:
        return LogLevel.ERROR


def _extract_file_path(exc: Exception) -> str:
    tb = exc.__traceback__
    if tb:
        while tb.tb_next:
            tb = tb.tb_next
        return tb.tb_frame.f_code.co_filename
    return "unknown"