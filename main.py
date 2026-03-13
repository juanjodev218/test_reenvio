import os
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

SESSION_STRING = os.environ["SESSION_STRING"]
api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]

client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

# ---------------- DEBUG MENSAJES ----------------
@client.on(events.NewMessage)
async def debug(event):
    title = getattr(event.chat, "title", None) or getattr(event.chat, "username", None) or "SIN_TITULO"
    print(f"[DEBUG] chat_id={event.chat_id} | chat={title} | texto={event.raw_text[:50]}")

# ---------------- BOT REENVIO ----------------
PAIRS = [
    (-1003585196721, -1003820294533),
]

@client.on(events.NewMessage(chats=[o for o,_ in PAIRS]))
async def forward(event):
    destino = dict(PAIRS).get(event.chat_id)

    if event.message.text:
        await client.send_message(destino, event.message.text)

# ---------------- BOT LOOP ----------------
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        await client.start()
        print("Bot activo...")
        await client.run_until_disconnected()

    loop.run_until_complete(main())

# ---------------- WEB ----------------
app = Flask(__name__)

@app.get("/")
def health():
    return "OK"

if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)