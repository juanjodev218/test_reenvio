from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = 30533350
api_hash = "1b3cea0469dc63434eada8ccd8d5d6a8"

with TelegramClient("sesion_bg", api_id, api_hash) as client:
    string_session = StringSession.save(client.session)
    print(string_session)