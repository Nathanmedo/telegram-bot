"""
==========================================
 Author:       Nathanmedo_devs (https://github.com/Nathanmedo)
 Created:      22-Jun-2024
 License:      MIT License
==========================================
"""

from pyrogram import filters
from pyrogram.errors import FloodWait
from bot.commands import start
from bot.client import Bot
import asyncio
import time

@Bot.on_message(filters.private & filters.command(["start"]))
async def handle_start(client, message):
    await start(client, message)

def run_bot():
    while True:
        try:
            print('Bot is Cooking...')
            Bot.run()
        except KeyboardInterrupt:
            print("Bot stopped by user")
            break
        except Exception as e:
            print(f'Error occurred: {e}')
            # Try to stop the client if it's running
            try:
                Bot.stop()
            except:
                pass
            time.sleep(5)
            continue

if __name__ == "__main__":
    run_bot()
