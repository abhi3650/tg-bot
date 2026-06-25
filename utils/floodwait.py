"""
utils/floodwait.py — Wrapper around Pyrogram sends with automatic FloodWait handling.
"""
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from core.logger import get

log = get("floodwait")


async def safe_send(client: Client, chat, text: str, delay: float = 1.0) -> None:
    while True:
        try:
            await client.send_message(chat, text)
            await asyncio.sleep(delay)
            return
        except FloodWait as e:
            log.warning(f"FloodWait: sleeping {e.value}s before send")
            await asyncio.sleep(e.value)
        except Exception as e:
            log.error(f"send_message error: {e}")
            await asyncio.sleep(3)
            return


async def wait_for_reply(
    client: Client,
    from_username: str,
    timeout: float = 10.0,
    after_msg_id: int = 0,
) -> str | None:
    """
    Poll the DM with `from_username` for a new message that arrived after
    `after_msg_id`, within `timeout` seconds.
    Returns the message text, or None on timeout.
    """
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        async for msg in client.get_chat_history(from_username, limit=5):
            if msg.id > after_msg_id and msg.text:
                return msg.text
        await asyncio.sleep(1.0)
    return None
