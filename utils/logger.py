# ...existing code...
import logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "aws_agents.log")


def get_logger(name: str = "aws_agents") -> logging.Logger:
    """
    Return a configured logger. Safe to call multiple times (won't add duplicate handlers).
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    fh = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def log_action(message: str, level: str = "info"):
    """
    Convenience wrapper used by agents to log actions.
    Keeps compatibility with existing imports like `from utils.logger import log_action`.
    """
    logger = get_logger("actions")
    level = (level or "info").lower()
    if level == "debug":
        logger.debug(message)
    elif level == "warning" or level == "warn":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    else:
        logger.info(message)
# ...existing code...