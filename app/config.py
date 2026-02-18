import os
from typing import List, Set

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", f"/webhook/{BOT_TOKEN}")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", 8080))
ADMIN_IDS: Set[int] = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}
CHANNELS: List[int] = [int(x) for x in os.getenv("CHANNELS", "").split(",") if x.strip()]
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID")) if os.getenv("STORAGE_CHANNEL_ID") else None
DB_PATH = os.getenv("DB_PATH", "movies.db")


def validate_config():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required")
    if not WEBHOOK_HOST:
        raise RuntimeError("WEBHOOK_HOST is required for webhook mode")
    if STORAGE_CHANNEL_ID is None:
        raise RuntimeError("STORAGE_CHANNEL_ID is required")

