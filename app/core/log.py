import logging
import os

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    force=True,
)

for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
    logging.getLogger(name).setLevel(LOG_LEVEL)

# Shovqinli kutubxonalarni jimlashtirish
for name in ("aiohttp.access", "telebot"):
    logging.getLogger(name).setLevel(logging.WARNING)

logger = logging.getLogger("driver-bot")