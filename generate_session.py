"""
generate_session.py
===================
Run this ONCE on your local machine to generate a SESSION_STRING.
Then set that string as the SESSION_STRING env var on Render/Koyeb.

Usage:
    pip install pyrogram tgcrypto
    python generate_session.py
"""
import asyncio
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pyrogram import Client


async def main():
    api_id = int(input("Enter API_ID (from my.telegram.org): ").strip())
    api_hash = input("Enter API_HASH: ").strip()

    print("\nYou'll be prompted for your phone number and OTP code.")
    print("This generates a session string you can use on Render/Koyeb.\n")

    async with Client(
        name="session_gen",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    ) as client:
        session_string = await client.export_session_string()

    print("\n" + "=" * 60)
    print("YOUR SESSION_STRING:")
    print("=" * 60)
    print(session_string)
    print("=" * 60)
    print("\nCopy this and set it as SESSION_STRING in your Render/Koyeb env vars.")
    print("NEVER share this string with anyone.")


if __name__ == "__main__":
    asyncio.run(main())
