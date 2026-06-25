"""
app.py — ABTech Movie Extractor
================================
Entry point. Starts all pipeline workers concurrently.

Full pipeline:
  [scraper] → vplink_queue → [receiver] → deeplink_queue → [delivery]
                                                         ↕
                                              [file_handler] (always-on)
                                                         ↓
                                               target channel

Usage:
    python app.py                   # uses .env file
    SESSION_STRING=xxx python app.py  # for Render/Koyeb (no .env needed)
"""
import asyncio
import time
import os
import sys

# Load .env if present (local dev)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pyrogram import Client
from core.config import load_config
from core.logger import get
from handlers.file_handler import setup as setup_file_handler
import workers.scraper as scraper
import workers.receiver as receiver
import workers.delivery as delivery

log = get("app")


def build_client(cfg) -> Client:
    """Build Pyrogram client using session string (cloud) or file (local)."""
    if cfg.session_string:
        log.info("Using SESSION_STRING for cloud deployment")
        return Client(
            name="userbot",
            api_id=cfg.api_id,
            api_hash=cfg.api_hash,
            session_string=cfg.session_string,
            in_memory=True,
        )
    else:
        log.info(f"Using local session file: {cfg.session_name}")
        return Client(
            name=cfg.session_name,
            api_id=cfg.api_id,
            api_hash=cfg.api_hash,
        )


async def main():
    cfg = load_config()
    session_start = time.time()

    client = build_client(cfg)

    # Register the always-on file listener (Process 2)
    setup_file_handler(client, cfg)

    async with client:
        me = await client.get_me()
        log.info(f"✅ Logged in as: {me.first_name} (@{me.username})")
        log.info(f"Session window: {cfg.session_window}s")

        # Run all pipeline workers concurrently
        await asyncio.gather(
            scraper.run(client, cfg, session_start),
            receiver.run(client, cfg),
            delivery.run(client, cfg),
        )

    log.info("All workers finished. Session ended.")


if __name__ == "__main__":
    asyncio.run(main())
