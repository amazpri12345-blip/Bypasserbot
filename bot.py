import os
import time
import logging
from collections import Counter

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("8615726118:AAE8mIYmfXxlKJ010o-Rg0bApK4SA77wagY")
HISTORY_URL = os.getenv(
    "HISTORY_URL",
    "https://draw.ar-lottery01.com/api/WingO/WingO_1M/GetHistoryIssuePage.json",
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def fetch_history(limit=100):
    params = {"ts": int(time.time() * 1000)}
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://8okwin1.com",
        "Referer": "https://8okwin1.com/",
    }
    r = requests.get(HISTORY_URL, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("data", {}).get("list", [])[:limit]


def make_stats(items):
    colors = [
        str(x.get("color", "")).strip().lower()
        for x in items
        if str(x.get("color", "")).strip()
    ]
    counts = Counter(colors)
    total = len(colors)
    if not total:
        return "No colour data returned."

    return "\n".join(
        f"• {c.title()}: {n}/{total} ({n/total*100:.2f}%)"
        for c, n in counts.most_common()
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Colour Statistics Bot\n\n"
        "/stats - analyse latest 100 records\n"
        "/stats 50 - analyse latest 50 records\n\n"
        "This reports historical frequencies only; it does not guarantee the next result."
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    limit = 100
    if context.args:
        try:
            limit = max(1, min(500, int(context.args[0])))
        except ValueError:
            await update.message.reply_text("Example: /stats 50")
            return

    try:
        items = fetch_history(limit)
        if not items:
            await update.message.reply_text("No history was returned by the endpoint.")
            return

        await update.message.reply_text(
            f"Historical colour statistics\n"
            f"Records analysed: {len(items)}\n\n"
            f"{make_stats(items)}\n\n"
            "Historical frequency is not a prediction or guarantee."
        )
    except requests.RequestException as e:
        log.exception("Request failed")
        await update.message.reply_text(f"Endpoint request failed: {e}")
    except Exception as e:
        log.exception("Processing failed")
        await update.message.reply_text(f"Processing failed: {e}")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
