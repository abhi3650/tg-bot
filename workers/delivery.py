"""
workers/delivery.py — Process 1, Stage 3
Consumes deep links from deeplink_queue.
Parses the bot username and start param from each link.
Sends /start shortlink_xxx to the delivery bot.
The delivery bot immediately sends the file — Process 2 (file_handler) picks it up.
"""
import asyncio
from pyrogram import Client
from core.config import Config
from core import queues
from core.logger import get
from utils.parsers import parse_start_param
from utils.floodwait import safe_send

log = get("delivery")


async def run(client: Client, cfg: Config):
    """
    Reads deep links, sends /start to the delivery bot.
    Files are forwarded by the file_handler (Process 2), not here.
    """
    log.info("Delivery worker started.")

    while True:
        item = await asyncio.wait_for(queues.deeplink_queue.get(), timeout=300)

        if item is queues.STOP:
            log.info("Delivery: got STOP. Pipeline complete.")
            return

        deep_link = item
        log.info(f"Processing deep link: {deep_link}")

        try:
            bot_username, start_param = parse_start_param(deep_link)
        except ValueError as e:
            log.error(f"Failed to parse deep link '{deep_link}': {e}")
            continue

        # The delivery bot may differ from the one in the URL, or be the same.
        # We use the bot username extracted from the URL to be accurate.
        target_bot = bot_username if bot_username else cfg.delivery_bot

        command = f"/start {start_param}"
        log.info(f"  → Sending '{command}' to @{target_bot}")
        await safe_send(client, target_bot, command, delay=2.0)

        # File will be received by the on_message handler in file_handler.py
        # Give the delivery bot a moment to respond
        await asyncio.sleep(2.5)
