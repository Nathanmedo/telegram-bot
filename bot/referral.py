from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from .database import db
from .client import Bot
from .admin import add_user
from .commands import MAIN_BUTTONS

REFERRAL_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("📤 Share Bot", url="https://t.me/BamCryptoTradingBot")],
    [InlineKeyboardButton("❌ Close", callback_data="close")]
])

async def handle_referral_command(client: Client, message: Message):
    """Handle /referral command"""
    print(message)
    user_id = message.chat.id
    await add_user(user_id)
    
    # Get referral stats
    stats = await db.get_referral_stats(user_id)
    if not stats:
        await message.reply_text("❌ Error getting referral stats. Please try again.")
        return
    
    # Build referral message
    message_text = (
        "🤝 **Referral Program**\n\n"
        f"Your Referral Code: `{stats['referral_code']}`\n\n"
        f"Total Referrals: {stats['referral_count']}\n"
        f"Total Earnings: {stats['referral_earnings']} BTS\n\n"
        "**How it works:**\n"
        "1. Share your referral link with friends\n"
        "2. When they join using your link, you get 50 BTS\n"
        "3. The more friends you invite, the more you earn!\n\n"
        "Share your referral link:"
    )
    
    # Create referral link
    referral_link = f"https://t.me/BamCryptoTradingBot?start={stats['referral_code']}"
    
    # Create buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Share Referral Link", url=referral_link)],
        [InlineKeyboardButton("❌ Close", callback_data="close")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="start")]
    ])
    
    if isinstance(message, CallbackQuery):
        await message.edit_message_text(message_text, reply_markup=buttons)
    else:
        await message.reply_text(message_text, reply_markup=buttons)

@Bot.on_message(filters.private & filters.command(["referral"]))
async def referral_command(client: Client, message: Message):
    """Handle /referral command"""
    await handle_referral_command(client, message)

@Bot.on_callback_query(filters.regex("^close$"))
async def handle_close_callback(client: Client, callback_query: CallbackQuery):
    """Handle close button callback"""
    await callback_query.message.delete() 