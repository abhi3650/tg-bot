"""
handlers/file_handler.py — Process 2 (always-on listener)

Listens for ANY file (document/video/audio/animation) sent by the delivery bot in DM.
Copies it to the target channel with ONLY the filename as caption.

This runs as a Pyrogram event handler — always active in the background.
"""
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import asyncio
from core.logger import get
from utils.parsers import get_filename

log = get("file_handler")

# Will be set by app.py before the client starts
_cfg = None


def setup(client: Client, cfg):
    """Register the file handler on the client."""
    global _cfg
    _cfg = cfg

    file_filter = (
        filters.private
        & (filters.document | filters.video | filters.audio | filters.animation)
    )

    @client.on_message(file_filter)
    async def handle_file(c: Client, message: Message):
        if not _cfg:
            return

        # Only handle files from the delivery bot
        sender = message.from_user or message.sender_chat
        sender_username = getattr(sender, "username", "") or ""
        if sender_username.lower() not in (
            _cfg.delivery_bot.lstrip("@").lower(),
            # Also accept from movie bot directly (in case it sends files too)
            _cfg.movie_bot_username.lstrip("@").lower(),
        ):
            return

        filename = get_filename(message)
        log.info(f"📁 Received file: {filename} (from @{sender_username})")

        # Forward to target channel with filename as caption
        for attempt in range(3):
            try:
                await c.copy_message(
                    chat_id=_cfg.target_channel,
                    from_chat_id=message.chat.id,
                    message_id=message.id,
                    caption=filename,
                )
                log.info(f"✅ Forwarded '{filename}' → {_cfg.target_channel}")
                return
            except FloodWait as e:
                log.warning(f"FloodWait {e.value}s on forward")
                await asyncio.sleep(e.value)
            except Exception as e:
                log.error(f"Forward attempt {attempt+1} failed: {e}")
                await asyncio.sleep(3)

        log.error(f"❌ Failed to forward '{filename}' after 3 attempts")
