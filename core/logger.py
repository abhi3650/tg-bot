"""
core/logger.py — Shared logger with file + console output.
"""
import logging
import os
from pathlib import Path

Path("data/logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/logs/bot.log", encoding="utf-8"),
    ],
)


def get(name: str) -> logging.Logger:
    return logging.getLogger(name)
