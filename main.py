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

# -------------------------------------------------
# RUTAS: chat origen -> chat destino + tema destino
# -------------------------------------------------
ROUTES = {
    -1003585196721: {
        "dest_chat": -1003820294533,
        "dest_thread": None,  # reemplaza por el thread real de "SEÑALES BÁSICAS"
    },
    -1003020297428: {
        "dest_chat": -1003728976509,
        "dest_thread": None,  # reemplaza por el thread real de "SEÑALES PRO"
    },
    -1003805449629: {
        "dest_chat": -1003668463973,
        "dest_thread": None,  # tema vip 1
    },
    -1003585196721: {
        "dest_chat": -1003668463973,
        "dest_thread": None,  # tema vip 2
    },
}

# origen_chat -> origen_msg_id -> datos del mensaje copiado
mapa_por_origen = {origen: {} for origen in ROUTES.keys()}


# ---------------- DEBUG MENSAJES ----------------
@client.on(events.NewMessage)
async def debug(event):
    try:
        title = getattr(event.chat, "title", None) or getattr(event.chat, "username", None) or "SIN_TITULO"
        thread = getattr(event.message, "message_thread_id", None)
        print(
            f"[DEBUG] chat_id={event.chat_id} | thread={thread} | chat={title} | texto={event.raw_text[:50]}",
            flush=True
        )
    except Exception as e:
        print(f"[DEBUG ERROR] {e}", flush=True)


# ---------------- BOT REENVIO ----------------
@client.on(events.NewMessage(chats=list(ROUTES.keys())))
async def forward(event):
    try:
        origen = event.chat_id
        route = ROUTES.get(origen)
        if not route:
            return

        destino_chat = route["dest_chat"]
        destino_thread = route["dest_thread"]

        sent_msg = None

        # kwargs comunes
        extra = {}
        if destino_thread is not None:
            # En algunas versiones de Telethon esto funciona directo
            extra["message_thread_id"] = destino_thread

        if event.message.media:
            sent_msg = await client.send_file(
                destino_chat,
                event.message.media,
                caption=event.message.text or "",
                **extra
            )
        elif event.message.text:
            sent_msg = await client.send_message(
                destino_chat,
                event.message.text,
                **extra
            )

        if sent_msg:
            mapa_por_origen[origen][event.message.id] = {
                "dest_chat": destino_chat,
                "dest_msg_id": sent_msg.id,
                "dest_thread": destino_thread,
            }
            print(
                f"Copiado: {origen}:{event.message.id} -> {destino_chat}:{sent_msg.id} thread={destino_thread}",
                flush=True
            )

    except Exception as e:
        print(f"Error reenviando: {repr(e)}", flush=True)


# ---------------- EDICION DE MENSAJES ----------------
@client.on(events.MessageEdited(chats=list(ROUTES.keys())))
async def on_edit(event):
    try:
        origen = event.chat_id
        origen_msg_id = event.message.id

        data = mapa_por_origen.get(origen, {}).get(origen_msg_id)
        if not data:
            print(f"No encontré mapeo para editar {origen}:{origen_msg_id}", flush=True)
            return

        destino_chat = data["dest_chat"]
        destino_msg_id = data["dest_msg_id"]

        nuevo_texto = event.message.text or ""
        await client.edit_message(destino_chat, destino_msg_id, nuevo_texto)

        print(
            f"Editado: {origen}:{origen_msg_id} -> {destino_chat}:{destino_msg_id}",
            flush=True
        )

    except Exception as e:
        print(f"Error editando: {repr(e)}", flush=True)


# ---------------- BOT LOOP ----------------
def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def main():
        await client.start()
        me = await client.get_me()
        print(f"Bot activo como: {me.id}", flush=True)
        await client.run_until_disconnected()

    loop.run_until_complete(main())


# ---------------- WEB ----------------
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

    port = int(os.environ.get("PORT", 10000))
    print(f"Web listening on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port)
