"""
core/config.py — All configuration loaded from environment variables.
"""
import os
from dataclasses import dataclass


@dataclass
class Config:
    # Telegram API credentials (from https://my.telegram.org)
    api_id: int
    api_hash: str

    # Session: either a Pyrogram session STRING (for Render/Koyeb)
    # or leave blank to use a local session file named SESSION_NAME
    session_string: str
    session_name: str

    # Telegram entities
    source_group: str       # group where you send "mkv"
    movie_bot_username: str # bot that posts the movie list in that group
    receiver_bot: str       # bot that receives /b <vplink> and returns deep links
    delivery_bot: str       # bot that receives /start shortlink_xxx and sends the file
    target_channel: str     # your channel where files get forwarded

    # Timing
    session_window: int     # seconds — save state and stop before 3-min limit
    inter_click_delay: float  # seconds between button clicks
    bot_reply_timeout: float  # seconds to wait for a bot reply after clicking


def load_config() -> Config:
    def req(key: str) -> str:
        v = os.getenv(key, "").strip()
        if not v:
            raise EnvironmentError(f"Required env var missing: {key}")
        return v

    return Config(
        api_id=int(req("API_ID")),
        api_hash=req("API_HASH"),
        session_string=os.getenv("SESSION_STRING", ""),
        session_name=os.getenv("SESSION_NAME", "movie_userbot"),
        source_group=req("SOURCE_GROUP"),
        movie_bot_username=req("MOVIE_BOT_USERNAME"),
        receiver_bot=req("RECEIVER_BOT"),
        delivery_bot=req("DELIVERY_BOT"),
        target_channel=req("TARGET_CHANNEL"),
        session_window=int(os.getenv("SESSION_WINDOW", "160")),
        inter_click_delay=float(os.getenv("INTER_CLICK_DELAY", "2.5")),
        bot_reply_timeout=float(os.getenv("BOT_REPLY_TIMEOUT", "10.0")),
    )
