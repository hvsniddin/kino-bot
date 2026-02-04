import os
from typing import List, Set

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS: Set[int] = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()}
CHANNELS: List[int] = [int(x) for x in os.getenv("CHANNELS", "").split(",") if x.strip()]
STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID")) if os.getenv("STORAGE_CHANNEL_ID") else None
DB_PATH = os.getenv("DB_PATH", "movies.db")


def validate_config():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required")
    if STORAGE_CHANNEL_ID is None:
        raise RuntimeError("STORAGE_CHANNEL_ID is required")

