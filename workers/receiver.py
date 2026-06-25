"""
workers/receiver.py — Process 1, Stage 2
Consumes vplinks from vplink_queue, batches them into /b link1\n/b link2...,
sends to the receiver bot, waits for the response, extracts telegram deep links,
and puts them into deeplink_queue.

The receiver bot may reply with 1 message containing all 10 deep links,
or 10 separate messages — we handle both.
"""
import asyncio
from pyrogram import Client
from core.config import Config
from core import queues
from core.logger import get
from utils.parsers import extract_deeplinks
from utils.floodwait import wait_for_reply, safe_send

log = get("receiver")

BATCH_SIZE = 10  # send 10 vplinks per batch (matches 1 page of movies)


async def _collect_batch(timeout: float = 5.0) -> list[str]:
    """Drain up to BATCH_SIZE vplinks from the queue, or until STOP."""
    batch = []
    try:
        while len(batch) < BATCH_SIZE:
            item = await asyncio.wait_for(queues.vplink_queue.get(), timeout=timeout)
            if item is queues.STOP:
                await queues.vplink_queue.put(queues.STOP)  # re-signal for next call
                break
            batch.append(item)
    except asyncio.TimeoutError:
        pass
    return batch


async def run(client: Client, cfg: Config):
    """
    Reads vplinks in batches, sends to receiver bot, collects deep links.
    """
    log.info("Receiver worker started.")

    while True:
        # Check if pipeline is done
        sentinel = await asyncio.wait_for(queues.vplink_queue.get(), timeout=300)
        if sentinel is queues.STOP:
            log.info("Receiver: got STOP. Sending STOP downstream.")
            await queues.deeplink_queue.put(queues.STOP)
            return

        # Got a real vplink — collect it plus up to 9 more
        batch = [sentinel]
        try:
            while len(batch) < BATCH_SIZE:
                item = await asyncio.wait_for(queues.vplink_queue.get(), timeout=3.0)
                if item is queues.STOP:
                    await queues.vplink_queue.put(queues.STOP)
                    break
                batch.append(item)
        except asyncio.TimeoutError:
            pass

        if not batch:
            continue

        # Build the /b <link1>\n/b <link2>... payload
        payload = "\n".join(f"/b {link}" for link in batch)
        log.info(f"Sending {len(batch)} vplinks to receiver bot:\n  {batch[0]} ...")

        # Get latest msg id before sending so we can detect new replies
        last_id = 0
        async for m in client.get_chat_history(cfg.receiver_bot, limit=1):
            last_id = m.id

        await safe_send(client, cfg.receiver_bot, payload, delay=1.5)

        # Collect reply messages — bot may send 1 or N messages
        collected_links = []
        deadline = asyncio.get_event_loop().time() + cfg.bot_reply_timeout * 3

        while asyncio.get_event_loop().time() < deadline:
            async for msg in client.get_chat_history(cfg.receiver_bot, limit=20):
                if msg.id <= last_id:
                    break
                if msg.text:
                    links = extract_deeplinks(msg.text)
                    for lnk in links:
                        if lnk not in collected_links:
                            collected_links.append(lnk)
                            log.info(f"  🔗 Deep link: {lnk}")
            if collected_links:
                break
            await asyncio.sleep(1.5)

        if not collected_links:
            log.warning(f"No deep links found in receiver bot reply for batch of {len(batch)}")

        for link in collected_links:
            await queues.deeplink_queue.put(link)

        await asyncio.sleep(1.0)
