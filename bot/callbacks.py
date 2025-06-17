from bot.buttons import SETTINGS_BUTTONS
from .admin import add_user
from pyrogram import Client, filters
from .commands import start, help, about, MAIN_BUTTONS
from .mining import mine_callback
from .deposit import (
    show_deposit_menu,
    handle_select_currency,
    handle_complete_deposit,
    handle_cancel_deposit
)
from .withdraw import (
    handle_withdraw_callback,
    handle_set_wallet_callback,
    handle_confirm_withdrawal,
    handle_approve_withdrawal_callback,
    handle_cancel_withdrawal
)
from .upgrade import (
    handle_upgrade_command,
    handle_confirm_upgrade,
    handle_approve_upgrade_callback,
    handle_cancel_upgrade
)
from .referral import handle_referral_command
from .client import Bot
from .database import db
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


@Bot.on_callback_query()
async def cb_data(client, callback_query):
    try:
        await add_user(callback_query.from_user.id)
        
        if callback_query.data == "home":
            await start(client, callback_query.message, cb=True)
        elif callback_query.data == "help":
            await help(client, callback_query.message, cb=True)
        elif callback_query.data == "about":
            await about(client, callback_query.message, cb=True)
        elif callback_query.data == "settings":
            await callback_query.edit_message_text(
                "Settings:",
                reply_markup=SETTINGS_BUTTONS
            )
        elif callback_query.data == "trade":
            await mine_callback(client, callback_query)
        elif callback_query.data == "deposit":
            await show_deposit_menu(client, callback_query)
        elif callback_query.data == "referral":
            await handle_referral_command(client, callback_query.message)
        elif callback_query.data == "view_ads":
            # Add 0.2 BTS to user's balance
            user_id = callback_query.from_user.id
            user = await db.get_user(user_id)
            current_balance = user.get('balance', 0)
            new_balance = current_balance + 0.2
            
            # Update balance
            await db.update_balance(user_id, new_balance)
            
            # Create buttons for the response
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Visit Website", url="https://otieu.com/4/9455388")],
                [InlineKeyboardButton("✅ I've Visited", callback_data="ads_complete")]
            ])
            
            await callback_query.edit_message_text(
                f"📺 View ads to earn more BTS!\n\n"
                f"💰 You've earned 0.2 BTS!\n"
                f"💵 New balance: {new_balance} BTS\n\n"
                f"Visit the website and click 'I've Visited' to continue.",
                reply_markup=buttons
            )
        elif callback_query.data == "ads_complete":
            await callback_query.edit_message_text(
                "✅ Thank you for viewing the ads!\n\n"
                "You can view more ads to earn more BTS.",
                reply_markup=MAIN_BUTTONS
            )
        elif callback_query.data.startswith("deposit_"):
            if callback_query.data == "deposit_cancel":
                await handle_cancel_deposit(client, callback_query)
            elif callback_query.data == "deposit_complete":
                await handle_complete_deposit(client, callback_query)
            else:
                await handle_select_currency(client, callback_query)
        elif callback_query.data == "withdraw":
            await handle_withdraw_callback(client, callback_query)
        elif callback_query.data == "set_wallet":
            await handle_set_wallet_callback(client, callback_query)
        elif callback_query.data == "upgrade":
            await handle_upgrade_command(client, callback_query.message)
        elif callback_query.data == "confirm_upgrade":
            await handle_confirm_upgrade(client, callback_query)
        elif callback_query.data.startswith("approve_upgrade_"):
            await handle_approve_upgrade_callback(client, callback_query)
        elif callback_query.data == "upgrade_cancel":
            await handle_cancel_upgrade(client, callback_query)
        elif callback_query.data == "confirm_withdraw":
            await handle_confirm_withdrawal(client, callback_query)
        elif callback_query.data.startswith("approve_withdrawal_"):
            await handle_approve_withdrawal_callback(client, callback_query)
        elif callback_query.data == "withdraw_cancel":
            await handle_cancel_withdrawal(client, callback_query)
        elif callback_query.data == "close":
            await callback_query.message.delete()
    except Exception as e:
        print(f"Error in callback: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)


@Bot.on_message(filters.private & filters.command(["settings"]))
async def settings(client, message):
    await message.reply_text(
        "Settings:",
        reply_markup=SETTINGS_BUTTONS
    )
