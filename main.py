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
from flask import Flask, request, redirect
from threading import Thread
from bot.database import db
import random
import nest_asyncio
from pymongo import MongoClient
from bot.vars import DATABASE_URL, DATABASE_NAME

nest_asyncio.apply()

sync_client = MongoClient(DATABASE_URL)
sync_db = sync_client[DATABASE_NAME]
sync_users = sync_db.users

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


callback_app = Flask(__name__)

@callback_app.route("/nowpayments-callback", methods=["POST"])
def payment_callback():
    print("Received payment callback")
    data = request.json
    print("Received payment data:", data)
    return {"status": "success"}, 200

@callback_app.route("/click", methods=["GET"])
def handle_click():
    userid = request.args.get("userid")
    link = request.args.get("link")
    if not userid or not link:
        return {"error": "Missing userid or link parameter"}, 400
    try:
        userid = int(userid)
    except ValueError:
        return {"error": "Invalid userid"}, 400
    try:
        link_number = int(link)
        if link_number not in [1, 2, 3]:
            return {"error": "Invalid link number"}, 400
    except ValueError:
        return {"error": "Invalid link number"}, 400

    # Synchronous DB update using PyMongo
    link_key = f"link_{link_number}"
    user = sync_users.find_one({"id": userid})
    if not user:
        return {"error": "User not found"}, 404
    link_clicks = user.get("link_clicks", {"link_1": False, "link_2": False, "link_3": False})
    link_clicks[link_key] = True
    sync_users.update_one({"id": userid}, {"$set": {"link_clicks": link_clicks}})

    redirect_url = ""
    if link_number == 1:
        # List of possible redirect URLs (replace with your own)
        links_1 = [
                "https://otieu.com/4/9469081",
                "https://otieu.com/4/9469070",
                "https://otieu.com/4/9469084",
                "https://otieu.com/4/9469071",
                "https://otieu.com/4/9469085",
                "https://otieu.com/4/9469148",
                "https://www.profitableratecpm.com/gibewe00r8?key=1fb6a9250666489b3485c51111a0fa03",
                "https://www.profitableratecpm.com/d7v4z5j2?key=6b9373abf0f59017cc4ad1c95f2ba6d2",
                "https://www.profitableratecpm.com/ph6rddjzy?key=6b2f2d58d8b65223de0f046e9b53e530"
        ]
        redirect_url = random.choice(links_1)
    elif link_number == 2:
        links_2 = [
                "https://www.profitableratecpm.com/bzyb5vhc?key=8f4e212e6c47f8713eabf66331d6f3a7",
                "https://www.profitableratecpm.com/kdm1h0uyjh?key=3b8d567da996de6e3a45a5b3929de9e4",
                "https://www.profitableratecpm.com/mekkw4sqcf?key=1f61c923b6d43d507442356fcc7b6ba4",
                "https://www.profitableratecpm.com/dxh54phy?key=71ddc6a3b1ebe7130403ba039e09c5e1",
                "https://www.profitableratecpm.com/m109t46m4?key=3cf6beb2c99911aae2976333da0d5d76"
            ]
        redirect_url = random.choice(links_2)
    else:
        links_3 = [
            "https://Bamcrypto.blogspot.com",
            "https://www.profitableratecpm.com/pf2xg2fx0?key=f709a90db51366a99bb84ff7a051b135",
            "https://www.profitableratecpm.com/ehzzsb22?key=eb04bcdbb34428b7f66e84a1fab4215b"
        ]
        redirect_url = random.choice(links_3)

    return redirect(redirect_url)

def run_flask():
    callback_app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    # Run Flask in a background thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Run the bot
    run_bot()