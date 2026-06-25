"""
utils/buttons.py — Safe inline button navigation for Pyrogram messages.
"""
import asyncio
from typing import Optional
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from core.logger import get

log = get("buttons")


def get_inline_buttons(message: Message) -> list:
    """Flatten all inline keyboard buttons into a single list."""
    kb = getattr(message, "reply_markup", None)
    if not kb or not hasattr(kb, "inline_keyboard"):
        return []
    return [btn for row in kb.inline_keyboard for btn in row]


def get_movie_buttons(message: Message) -> list:
    """Return only the movie-entry buttons (exclude NEXT, PREV, LANGUAGE etc)."""
    skip = {"next", "prev", "language", "languages", "<<", ">>"}
    return [
        btn for btn in get_inline_buttons(message)
        if not any(kw in btn.text.lower() for kw in skip)
    ]


def get_next_button(message: Message):
    """Return the NEXT >> button, or None if on the last page."""
    for btn in get_inline_buttons(message):
        if "next" in btn.text.lower() or ">>" in btn.text:
            return btn
    return None


async def safe_click(message: Message, button_text: str, retries: int = 3) -> Optional[Message]:
    """
    Click an inline button by its text label with flood-wait retry.
    Returns the resulting Message or None on failure.
    """
    for attempt in range(retries):
        try:
            result = await message.click(button_text)
            await asyncio.sleep(0.5)
            return result
        except FloodWait as e:
            log.warning(f"FloodWait {e.value}s on click '{button_text}'")
            await asyncio.sleep(e.value)
        except Exception as e:
            log.error(f"Click '{button_text}' attempt {attempt+1} failed: {e}")
            await asyncio.sleep(2)
    return None
