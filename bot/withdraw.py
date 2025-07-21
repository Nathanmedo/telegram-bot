from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from .database import db
from .crypto_utils import get_crypto_price
from .vars import ADMINS, BOT_LINK
from .client import Bot
from .admin import add_user
from datetime import datetime
from .clear_states import clear_stale_states, withdrawal_state_object

withdrawal_states = {}



# Withdrawal buttons
WITHDRAW_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")],
    [InlineKeyboardButton("❌ Cancel", callback_data="withdraw_cancel")]
])

SET_WALLET_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("💳 Set BTC Wallet", callback_data="set_wallet")],
    [InlineKeyboardButton("❌ Cancel", callback_data="withdraw_cancel")]
])

CONFIRM_WITHDRAW_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ Confirm Withdrawal", callback_data="confirm_withdraw")],
    [InlineKeyboardButton("❌ Cancel", callback_data="withdraw_cancel")]
])

@Bot.on_message(filters.private & filters.command(["withdraw"]))
async def handle_withdraw_command(client: Client, message: Message):
    """Handle /withdraw command"""
    await clear_stale_states()  # Clear any stale states before processing new command
    user_id = message.chat.id
    print(f"[DEBUG] Withdraw command from user {user_id}")
    
    withdrawal_state_object["user_id"] = user_id
    withdrawal_state_object['state'] = 'withdrawal_input'

    if user_id in db.cache:
        del db.cache[user_id]
    
    # Get user's wallet address
    user = await db.get_user(user_id)
    wallet_address = user.get("wallet_address")
    print(wallet_address)
    print(f"[DEBUG] Retrieved wallet address for user {user_id}: {wallet_address}")
    
    if not wallet_address:
        print(f"[DEBUG] No wallet address found for user {user_id}, showing set wallet button")
        await message.reply_text(
            "⚠️ You need to set up your BTC wallet address first!\n\n"
            "Use /set_wallet to set your BTC wallet address.",
            reply_markup=SET_WALLET_BUTTON
        )
        return
    
    # Get user's balance
    balance = user.get("balance", 0)
    print(f"[DEBUG] User {user_id} balance: {balance}")
    
    # Get BTC price to convert balance
    price_info = await get_crypto_price("BTC", user_id)
    if "Could not fetch" in price_info:
        print(f"[DEBUG] Failed to fetch BTC price for user {user_id}")
        await message.reply_text("Error fetching BTC price. Please try again later.")
        return
    
    # Extract price from the response
    price_str = price_info.split("$")[1].split()[0]
    price_usd = float(price_str)
    print(f"[DEBUG] BTC price in USD: {price_usd}")
    
    # Calculate BTC equivalent
    balance_btc = balance / (price_usd * 1000)  # Since 1 USD = 1000 tokens
    
    # Calculate min and max BTC amount based on USD limits
    min_usd = 3.0
    max_usd = 100.0
    min_btc = min_usd / price_usd
    max_btc = max_usd / price_usd
    
    # Store state for withdrawal input
    withdrawal_states[user_id] = {
        "step": "withdrawal_input",
        "message_id": message.id,
        "balance_btc": balance_btc,
        "price_usd": price_usd,
        "wallet_address": wallet_address,
        "timestamp": datetime.now()
    }
    print(f"[DEBUG] Stored withdrawal state for user {user_id}: {withdrawal_states[user_id]}")
    
    await message.reply_text(
        f"📤 Withdraw your earnings\n\n"
        f"💰 Available balance: {balance_btc:.8f} BTC  ( {balance} tokens )\n\n"
        f"Withdrawal limits:\n"
        f"• Minimum: ${min_usd:.2f}  ( {min_btc:.8f} BTC )\n"
        f"• Maximum: ${max_usd:.2f} ( {max_btc:.8f} BTC )\n"
        f"• Fee: $1.00 (deducted from withdrawal amount)\n\n"
        f"Please enter the amount you want to withdraw in USD (between $3 and $100).\n"
        f"Enter /cancel to cancel this operation."
    )

@Bot.on_message(filters.private & filters.command(["set_wallet"]))
async def handle_set_wallet_command(client: Client, message: Message):
    """Handle /set_wallet command"""
    await clear_stale_states()  # Clear any stale states before processing new command
    user_id = message.chat.id
    withdrawal_state_object["user_id"] = user_id
    withdrawal_state_object['state'] = 'wallet_input'
    # Ensure user exists in database
    await add_user(user_id)
    
    # Store state for wallet input
    withdrawal_states[user_id] = {
        "step": "wallet_input",
        "message_id": message.id,
        "timestamp": datetime.now()
    }
    
    await message.reply_text(
        "💳 Please enter your BTC wallet address.\n\n"
        "⚠️ Important: Make sure to enter a valid BTC address. "
        "Incorrect addresses may result in permanent loss of funds.\n\n"
        "Enter /cancel to cancel this operation."
    )

async def handle_wallet_input_logic(client: Client, message: Message, text: str):
    """Handle wallet address input"""
    user_id = message.chat.id
    
    # Validate BTC address format
    if not text.startswith(('1', '3', 'bc1')):
        await message.reply_text("❌ Invalid BTC address format. Please enter a valid BTC address.")
        return
    
    # Save wallet address
    success = await db.set_wallet_address(user_id, text)
    if not success:
        await message.reply_text("❌ Failed to save wallet address. Please try again.")
        return
    
    # Clear the state after successful save
    if user_id in withdrawal_states:
        del withdrawal_states[user_id]
    
    await message.reply_text(
        "✅ Wallet address saved successfully!\n\n"
        "You can now use /withdraw to withdraw your funds."
    )

async def handle_withdrawal_input_logic(client: Client, message: Message, text: str):
    """Handle withdrawal amount input"""
    user_id = message.chat.id
    print(f"[DEBUG] Processing withdrawal input for user {user_id}: {text}")
    
    if user_id not in withdrawal_states:
        print(f"[DEBUG] No withdrawal state found for user {user_id}")
        return
        
    state = withdrawal_states[user_id]
    print(f"[DEBUG] Current withdrawal state: {state}")
    
    try:
        amount_usd = float(text)
        if amount_usd <= 0:
            await message.reply_text("❌ Please enter a positive amount in USD.")
            return
        # Check min/max
        if amount_usd < 3.0:
            await message.reply_text("❌ Minimum withdrawal is $3.00.")
            return
        if amount_usd > 100.0:
            await message.reply_text("❌ Maximum withdrawal is $100.00.")
            return
        # Apply $1 fee
        amount_usd_after_fee = amount_usd - 1.0
        if amount_usd_after_fee <= 0:
            await message.reply_text("❌ Amount after fee must be positive. Please enter a higher amount.")
            return
        # Convert to BTC
        price_usd = state["price_usd"]
        amount_btc = amount_usd_after_fee / price_usd
        # Check if user has enough balance (in tokens)
        user = await db.get_user(user_id)
        balance = user.get("balance", 0) if user else 0
        if amount_usd > (balance / 1000):
            await message.reply_text(f"❌ Insufficient balance. Your balance is {balance} tokens (${balance/1000:.2f}).")
            return
        state["amount_usd"] = amount_usd
        state["amount_btc"] = amount_btc
        state["step"] = "confirm"
        print(f"[DEBUG] Updated withdrawal state for user {user_id}: {state}")
        await message.reply_text(
            f"💎 Withdraw ${amount_usd:.2f} (after $1 fee: ${amount_usd_after_fee:.2f})\n"
            f"Equivalent to: {amount_btc:.8f} BTC\n"
            f"To: {state['wallet_address']}\n\n"
            "Please confirm your withdrawal:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm", callback_data="confirm_withdrawal")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_withdrawal")]
            ])
        )
        
    except ValueError:
        print(f"[DEBUG] Invalid number format for user {user_id}: {text}")
        await message.reply_text("❌ Please enter a valid number in USD.")
    except Exception as e:
        print(f"[DEBUG] Error in withdrawal input: {str(e)}")
        await message.reply_text("❌ An error occurred. Please try again.")


async def handle_text_input(client: Client, message: Message):
    """Central handler for all text input"""
    # Skip if command
    if message.text.startswith('/'):
        return
        
    user_id = message.chat.id
    text = message.text.strip()
    print(f"[DEBUG] Text input received from user {user_id}: {text}")
    
    # Check withdrawal states first (wallet address or amount)
    if user_id in withdrawal_states:
        state = withdrawal_states[user_id]
        print(f"[DEBUG] Found withdrawal state for user {user_id}: {state}")
        
        if state["step"] == "wallet_input":
            print(f"[DEBUG] Processing wallet input for user {user_id}")
            await handle_wallet_input_logic(client, message, text)
        elif state["step"] == "withdrawal_input":
            print(f"[DEBUG] Processing withdrawal input for user {user_id}")
            await handle_withdrawal_input_logic(client, message, text)
        return
    else:
        print(f"[DEBUG] No withdrawal state found for user {user_id}")

@Bot.on_callback_query(filters.regex("^withdraw$"))
async def handle_withdraw_callback(client: Client, callback_query: CallbackQuery):
    """Handle withdraw button click"""
    user_id = callback_query.from_user.id
    
    # Check if user has wallet address
    wallet_address = await db.get_wallet_address(user_id)
    if not wallet_address:
        await callback_query.edit_message_text(
            "⚠️ You need to set up your BTC wallet address first!\n\n"
            "Use /set_wallet to set your BTC wallet address.",
            reply_markup=SET_WALLET_BUTTON
        )
        return
    
    # If user has wallet, proceed with withdrawal
    await handle_withdraw_command(client, callback_query.message)

@Bot.on_callback_query(filters.regex("^set_wallet$"))
async def handle_set_wallet_callback(client: Client, callback_query: CallbackQuery):
    """Handle set wallet button click"""
    await handle_set_wallet_command(client, callback_query.message)

@Bot.on_callback_query(filters.regex("^confirm_withdrawal$"))
async def handle_confirm_withdrawal(client: Client, callback_query: CallbackQuery):
    """Handle withdrawal confirmation"""
    user_id = callback_query.from_user.id
    print(f"[DEBUG] Confirm withdrawal callback from user {user_id}")
    
    if user_id not in withdrawal_states:
        print(f"[DEBUG] No withdrawal state found for user {user_id}")
        await callback_query.answer("Invalid withdrawal state", show_alert=True)
        return
        
    state = withdrawal_states[user_id]
    print(f"[DEBUG] Current withdrawal state: {state}")
    
    if state["step"] != "confirm":
        print(f"[DEBUG] Invalid step in withdrawal state: {state['step']}")
        await callback_query.answer("Invalid withdrawal state", show_alert=True)
        return
    
    try:
        # Get withdrawal details
        amount_btc = state["amount_btc"]
        amount_tokens = amount_btc * state["price_usd"] * 1000  # Convert BTC to tokens
        
        # Get wallet address
        wallet_address = state["wallet_address"]
        if not wallet_address:
            await callback_query.answer("Please set your wallet address first using /set_wallet", show_alert=True)
            return
        
        # Store withdrawal request
        await db.add_pending_withdrawal(user_id, amount_btc, amount_tokens)
        print(f"[DEBUG] Added pending withdrawal for user {user_id}: {amount_btc} BTC")
        
        # Create approve button for admin
        approve_button = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"✅ Approve Withdrawal ({amount_btc:.8f} BTC)",
                callback_data=f"approve_withdrawal_{user_id}_{amount_btc}"
            )]
        ])
        
        # Clear withdrawal state
        del withdrawal_states[user_id]
        print(f"[DEBUG] Cleared withdrawal state for user {user_id}")
        
        # Notify user
        await callback_query.edit_message_text(
            f"✅ Withdrawal request submitted!\n\n"
            f"Amount: {amount_btc:.8f} BTC\n"
            f"To address: {wallet_address}\n\n"
            f"Your withdrawal is being processed. You will be notified once it's approved."
        )
        
        # Notify admins
        user = await db.get_user(user_id)  # Fetch latest user info for extra fields
        robot_counts = user.get("robot_counts", {})
        robot_counts_str = "\n".join([
            f"• Robot {level}: {count}x" for level, count in robot_counts.items() if count > 0
        ]) or "No robots"
        ads_completed_count = user.get("ads_completed_count", 0)
        ads_completed_after_withdrawal = user.get("ads_views_since_withdraw", 0)
        last_bts_withdrawal = user.get("last_bts_withdrawal", 0.0)
        last_withdrawal_date = user.get("last_withdrawal_date", "N/A")
        for admin_id in ADMINS:
            try:
                await client.send_message(
                    admin_id,
                    f"🛎️ New Withdrawal Request\n\n"
                    f"User: @{callback_query.from_user.username or callback_query.from_user.first_name}\n"
                    f"Amount: {amount_btc:.8f} BTC\n"
                    f"To address: {wallet_address}\n\n"
                    f"Current Robot(s):\n{robot_counts_str}\n"
                    f"Ads Completed Since Last Withdrawal: {ads_completed_after_withdrawal}\n"
                    f"Total Ads Views: {ads_completed_count}\n"
                    f"Last BTS Withdrawal: {last_bts_withdrawal:.8f} BTC\n"
                    f"Last Withdrawal Date: {last_withdrawal_date}\n\n"
                    f"Click the button below to approve:",
                    reply_markup=approve_button
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
        
        # Send message to channel
        try:
            # Get user details for the channel message
            user_info = await client.get_users(user_id)
            username = user_info.username or "No username"
            first_name = user_info.first_name or "No name"
            
            await client.send_message(
                "BTS_bot_payment",
                f"📤 New Withdrawal Request\n\n"
                f"🔸Name: {first_name}\n"
                f"🔸Username: @{username}\n"
                f"🔸ID: {user_id}\n"
                f"💸 Amount: {amount_btc:.8f} BTC\n"
                f"📝 To address: {wallet_address}\n\n"
                f"Withdrawal is being processed...\n\n"
                f"🤖 Bot: BTS Trading: ({BOT_LINK}) ™"
            )
        except Exception as e:
            print(f"Failed to send channel message: {e}")
            
    except Exception as e:
        print(f"Error in confirm_withdrawal: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)

@Bot.on_callback_query(filters.regex("^approve_withdrawal_"))
async def handle_approve_withdrawal_callback(client: Client, callback_query: CallbackQuery):
    """Handle withdrawal approval from callback"""
    # Check if user is admin
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("❌ You are not authorized to approve withdrawals.", show_alert=True)
        return
    
    try:
        # Parse callback data
        data = callback_query.data.replace('approve_withdrawal_', '')
        user_id, amount = data.split('_', 1)
        user_id = int(user_id)
        
        # Get user info
        user = await db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ User not found.", show_alert=True)
            return
        
        # Get and approve pending withdrawal
        withdrawal = await db.approve_withdrawal(user_id)
        if not withdrawal:
            await callback_query.answer("❌ No pending withdrawal found.", show_alert=True)
            return
        
        # Get updated user info
        user = await db.get_user(user_id)
        new_balance = user.get("balance", 0)
        
        # Send confirmation to admin
        await callback_query.answer("✅ Withdrawal approved successfully!", show_alert=True)
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                f"✅ Your withdrawal has been approved!\n\n"
                f"Amount: {withdrawal['amount_btc']:.8f} BTC\n"
                f"To address: {await db.get_wallet_address(user_id)}\n\n"
                f"💰 New balance: {new_balance} tokens"
            )
            
            # Send message to channel
            try:
                # Get user details for the channel message
                user_info = await client.get_users(user_id)
                username = user_info.username or "No username"
                first_name = user_info.first_name or "No name"
                
                await client.send_message(
                    "BTS_bot_payment",
                    f"✅ Withdrawal Completed ✅\n\n"
                    f"🔸Name: {first_name}\n"
                    f"🔸Username: @{username}\n"
                    f"🔸ID: {user_id}\n"
                    f"💸 Amount: {withdrawal['amount_btc']:.8f} BTC\n"
                    f"📝 To address: {await db.get_wallet_address(user_id)}\n\n"
                    f"Withdrawal has been processed successfully!\n\n"
                    f"🤖 Bot: BTS Trading: ({BOT_LINK})"
                )
            except Exception as e:
                print(f"Failed to send channel message: {e}")
            
            # Delete the approval message
            await callback_query.message.delete()
            
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")
            await callback_query.edit_message_text(
                f"⚠️ Withdrawal approved but user notification failed!\n\n"
                f"User: {user_id}\n"
                f"Amount: {withdrawal['amount_btc']:.8f} BTC\n"
                f"New balance: {new_balance} tokens\n\n"
                f"Error: {str(e)}\n"
                f"Please notify the user manually."
            )
            
    except Exception as e:
        print(f"Error in approve_withdrawal_callback: {str(e)}")
        await callback_query.answer("❌ An error occurred", show_alert=True)

@Bot.on_callback_query(filters.regex("^cancel_withdrawal$"))
async def handle_cancel_withdrawal(client: Client, callback_query: CallbackQuery):
    """Cancel withdrawal process"""
    user_id = callback_query.from_user.id
    if user_id in withdrawal_states:
        del withdrawal_states[user_id]
    
    await callback_query.edit_message_text("❌ Withdrawal cancelled.")

@Bot.on_message(filters.private & filters.command(["cancel"]))
async def handle_cancel_withdraw_command(client: Client, message: Message):
    user_id = message.chat.id
    if user_id in withdrawal_states:
        del withdrawal_states[user_id]
    await message.reply_text("❌ Withdrawal cancelled.")
    # Optionally, you can show the main menu or other navigation here 