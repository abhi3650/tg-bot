"""
utils/parsers.py — Extract URLs and data from various bot message formats.
"""
import re
from typing import Optional


# ── vplink extractor (from movie detail message) ──────────────────────────────
_VPLINK_PATTERNS = [
    r"MOVIE LINK\s*[➠:\-]+\s*:?\s*(https?://\S+)",   # labelled "MOVIE LINK ➠ :"
    r"🔗[^\n]*?(https?://vplink\.\S+)",                 # emoji prefix
    r"(https?://vplink\.in/[A-Za-z0-9]+)",              # bare vplink.in URL
    r"(https?://[A-Za-z0-9._\-]+/[A-Za-z0-9]+)\s*$",  # last URL in message
]

def extract_vplink(text: str) -> Optional[str]:
    for pat in _VPLINK_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            url = m.group(1).strip().rstrip(")")
            return url
    return None


# ── deep link extractor (from receiver bot response) ─────────────────────────
# Receiver bot returns something like:
#   🔓 Bypassed Link :
#   https://telegram.me/SomeBot?start=shortlink_abc123
#   or https://t.me/SomeBot?start=shortlink_abc123
_DEEPLINK_PATTERNS = [
    r"Bypassed Link\s*:?\s*\n?(https?://(?:t\.me|telegram\.me)/[^\s]+)",
    r"(https?://(?:t\.me|telegram\.me)/[A-Za-z0-9_]+\?start=[A-Za-z0-9_\-]+)",
]

def extract_deeplinks(text: str) -> list[str]:
    """Extract ALL deep links from a receiver bot message (may contain multiple)."""
    links = []
    for pat in _DEEPLINK_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            url = m.group(1).strip()
            if url not in links:
                links.append(url)
    return links


def parse_start_param(deep_link: str) -> tuple[str, str]:
    """
    Given https://t.me/SomeBotName?start=shortlink_xxx
    Returns ("SomeBotName", "shortlink_xxx")
    """
    m = re.search(
        r"(?:t\.me|telegram\.me)/([A-Za-z0-9_]+)\?start=([A-Za-z0-9_\-]+)",
        deep_link,
        re.IGNORECASE,
    )
    if not m:
        raise ValueError(f"Cannot parse deep link: {deep_link}")
    return m.group(1), m.group(2)


# ── filename from file message ────────────────────────────────────────────────
def get_filename(message) -> str:
    """Extract the best available filename from a Pyrogram Message."""
    for attr in ("document", "video", "audio", "animation"):
        obj = getattr(message, attr, None)
        if obj:
            fn = getattr(obj, "file_name", None)
            if fn:
                return fn
    # fallback: use message caption or a generic name
    if message.caption:
        return message.caption.strip().split("\n")[0][:200]
    return "unknown_file"
