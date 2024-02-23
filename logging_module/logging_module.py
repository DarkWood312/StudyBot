import inspect
import logging
import sys

from loguru import logger

format_ = '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# logging.getLogger('aiogram').setLevel(logging.DEBUG)
logging.getLogger('hpack').setLevel(logging.ERROR)
config = {
    "handlers": [
        {"sink": sys.stdout, "format": format_},
        {"sink": "debug.log", "format": format_, "retention": "10 days"},
    ]
}
logger.configure(**config)
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True, encoding='utf-8')
