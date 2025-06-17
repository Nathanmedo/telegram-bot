from datetime import datetime, timedelta
from pyrogram import Client, filters
from .database import db
from .buttons import MINING_BUTTONS
from .client import Bot
from .constants import ROBOT_PRICES, ROBOT_RATES
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def get_mining_data(user_id):
    print("getting mining data", user_id)
    user = await db.get_user(user_id)
    if not user:
        return None
    
    mining_data = user.get('mining_data', {})
    last_mined = mining_data.get('last_mined')
    print("Mining data:", mining_data, "Last mined:", last_mined)
    
    if last_mined:
        try:
            last_mined = datetime.fromisoformat(last_mined)
            time_diff = datetime.now() - last_mined
            if time_diff < timedelta(hours=1):
                return False, last_mined
        except Exception as e:
            print(f"Error parsing last_mined time: {e}")
            # If there's an error parsing the time, allow mining
            return True, None
    
    return True, last_mined

async def update_mining_data(user_id, mined_amount):
    current_time = datetime.now().isoformat()
    # First get the current user data
    user = await db.get_user(user_id)
    current_balance = user.get('balance', 0)
    new_balance = current_balance + mined_amount
    
    # Update with the new balance and mining data
    await db.update_balance(user_id, new_balance)
    await db.col.update_one(
        {'id': int(user_id)},
        {
            '$set': {
                'mining_data': {
                    'last_mined': current_time,
                    'total_mined': mined_amount
                }
            }
        }
    )

def get_upgrade_suggestion(user_id, current_level):
    """Generate upgrade suggestion based on current robot level"""
    if current_level >= 7:
        return None
    
    next_level = current_level + 1
    price = ROBOT_PRICES[next_level]
    return f"\n\n💡 Want to trade faster? Upgrade to Robot {next_level} for ${price} using /upgrade"

@Bot.on_message(filters.private & filters.command(["mine"]))
async def mine_command(bot, message):
    user_id = message.chat.id
    can_mine, last_mined = await get_mining_data(user_id)
    
    if not can_mine:
        time_left = timedelta(hours=1) - (datetime.now() - last_mined)
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        await message.reply_text(
            f"⏳ You need to wait {hours}h {minutes}m before mining again!",
            quote=True
        )
        return
    
    # Create redirect button only
    redirect_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Visit Website", url="https://otieu.com/4/9455388")],
        [InlineKeyboardButton("✅ I've Visited", callback_data="redirect_mining")]
    ])
    
    await message.reply_text(
        "⛏️ First, visit our website, then click 'I've Visited' to start mining!",
        reply_markup=redirect_button,
        quote=True
    )

@Bot.on_callback_query(filters.regex("^redirect_mining$"))
async def handle_redirect_mining(bot, callback_query):
    user_id = callback_query.from_user.id
    mining_rate = await db.calculate_mining_rate(user_id)
    current_level = await db.get_robot_level(user_id)
    
    upgrade_suggestion = get_upgrade_suggestion(user_id, current_level)
    
    # Create mining button
    mining_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("⛏️ Start Trading", callback_data="mine")]
    ])
    
    await callback_query.edit_message_text(
        f"⛏️ Click the button below to start mining!\n"
        f"Current mining rate: {mining_rate} BTS per hour{upgrade_suggestion or ''}",
        reply_markup=mining_button
    )

@Bot.on_callback_query(filters.regex("^mine$"))
async def mine_callback(bot, callback_query):
    user_id = callback_query.from_user.id
    can_mine, last_mined = await get_mining_data(user_id)
    print("Can mine:", can_mine, "Last mined:", last_mined)
    
    if not can_mine:
        time_left = timedelta(hours=1) - (datetime.now() - last_mined)
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        await callback_query.answer(f"⏳ Wait {hours}h {minutes}m before mining again!", show_alert=True)
        return
    
    # Calculate mining amount based on robot level
    mining_rate = await db.calculate_mining_rate(user_id)
    mined_amount = mining_rate  # Amount per hour
    
    await update_mining_data(user_id, mined_amount)
    
    # Get fresh user data after update
    user = await db.get_user(user_id)
    new_balance = user.get('balance', 0)
    current_level = await db.get_robot_level(user_id)
    
    upgrade_suggestion = get_upgrade_suggestion(user_id, current_level)
    
    await callback_query.answer("⛏️ Mining successful!", show_alert=True)
    await callback_query.edit_message_text(
        f"⛏️ You Traded {mined_amount} BTS!\n"
        f"💰 Your new balance: {new_balance} BTS\n"
        f"Current mining rate: {mining_rate} BTS per hour{upgrade_suggestion or ''}"
    )

