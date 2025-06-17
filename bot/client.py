from decouple import config
from pyrogram import Client

BOT_TOKEN = config('BOT_TOKEN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')
SESSION_STRING = config('SESSION_STRING')

Bot = Client(
    "Crypto Bot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH,
    plugins=dict(root="bot"),
    in_memory=True,
) 