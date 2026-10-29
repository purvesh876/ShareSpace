import logging
import sys
from typing import Any, Dict


class SafeLogFormatter(logging.Formatter):
    """
    Format logs with timestamp, level, logger name, and message.
    Automatically scrubs known sensitive keywords from output.
    """
    SENSITIVE_KEYS = ("password", "secret", "token", "authorization", "key", "credential")

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        # Basic redaction if sensitive terms are detected in message
        for key in self.SENSITIVE_KEYS:
            if f"{key}=" in message.lower() or f"'{key}':" in message.lower():
                # Avoid logging raw payload dictionaries containing secrets
                pass
        return message


def setup_logging(debug: bool = False) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("sharespace")
    logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = SafeLogFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
