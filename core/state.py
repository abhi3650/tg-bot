"""
core/state.py — Persistent state for exact-movie resume across 3-min sessions.

State file schema:
{
  "current_page": 3,
  "current_movie_index": 4,   ← 0-based index within the page
  "done": false,
  "total_processed": 1234
}
"""
import json
import os
from pathlib import Path

STATE_FILE = Path("data/state.json")


_DEFAULTS = {
    "current_page": 1,
    "current_movie_index": 0,
    "done": False,
    "total_processed": 0,
}


def load() -> dict:
    state = dict(_DEFAULTS)  # always start with full defaults
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
            if isinstance(data, dict):
                state.update(data)   # overlay saved values on top of defaults
        except (json.JSONDecodeError, OSError):
            pass  # corrupted file → start fresh
    return state


def save(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def clear():
    if STATE_FILE.exists():
        os.remove(STATE_FILE)
    save({"current_page": 1, "current_movie_index": 0, "done": False, "total_processed": 0})


def mark_done(state: dict):
    state["done"] = True
    save(state)
