"""
core/queues.py — Shared asyncio queues that connect the pipeline stages.

Pipeline:
  scraper  →[vplink_queue]→  receiver  →[deeplink_queue]→  delivery  →[file_queue]→  forwarder
"""
import asyncio

# vplink URLs extracted from movie detail messages (e.g. https://vplink.in/RLWJRC)
vplink_queue: asyncio.Queue = asyncio.Queue()

# telegram.me deep links returned by the receiver bot (e.g. https://t.me/BOT?start=xxx)
deeplink_queue: asyncio.Queue = asyncio.Queue()

# Sentinel value to signal workers to shut down
STOP = object()
