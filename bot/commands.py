from .admin import add_user
from .buttons import HELP_BUTTONS, START_BUTTONS, ABOUT_BUTTONS, MINING_BUTTONS
from .constants import START_TEXT, HELP_TEXT, ABOUT_TEXT
from .stickers import WAITING
import random
from .crypto_utils import (
    get_crypto_price,
    get_crypto_historical,
    get_trending_cryptos,
    get_coin_details,
    get_exchanges,
    get_coin_market_data,
    get_exchange_rates,
    get_coin_exchanges,
    fetch_live_prices,
    format_prices_message,
)
from .database import db
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, BotCommand, BotCommandScopeAllPrivateChats, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from datetime import datetime, timedelta
import pytz
from .client import Bot

# Channel ID for verification
CHANNEL_USERNAME = "@BTS_bot_payment"
CHANNEL_USERNAME_2 = "@bamcryptoalphaGem"

# Main menu buttons
MAIN_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("⛏️ Trade", callback_data="mine")],
    [InlineKeyboardButton("💳 Deposit", callback_data="deposit")],
    [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
    [InlineKeyboardButton("🤖 Upgrade", callback_data="upgrade")],
    [InlineKeyboardButton("🤝 Referral", callback_data="referral")],
    [InlineKeyboardButton("📺 View Ads", callback_data="view_ads")]
])

# Verification buttons
VERIFY_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/BTS_bot_payment")],
    [InlineKeyboardButton("📢 Join Channel 2", url=f"https://t.me/bamcryptoalphaGem")],
    [InlineKeyboardButton("✅ Verify", callback_data="verify_channel")]
])

async def check_channel_membership(user_id: int) -> bool:
    try:
        print(f"Checking channel membership for user {user_id}")
        member = await Bot.get_chat_member(CHANNEL_USERNAME, user_id)
        print(f"Member status: {member.status}")
        is_member = member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        print(f"Is member: {is_member}")
        return is_member
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

async def check_channel_membership_2(user_id: int) -> bool:
    try:
        print(f"Checking channel membership for user {user_id}")
        member = await Bot.get_chat_member(CHANNEL_USERNAME_2, user_id)
        print(f"Member status: {member.status}")
        is_member = member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        print(f"Is member: {is_member}")
        return is_member
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False

@Bot.on_callback_query(filters.regex("^verify_channel$"))
async def verify_channel_callback(bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    print(f"Verify callback received from user {user_id}")
    
    if await check_channel_membership(user_id) and await check_channel_membership_2(user_id):
        print(f"User {user_id} verified as channel member")
        # User has joined the channel, proceed with start command
        await start(bot, callback_query.message, cb=True)
    else:
        print(f"User {user_id} not verified as channel member")
        # User hasn't joined yet
        await callback_query.answer("Please join the channel first!", show_alert=True)

@Bot.on_message(filters.private & filters.command(["start"]))
async def start(bot, message, cb=False):
    user_id = message.chat.id
    print(f"Start command received from user {user_id}")
    
    # Check channel membership first
    is_member = await check_channel_membership(user_id)
    print(f"Channel membership check result for user {user_id}: {is_member}")
    
    if not is_member:
        verify_text = (
            "⚠️ Please join our official channel first!\n\n"
            "Join the channel to access the bot's features."
        )
        if cb:
            await message.reply_text(verify_text, reply_markup=VERIFY_BUTTONS)
        else:
            await message.reply_text(verify_text, reply_markup=VERIFY_BUTTONS)
        return
    
    # If user is in channel, proceed with normal start flow
    await add_user(user_id)
    
    # Check for referral code - only if it's a regular message with command
    if not cb and hasattr(message, 'command') and len(message.command) > 1:
        referrer_code = message.command[1]
        try:
            print(f"Processing referral code: {referrer_code}")
            # Get referrer's user ID from their referral code
            referrer = await db.col.find_one({"referral_code": referrer_code})
            if referrer and referrer["id"] != user_id:  # Can't refer yourself
                print(f"Found referrer: {referrer['id']}")
                # Process the referral
                success = await db.process_referral(user_id, referrer["id"])
                if success:
                    print(f"Referral processed successfully for user {user_id}")
                    # Notify referrer if they're not a bot
                    try:
                        # Get user info to check if they're a bot
                        referrer_info = await bot.get_users(referrer["id"])
                        if not referrer_info.is_bot:
                            await bot.send_message(
                                referrer["id"],
                                f"🎉 Congratulations! You've earned 50 BTS from a new referral!\n"
                                f"User @{message.from_user.username or message.from_user.first_name} joined using your referral link."
                            )
                            print(f"Notified referrer {referrer['id']} about new referral")
                        else:
                            print(f"Referrer {referrer['id']} is a bot, skipping notification")
                    except Exception as e:
                        print(f"Failed to notify referrer: {e}")
                else:
                    print(f"Failed to process referral for user {user_id}")
            else:
                print(f"Invalid referrer or self-referral attempt: {referrer_code}")
        except Exception as e:
            print(f"Error processing referral: {e}")
    
    # Get user info
    user = await db.get_user(user_id)
    balance = user.get('balance', 0)
    deposited_balance = user.get('deposited_balance', 0)
    
    # Format welcome message
    welcome_text = (
        START_TEXT
    )
    
    if cb:
        await message.edit_message_text(welcome_text, reply_markup=MAIN_BUTTONS)
    else:
        await message.reply_text(welcome_text, reply_markup=MAIN_BUTTONS)


@Bot.on_message(filters.private & filters.command(["help"]))
async def help(bot, message, cb=False):
    if cb:
        message = message.message
    await add_user(message.chat.id)
    await message.reply_text(
        text=HELP_TEXT,
        reply_markup=HELP_BUTTONS,
        disable_web_page_preview=True,
        quote=True,
    )


@Bot.on_message(filters.private & filters.command(["about"]))
async def about(bot, message, cb=False):
    if cb:
        message = message.message
    await add_user(message.chat.id)
    await message.reply_text(
        text=ABOUT_TEXT,
        reply_markup=ABOUT_BUTTONS,
        disable_web_page_preview=True,
        quote=True,
    )


@Bot.on_message(filters.private & filters.command(["trending"]))
async def trending(bot, message: Message):
    sticker = random.choice(WAITING)
    sticker_message = await message.reply_sticker(sticker)
    txt = await message.reply("⏳ Fetching the latest trending cryptocurrencies...")
    response = await get_trending_cryptos()
    await txt.delete()
    await sticker_message.delete()
    await message.reply_text(response, quote=True)


@Bot.on_message(filters.private & filters.command(["price"]))
async def price(bot, message):
    txt = await message.reply("⏳ Fetching Latest results for You !!")
    symbol = message.command[1] if len(message.command) > 1 else None
    if symbol:
        user_id = message.chat.id
        response = await get_crypto_price(symbol, user_id)
    else:
        response = "Please specify a cryptocurrency symbol. Usage: `/price BTC`"
    await message.reply_text(response, quote=True)
    await txt.delete()

@Bot.on_message(filters.private & filters.command(["historical"]))
async def historical(bot, message):
    if len(message.command) < 3:
        await message.reply_text(
            "Usage: `/historical BTC day` `/historical BTC hour`", quote=True
        )
        return

    txt = await message.reply_text("⏳ Fetching historical data...")

    symbol = message.command[1].upper()
    timeframe = message.command[2].lower()
    user_id = message.chat.id

    historical_data = await get_crypto_historical(symbol, user_id, timeframe)
    await txt.delete()
    await message.reply_text(historical_data)


@Bot.on_message(filters.private & filters.command(["coin"]))
async def coin(bot, message):
    txt = await message.reply("⏳ Fetching Latest Coin details for You !!")
    symbol = message.command[1] if len(message.command) > 1 else None
    if symbol:
        response = await get_coin_details(symbol)
    else:
        response = "Please specify a cryptocurrency symbol. Usage: `/coin DOGECOIN`"
    await message.reply_text(response, quote=True, disable_web_page_preview=True)
    await txt.delete()


@Bot.on_message(filters.private & filters.command(["exchanges"]))
async def exchanges(bot, message):
    txt = await message.reply("⏳ Fetching supported exchanges...")
    response = await get_exchanges()
    await message.reply_text(response, quote=True)
    await txt.delete()


@Bot.on_message(filters.private & filters.command(["market_data"]))
async def coin_market_data(bot, message):
    txt = await message.reply("⏳ Fetching market data...")
    symbol = message.command[1] if len(message.command) > 1 else None
    if symbol:
        response = await get_coin_market_data(symbol)
        await txt.delete()
    else:
        response = (
            "Please specify a cryptocurrency symbol. Usage: /market_data <symbol>"
        )
        await txt.delete()
    await message.reply_text(response, quote=True)


@Bot.on_message(filters.private & filters.command(["exchange_rates"]))
async def exchange_rates(bot, message):
    txt = await message.reply("⏳ Fetching Exchange Rates for You !!")
    response = await get_exchange_rates()
    await message.reply_text(response, quote=True)
    await txt.delete()


@Bot.on_message(filters.private & filters.command(["exchange"]))
async def exchange(bot, message):
    txt = await message.reply("⏳ Fetching market data...")
    symbol = message.command[1] if len(message.command) > 1 else None
    if symbol:
        response = await get_coin_exchanges(symbol)
        if not response:
            response = (
                "Please specify a cryptocurrency symbol. Usage: /exchange DOGECOIN"
            )
        await txt.delete()
    else:
        response = "Please specify a cryptocurrency symbol. Usage: /exchange DOGECOIN"
        await txt.delete()
    await message.reply_text(response, quote=True)


@Bot.on_message(filters.private & filters.command(["live_prices"]))
async def live_prices(bot, message):
    sticker = random.choice(WAITING)
    sticker_message = await message.reply_sticker(sticker)
    user_id = message.chat.id
    user = await db.get_user(user_id)
    currency = user.get("currency", "usd")
    symbols = [
        "bitcoin",
        "ethereum",
        "binancecoin",
        "ripple",
        "cardano",
        "solana",
        "polkadot",
        "dogecoin",
        "shiba-inu",
        "litecoin",
    ]

    live_message = await message.reply_text(
        "🔄 Fetching live prices for popular coins..."
    )

    try:
        prev_prices = {symbol: None for symbol in symbols}  # Initialize previous prices

        start_time = datetime.now(pytz.utc)
        end_time = start_time + timedelta(minutes=2)
        last_update = start_time

        while datetime.now(pytz.utc) < end_time:
            current_prices = await fetch_live_prices(symbols, currency)
            if not current_prices:
                await asyncio.sleep(10)  # Wait for 10 seconds before retrying
                continue

            formatted_message = format_prices_message(
                symbols, current_prices, prev_prices
            )

            # Update message only if the last update time has changed
            current_time = datetime.now(pytz.utc)
            if current_time > last_update:
                updated_message = f"{formatted_message}\n\n🕒 Updated on: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"

                try:
                    await live_message.edit_text(updated_message)
                    last_update = current_time
                except Exception as e:
                    print(f"❌ Error occurred while updating message: {e}")

            await asyncio.sleep(10)
            prev_prices = current_prices

    except asyncio.CancelledError:
        pass

    except Exception as e:
        print(f"❌ Error occurred: {e}")

    await live_message.edit_text(
        "⏹️ Live price updates stopped."
    )
    await sticker_message.delete()  

@Bot.on_message(filters.private & filters.command(["balance"]))
async def balance_command(bot, message):
    user_id = message.chat.id
    await add_user(user_id)
    
    # Get fresh user data
    user = await db.get_user(user_id)
    mined_balance = user.get('balance', 0)
    deposited_balance = user.get('deposited_balance', 0)
    
    # Format the balance message
    await message.reply_text(
        f"💰 Your Balances:\n\n"
        f"⛏️ Traded Balance: {mined_balance} tokens\n"
        f"💳 Deposited Balance: ${deposited_balance:.2f}",
        quote=True
    )  