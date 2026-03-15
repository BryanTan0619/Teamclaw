import logging
import os


_LOG_INITIALIZED = False


def setup_basic_logging() -> None:
    global _LOG_INITIALIZED
    if _LOG_INITIALIZED:
        return
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    _LOG_INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    setup_basic_logging()
    return logging.getLogger(name)
