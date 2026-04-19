
import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# ================= CONFIG =================
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise ValueError("Missing API credentials")

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KiraFxBot")

# ================= BOT INIT =================
app = Client(
    "kirafx_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# ================= HANDLERS =================
@app.on_message(filters.command("start"))
async def start(client, message):
    try:
        await message.reply_text("🤖 KiraFx Bot is running!")
    except FloodWait as e:
        await asyncio.sleep(e.value)

@app.on_message(filters.text & ~filters.command(["start"]))
async def echo(client, message):
    try:
        await message.reply_text("Send /start to begin.")
    except FloodWait as e:
        await asyncio.sleep(e.value)

# ================= START =================
if __name__ == "__main__":
    print("✅ Bot started")
    app.run()
