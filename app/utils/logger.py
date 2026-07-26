import logging
import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "kanani_backend.log")


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger.
    Logs are written to both console and logs/kanani_backend.log
    """

    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Log format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File Handler (5 MB per file, keep 5 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger





# ============================

# How to use it

# In any file:

# from app.utils.logger import get_logger

# logger = get_logger(__name__)

# Examples:

# logger.info("Vendor created successfully")
# logger.warning("Vendor not found")
# logger.error("Database connection failed")
# try:
#     x = 10 / 0
# except Exception:
#     logger.exception("Unexpected error while saving vendor")