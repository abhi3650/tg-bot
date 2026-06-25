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


def load() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "current_page": 1,
        "current_movie_index": 0,
        "done": False,
        "total_processed": 0,
    }


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
