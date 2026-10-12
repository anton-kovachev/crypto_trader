import logging
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "logs/error_logs.txt"

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")],
    force=True,
)

logger = logging.getLogger("coinmarketcap_mcp")


def log_and_raise(context: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{context} | {e}", exc_info=True)
                raise

        return wrapper

    return decorator
