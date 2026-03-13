import os
import asyncio
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ----------------- CONFIG SESION -----------------
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()

api_id = int(os.environ["API_ID"])
api_hash = os.environ["API_HASH"]

if not SESSION_STRING:
    raise RuntimeError("Falta SESSION_STRING")

client = TelegramClient(StringSession(SESSION_STRING), api_id, api_hash)

PAIRS = [
    (-1003585196721, -1003820294533),
    (-1003020297428, -1003728976509),
]

mapa_por_origen = {o: {} for o, _ in PAIRS}
destino_por_origen = dict(PAIRS)


@client.on(events.NewMessage(chats=[o for o, _ in PAIRS]))
async def on_new_message(event):
    try:
        origen_chat_id = event.chat_id
        destino_chat_id = destino_por_origen.get(origen_chat_id)
        if not destino_chat_id:
            return

        sent_msg = None

        if event.message.text and not event.message.media:
            sent_msg = await client.send_message(destino_chat_id, event.message.text)
        elif event.message.media:
            sent_msg = await client.send_file(
                destino_chat_id,
                event.message.media,
                caption=event.message.text or ""
            )

        if sent_msg:
            mapa_por_origen[origen_chat_id][event.message.id] = sent_msg.id
            print(
                f"Mensaje copiado: {origen_chat_id}:{event.message.id} -> {destino_chat_id}:{sent_msg.id}",
                flush=True
            )

    except Exception as e:
        print("Error copiando:", repr(e), flush=True)


@client.on(events.MessageEdited(chats=[o for o, _ in PAIRS]))
async def on_edit_message(event):
    try:
        origen_chat_id = event.chat_id
        destino_chat_id = destino_por_origen.get(origen_chat_id)
        if not destino_chat_id:
            return

        origen_id = event.message.id
        if origen_id not in mapa_por_origen[origen_chat_id]:
            return

        destino_id = mapa_por_origen[origen_chat_id][origen_id]

        if event.message.text is not None:
            await client.edit_message(destino_chat_id, destino_id, event.message.text)
            print(f"Mensaje editado: {origen_chat_id}:{origen_id}", flush=True)

    except Exception as e:
        print("Error editando:", repr(e), flush=True)


def run_bot():
    print("🚀 Iniciando bot...", flush=True)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError("❌ SESSION_STRING inválida o expirada.")
        print("✅ Bot autorizado. Escuchando...", flush=True)
        await client.run_until_disconnected()

    loop.run_until_complete(main())


# ----------------- WEB (para Railway/Render) -----------------
app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

@app.get("/ping")
def ping():
    return "PONG", 200


if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", "10000"))
    print(f"🌐 Web listening on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port)