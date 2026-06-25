"""
workers/scraper.py — Process 1, Stage 1
Sends "mkv" to the source group, paginates through the movie list,
clicks each movie button to get its detail DM, extracts the vplink,
and puts it into vplink_queue.

Respects the 3-min session window and saves exact-movie state for resume.
"""
import asyncio
import time
from pyrogram import Client
from pyrogram.types import Message
from core.config import Config
from core import state as st
from core import queues
from core.logger import get
from utils.buttons import get_movie_buttons, get_next_button, safe_click
from utils.parsers import extract_vplink
from utils.floodwait import wait_for_reply

log = get("scraper")


async def _get_movie_list_message(client: Client, cfg: Config) -> Message | None:
    """Send 'mkv' to the group and wait for the movie bot's reply."""
    log.info(f"Sending 'mkv' to {cfg.source_group}")

    # Use the resolved chat object to avoid PeerIdInvalid with in_memory sessions
    try:
        chat = await client.get_chat(cfg.source_group)
        chat_id = chat.id
    except Exception as e:
        log.error(f"Cannot resolve SOURCE_GROUP '{cfg.source_group}': {e}")
        return None

    await client.send_message(chat_id, "mkv")
    await asyncio.sleep(4)

    async for msg in client.get_chat_history(chat_id, limit=15):
        sender = msg.from_user or msg.sender_chat
        username = getattr(sender, "username", "") or ""
        if username.lower() == cfg.movie_bot_username.lstrip("@").lower():
            if msg.reply_markup:
                log.info(f"Found movie list message (id={msg.id})")
                return msg
    log.error("Could not find movie bot's list message in group.")
    return None


async def _navigate_to_page(msg: Message, target_page: int) -> Message:
    """Fast-forward through NEXT buttons to reach the saved page."""
    current = 1
    while current < target_page:
        next_btn = get_next_button(msg)
        if not next_btn:
            log.warning(f"Ran out of pages at {current}, expected {target_page}")
            break
        result = await safe_click(msg, next_btn.text)
        if result:
            msg = result
        else:
            # Some bots edit the message in place — re-fetch
            await asyncio.sleep(2)
        current += 1
        log.info(f"Fast-forwarded to page {current}")
    return msg


async def run(client: Client, cfg: Config, session_start: float):
    """
    Main scraper coroutine. Puts vplink strings into queues.vplink_queue.
    Sends queues.STOP when done or when the session window expires.
    """
    state = st.load()

    if state.get("done"):
        log.info("Scraper: already marked done. Sending STOP.")
        await queues.vplink_queue.put(queues.STOP)
        return

    log.info(f"Scraper resuming at page={state['current_page']} movie_index={state['current_movie_index']}")

    # Step 1: trigger movie list
    list_msg = await _get_movie_list_message(client, cfg)
    if not list_msg:
        await queues.vplink_queue.put(queues.STOP)
        return

    # Step 2: navigate to saved page
    if state["current_page"] > 1:
        list_msg = await _navigate_to_page(list_msg, state["current_page"])

    # Step 3: main page loop
    while True:
        elapsed = time.time() - session_start
        if elapsed > cfg.session_window:
            log.warning(f"⏰ Session window reached ({elapsed:.0f}s). Saving state and stopping.")
            st.save(state)
            log.info(f"Next run will resume at page={state['current_page']} movie={state['current_movie_index']}")
            await queues.vplink_queue.put(queues.STOP)
            return

        movie_buttons = get_movie_buttons(list_msg)
        if not movie_buttons:
            log.warning("No movie buttons found on this page — may be last page.")
            break

        # Resume from saved movie index within the page
        start_idx = state["current_movie_index"]
        log.info(f"📄 Page {state['current_page']}: {len(movie_buttons)} movies (starting at #{start_idx})")

        for i, btn in enumerate(movie_buttons):
            if i < start_idx:
                continue  # skip already-processed movies on resume

            # Check time before each click
            elapsed = time.time() - session_start
            if elapsed > cfg.session_window:
                state["current_movie_index"] = i
                st.save(state)
                log.warning(f"⏰ Window hit mid-page at movie {i}. Saved.")
                await queues.vplink_queue.put(queues.STOP)
                return

            log.info(f"  [{i+1}/{len(movie_buttons)}] Clicking: {btn.text[:60]}")

            # Get the latest message id in movie bot DM before clicking
            last_id = 0
            async for m in client.get_chat_history(cfg.movie_bot_username, limit=1):
                last_id = m.id

            # Click the movie button — opens DM or sends message to movie bot
            await safe_click(list_msg, btn.text)

            # Wait for the movie bot's detail reply
            reply_text = await wait_for_reply(
                client,
                cfg.movie_bot_username,
                timeout=cfg.bot_reply_timeout,
                after_msg_id=last_id,
            )

            if reply_text:
                vplink = extract_vplink(reply_text)
                if vplink:
                    log.info(f"  ✅ vplink: {vplink}")
                    await queues.vplink_queue.put(vplink)
                    state["total_processed"] = state.get("total_processed", 0) + 1
                else:
                    log.warning(f"  ⚠️ Could not extract vplink from: {reply_text[:120]}")
            else:
                log.warning(f"  ⏱ No reply from movie bot within {cfg.bot_reply_timeout}s")

            # Save after every movie for fine-grained resume
            state["current_movie_index"] = i + 1
            st.save(state)

            await asyncio.sleep(cfg.inter_click_delay)

        # End of page — go to next
        next_btn = get_next_button(list_msg)
        if not next_btn:
            log.info("🎉 No NEXT button — reached last page.")
            break

        result = await safe_click(list_msg, next_btn.text)
        if result:
            list_msg = result
        else:
            await asyncio.sleep(2)

        state["current_page"] += 1
        state["current_movie_index"] = 0
        st.save(state)
        log.info(f"→ Moved to page {state['current_page']}")

    log.info(f"✅ Scraper finished. Total processed: {state.get('total_processed', 0)}")
    st.mark_done(state)
    await queues.vplink_queue.put(queues.STOP)
