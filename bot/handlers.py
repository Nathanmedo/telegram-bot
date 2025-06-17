from pyrogram import Client, filters
from pyrogram.types import Message
from .client import Bot
from .withdraw import (
    handle_wallet_input_logic,
    handle_withdrawal_input_logic
)
from .deposit import (
    handle_deposit_input_logic
)
from .upgrade import (
    handle_upgrade_input_logic
)
from .clear_states import deposit_state_object, withdrawal_state_object, upgrade_states_object
import asyncio
from datetime import datetime, timedelta



@Bot.on_message(filters.private & filters.text)
async def handle_text_input(client: Client, message: Message):
    """Central handler for all text input"""
    # Skip if command
    print(f"[DEBUG] Received message: {message.text}")
    if message.text.startswith('/'):
        print(f"[DEBUG] Skipping command: {message.text}")
        return
        
    user_id = message.chat.id
    text = message.text.strip()
    
    try:
        # Check withdrawal states first (wallet address or amount)
        if "user_id" in withdrawal_state_object:
            state = withdrawal_state_object["state"]
            print(f"[DEBUG] User in withdrawal state, step: {state}")
            if state == "wallet_input":
                await handle_wallet_input_logic(client, message, text)
            elif state == "withdrawal_input":
                await handle_withdrawal_input_logic(client, message, text)
            return
            
        # Check deposit states
        if "user_id" in deposit_state_object:
            state = deposit_state_object["state"]
            print(f"[DEBUG] User  in deposit state, step: {state}")
            if state == "amount":
                await handle_deposit_input_logic(client, message, text)
            return
            
        # Check upgrade states
        if "user_id" in upgrade_states_object:
            state = upgrade_states_object["state"]
            if state == "select_robot":
                await handle_upgrade_input_logic(client, message, text)
            return
            
        print(f"[DEBUG] No matching state found for user {user_id}")
            
    except Exception as e:
        print(f"[DEBUG] Error in handle_text_input: {e}")
        # Clear states on error
        if "user_id" in withdrawal_state_object:
            del withdrawal_state_object["user_id"]
        if "user_id" in deposit_state_object:
            del deposit_state_object["user_id"]
        if "user_id" in upgrade_states_object:
            del upgrade_states_object["user_id"]
        await message.reply_text("❌ An error occurred. Please try again.")

# Start the state cleanup tas # Check every minute 