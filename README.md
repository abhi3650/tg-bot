# ABTech Movie Extractor — Setup Guide

## What this does

Full 5-stage automated pipeline:

```
"mkv" → movie list → click each movie → get vplink
       → /b <vplink> to receiver bot → get telegram deep link
       → /start shortlink_xxx to delivery bot → file received
       → forward file to your channel (caption = filename)
```

Runs within the 3-minute session window. Saves exact page + movie index so it resumes right where it stopped.

---

## Step 1: Get Telegram API credentials

1. Go to https://my.telegram.org
2. Log in → "API development tools"
3. Create an app → copy **App api_id** and **App api_hash**

---

## Step 2: Fill in your .env

```bash
cp .env.example .env
```

Edit `.env` and fill in every value:

| Variable | What to put |
|---|---|
| `API_ID` | From my.telegram.org |
| `API_HASH` | From my.telegram.org |
| `SESSION_STRING` | Generate with step 3 (for cloud) |
| `SOURCE_GROUP` | @username or -100xxx of the group where you send "mkv" |
| `MOVIE_BOT_USERNAME` | Username of the bot that posts movie lists in that group |
| `RECEIVER_BOT` | Bot that accepts `/b <link>` and returns deep links |
| `DELIVERY_BOT` | Bot that accepts `/start shortlink_xxx` and sends the file |
| `TARGET_CHANNEL` | Your channel where files get forwarded |

---

## Step 3: Generate session string (for Render/Koyeb)

Run this **once on your local machine**:

```bash
pip install pyrogram tgcrypto
python generate_session.py
```

Enter your phone number and OTP. It prints a long `SESSION_STRING` — copy it.

Set it as an env var on Render/Koyeb (see Step 5).

---

## Step 4: Local test run

```bash
pip install -r requirements.txt
python app.py
```

On first run without `SESSION_STRING`, Pyrogram will ask for your phone + OTP.
After that a local session file is saved and it runs silently.

---

## Step 5: Deploy to Render (recommended)

1. Push this folder to a GitHub repo
2. Go to https://render.com → New → Background Worker
3. Connect your repo
4. Set all env vars from your `.env` in Render's dashboard
5. Deploy

The `render.yaml` file pre-configures everything.

---

## Step 6: Deploy to Koyeb (alternative)

```bash
# Install koyeb CLI
curl -fsSL https://cli.koyeb.com/install.sh | bash

# Deploy
koyeb app create abtech-movie-extractor
koyeb service create --app abtech-movie-extractor \
  --docker . \
  --env API_ID=xxx API_HASH=xxx SESSION_STRING=xxx \
  --env SOURCE_GROUP=xxx MOVIE_BOT_USERNAME=xxx \
  --env RECEIVER_BOT=xxx DELIVERY_BOT=xxx TARGET_CHANNEL=xxx
```

---

## Resume behavior

When the 3-minute window is reached mid-run:
- State is saved to `data/state.json` with **exact page and movie index**
- Re-run `python app.py` — it picks up from the exact movie it stopped at
- No duplicates, no skipped movies

To reset and start over:
```bash
rm data/state.json
python app.py
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "No movie bot message found" | Check `MOVIE_BOT_USERNAME` — no @ prefix needed |
| "Could not extract vplink" | The movie detail message format may have changed — check `utils/parsers.py` and update `_VPLINK_PATTERNS` |
| "No deep links found" | Check the receiver bot response format — update `_DEEPLINK_PATTERNS` in `utils/parsers.py` |
| Files not forwarding | Verify `DELIVERY_BOT` username matches what's in the deep links |
| FloodWait errors | Increase `INTER_CLICK_DELAY` and `BOT_REPLY_TIMEOUT` in `.env` |
| Session expired on Render | Re-run `generate_session.py` locally and update `SESSION_STRING` |
