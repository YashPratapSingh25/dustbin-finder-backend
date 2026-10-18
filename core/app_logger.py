from contextlib import contextmanager
import logging
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import time
from core.config import settings
from core.context_vars import ContextVars

# Creates logs folder to add logs
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    formatter = (
        logging.Formatter(  # TIME | INFO/DEBUG/ERROR/ETC | MSG
            "%(asctime)s | %(levelname)-8s | %(message)s"
        )
    )

    # Root logger which is the parent logger
    # It passes the log request to its handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.ROOT_LOG_LEVEL)

    if root_logger.handlers:
        root_logger.handlers.clear()

    # Write info and above logs in app.log
    app_handler = TimedRotatingFileHandler(
        "logs/app.log",
        when="midnight",  # Rotates file every midnight
        backupCount=30,  # Stores only 30 days of logs
        encoding="utf-8",
    )
    app_handler.setFormatter(formatter)
    app_handler.setLevel(settings.APP_LOG_LEVEL)

    # Writes error and critical logs in error.log
    error_handler = TimedRotatingFileHandler(
        "logs/error.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(settings.ERROR_LOG_LEVEL)

    # Write logs to stream and by default that is console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(settings.APP_LOG_LEVEL)

    # Adding all the handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)


logger = logging.getLogger(__name__)

def get_log_message(msg : str):
    return f"{ContextVars.request_id.get()} | {ContextVars.method.get()} | {ContextVars.path.get()} | {msg}"

@contextmanager
def log_task(task_name : str):
    start_time = time.time()

    try:
        yield
    finally:
        duration = time.time() - start_time
        HttpLogger.info(f"{task_name} took {duration:.2f} seconds")

class HttpLogger:
    @staticmethod
    def debug(msg: str):
        logger.debug(
            msg=get_log_message(msg),
        )

    @staticmethod
    def info(msg: str):
        logger.info(
            msg=get_log_message(msg),
        )

    @staticmethod
    def warning(msg: str):
        logger.warning(
            msg=get_log_message(msg),
        )

    @staticmethod
    def error(msg: str):
        logger.error(
            msg=get_log_message(msg),
        )

    @staticmethod
    def critical(msg: str):
        logger.critical(
            msg=get_log_message(msg),
        )

    @staticmethod
    def exception(msg: str):
        logger.exception(
            msg=get_log_message(msg),
        )