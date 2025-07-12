from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from .database import db
from .buttons import DEPOSIT_BUTTONS, DEPOSIT_CONFIRM_BUTTON
from .crypto_utils import get_crypto_price
import asyncio
from datetime import datetime, timedelta
import pytz
from .vars import ADMINS, BOT_LINK, NOWPAYMENTS_API_KEY, BASE_URL
from .client import Bot
from .clear_states import deposit_state_object, clear_stale_states
import string
import random
import requests


deposit_states={}

NOWPAYMENTS_API_URL= 'https://api.nowpayments.io/v1/payment' 

# Deposit addresses (replace with actual addresses)
DEPOSIT_ADDRESSES = {
    "btc": "bc1qqdc0du7kmfa6m6ga3jsrq439rw0sv2r7ekzfj8",
    "eth": "0x83D239C8198654942F2D37271a9c61208E45669D",
    "doge": "DJ9cwuz5Qw9W13843MkG7maUaiCtA734tt",
    "ltc": "ltc1qz870xpu5haea28vcn6r7ruv49j2u28pk5jdkwa",
    "dash": "XqYZc46D16Jq3jCqXCtD21nt8pa681DgU7",
    "etc": "0x00bdeA8FcA8cBD30ae61d32e8693d09cbC4f76aB",
    "bch": "qrray44nvclqv272xkvfq403cuutga5f353zvgkfw8",
    "sol": "J6Zw7m2RygAVqKKWc9h4JUNzwoas6yNjR4gVaKdbabSa",
}

# Deposit limits and fees (in USD)
DEPOSIT_LIMITS = {
    "min": 10,  # $10
    "max": 1000,  # $100000
    "fee": 1.00  # $1 fee
}

async def get_deposit_info(currency: str, amount: float, user_id: int) -> tuple:
    """Get deposit information including rates and conversion"""
    try:
        # Get current price in USD
        price_info = await get_crypto_price(currency, user_id)
        if "Could not fetch" in price_info:
            return None, None, None
        
        # Extract price from the response
        price_str = price_info.split("$")[1].split()[0]
        price_usd = float(price_str)
        
        # Calculate amounts
        amount_usd = amount * price_usd
        fee_amount = DEPOSIT_LIMITS["fee"] / price_usd  # Convert fee to crypto amount
        handyearn_amount = int(amount_usd * 1000)  # 1 USD = 1000 BTS
        bonus = int(handyearn_amount * 0.1)  # 10% bonus
        
        return price_usd, fee_amount, (handyearn_amount, bonus)
    except Exception as e:
        print(f"Error getting deposit info: {e}")
        return None, None, None

async def show_deposit_menu(client: Client, message_or_callback):
    """Show deposit menu - works with both message and callback"""
    text = (
        "🔌 **Automatic Deposits**\n\n"
        "Here you can deposit cryptocurrencies to earn more and faster.\n"
        "Your deposit will be converted automatically into 🏵 BTS. Use this amount to buy extractors.\n\n"
        "Don't you have cryptocurrencies?\n"
        "Deposit using Telegram ⭐️ Stars.\n"
        "(permanent bonus is not available with this deposit method)\n\n"
        "How to use cryptocurrency (https://telegra.ph/How-to-use-cryptocurrencies-04-14)"
    )
    
    if hasattr(message_or_callback, 'edit_message_text'):
        # It's a callback query
        await message_or_callback.edit_message_text(text, reply_markup=DEPOSIT_BUTTONS)
    else:
        # It's a message
        await message_or_callback.reply_text(text, reply_markup=DEPOSIT_BUTTONS)

@Bot.on_message(filters.private & filters.command(["deposit"]))
async def handle_deposit_command(client: Client, message: Message):
    """Handle /deposit command"""
    await show_deposit_menu(client, message)

@Bot.on_callback_query(filters.regex("^deposit$"))
async def handle_deposit_menu(client: Client, callback_query: CallbackQuery):
    """Handle deposit menu callback"""
    await show_deposit_menu(client, callback_query)

@Bot.on_callback_query(filters.regex("^deposit_(btc|eth|doge|ltc|dash|etc|bch|sol|stars)$"))
async def handle_select_currency(client: Client, callback_query: CallbackQuery):
    """Handle currency selection"""
    currency = callback_query.data.split("_")[1].upper()
    user_id = callback_query.from_user.id
    
    await clear_stale_states()
    deposit_state_object["user_id"] = user_id
    deposit_state_object["state"] = "amount"

    # Store currency selection in state
    deposit_states[user_id] = {
        "currency": currency,
        "step": "amount",
        "message_id": callback_query.message.id,
        "timestamp": datetime.now()
    }
    
    # Get current price for limits
    price_info = await get_crypto_price(currency, user_id)
    if "Could not fetch" in price_info:
        await callback_query.answer("Error fetching price. Please try again.", show_alert=True)
        return
    
    try:
        # Extract price from the response
        price_str = price_info.split("$")[1].split()[0]
        price_usd = float(price_str)
        
        if price_usd <= 0:
            await callback_query.answer("Invalid price received. Please try again.", show_alert=True)
            return
            
        # Calculate crypto amounts for limits
        min_amount = DEPOSIT_LIMITS["min"] / price_usd
        max_amount = DEPOSIT_LIMITS["max"] / price_usd
        fee_amount = DEPOSIT_LIMITS["fee"] / price_usd
        
        await callback_query.edit_message_text(
            f"✔️ Currency choice: {currency}\n\n"
            "Read the following information before depositing:\n\n"
            f"➖ Min. Deposit: {min_amount:.8f} {currency} ~ ${DEPOSIT_LIMITS['min']}\n"
            f"➕ Max. Deposit: {max_amount:.8f} {currency} ~ ${DEPOSIT_LIMITS['max']} (per calendar month)\n"
            f"💲 Fee: {fee_amount:.8f} {currency} ~ ${DEPOSIT_LIMITS['fee']}\n\n"
            f"💱 Current Rate:\n"
            f"{fee_amount:.8f} {currency} (${DEPOSIT_LIMITS['fee']}) ~ 1000 BTS\n\n"
            "💡 Additional Information:\n"
            "• All deposits below or above the set limit will be ignored and not refunded.\n"
            "• All deposits are automatically credited within 1-2 hours of the bot. you will be notified as soon as your BTS are credited.\n"
            "• All your deposits are subject to a fee. Then from each of your deposits the fee is deducted.\n\n"
            f"✔️ Write below the amount in {currency} you want to deposit\n"
            "or digit /start to cancel this operation."
        )
    except (ValueError, ZeroDivisionError, IndexError) as e:
        print(f"Error processing price for {currency}: {e}")
        await callback_query.answer("Error processing price. Please try again.", show_alert=True)
        return

async def handle_deposit_input_logic(client: Client, message: Message, text: str):
    """Handle deposit amount input"""
    user_id = message.chat.id
    if user_id not in deposit_states or deposit_states[user_id]["step"] != "amount":
        return
    
    try:
        amount = float(text)
        currency = deposit_states[user_id]["currency"]
        
        # Get deposit info
        price_usd, fee_amount, _ = await get_deposit_info(currency, amount, user_id)
        if not all([price_usd, fee_amount]):
            await message.reply_text("Error processing deposit. Please try again.")
            return
        
        amount_usd = amount * price_usd
        
        print(f"Debug - Amount: {amount} {currency}")
        print(f"Debug - Price USD: ${price_usd}")
        print(f"Debug - Amount USD: ${amount_usd}")
        print(f"Debug - Min Limit: ${DEPOSIT_LIMITS['min']}")
        print(f"Debug - Max Limit: ${DEPOSIT_LIMITS['max']}")
        
        # Check limits
        if amount_usd < DEPOSIT_LIMITS["min"]:
            await message.reply_text(
                f"Amount too low. Minimum deposit is ${DEPOSIT_LIMITS['min']} (approximately {DEPOSIT_LIMITS['min']/price_usd:.8f} {currency})"
            )
            return
        elif amount_usd > DEPOSIT_LIMITS["max"]:
            await message.reply_text(
                f"Amount too high. Maximum deposit is ${DEPOSIT_LIMITS['max']} (approximately {DEPOSIT_LIMITS['max']/price_usd:.8f} {currency})"
            )
            return
        
        #GENERATE PAYMENT CODE
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        deposit_id = f"deposit_{user_id}_{currency}_{code}"
        
        try: 
            payment_data  = {
                "price_amount": amount,
                "price_currency": currency.lower(),
                "pay_currency": currency.lower(),
                "order_id": deposit_id,
                "ipn_callback_url": f"{BASE_URL}/nowpayments-callback",
                "order_description": f"Deposit for user {user_id} in {currency}",
            }

            # Make the API request
            headers = {
                "x-api-key": NOWPAYMENTS_API_KEY,
                "Content-Type": "application/json"
            }

            response = requests.post(
            NOWPAYMENTS_API_URL,
            headers=headers,
            json=payment_data
        )
            if response.status_code == 201:
                payment_info = response.json()

                # Store amount in state
                deposit_states[user_id].update({
                    "amount": amount,
                    "amount_usd": amount_usd,
                    "fee_amount": fee_amount,
                    "step": "confirm",
                    "deposit_id": deposit_id,
                    "payment_id": payment_info["payment_id"]
                })
                
                # Get deposit address
                address = payment_info["pay_address"]
                if not address:
                    await message.reply_text("Error: Invalid currency selected.")
                    return
                
                # Send deposit instructions
                await message.reply_text(
                    f"💳 You have chosen to deposit {amount} {currency}\n"
                    f"deposit exactly this amount!\n"
                    "Read the report before depositing.\n\n"
                    "• Report:\n"
                    f"💰 You will deposit: {amount} {currency} ( ${amount_usd:.2f} )\n"
                    f"💲 Fee: {fee_amount:.8f} {currency} ~ ${DEPOSIT_LIMITS['fee']}\n\n"
                    f"Deposit to this {currency} Address:\n"
                    f"`{address}`\n\n"
                    f"Deposit ID: `{deposit_id}`\n\n"
                    f"Payment ID: {payment_info['payment_id']}"
                    f"💱 Only after sending {currency} and COMPLETED the transaction click on \"Deposit completed\".",
                    reply_markup=DEPOSIT_CONFIRM_BUTTON
                )
            else:
                await message.reply(f"Payment failed: {response.text}")

        except Exception as e:
            await message.reply(f"Error: {str(e)}")
            
        
        # Delete the amount input message
        await message.delete()
        
    except ValueError:
        await message.reply_text("❌ Please enter a valid number")
        return
    except Exception as e:
        print(f"Error processing deposit: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")
        return

@Bot.on_callback_query(filters.regex("^deposit_complete$"))
async def handle_complete_deposit(client: Client, callback_query: CallbackQuery):
    """Handle deposit completion"""
    user_id = callback_query.from_user.id
    
    # Check if user has a valid deposit state
    if user_id not in deposit_states:
        await callback_query.answer("Please start a new deposit by selecting a currency first.", show_alert=True)
        await show_deposit_menu(client, callback_query)
        return
        
    if deposit_states[user_id]["step"] != "confirm":
        await callback_query.answer("Please complete the previous steps first.", show_alert=True)
        # Reset to amount step if they're stuck
        if "currency" in deposit_states[user_id]:
            deposit_states[user_id]["step"] = "amount"
            await handle_select_currency(client, callback_query)
        else:
            await show_deposit_menu(client, callback_query)
        return
    
    # Get deposit info from state
    deposit_info = deposit_states[user_id]
    currency = deposit_info["currency"]
    amount = deposit_info["amount"]
    amount_usd = deposit_info["amount_usd"]
    payment_id = deposit_info["payment_id"]
    deposit_id = deposit_info["deposit_id"]
    
    try:
        # Store as pending deposit
        await db.add_pending_deposit(
            user_id=user_id,
            amount=amount,
            currency=currency,
            amount_usd=amount_usd
        )
        
        # Clear deposit state
        del deposit_states[user_id]
        
        # Send confirmation to user
        await callback_query.edit_message_text(
            f"✅ Deposit marked as pending!\n\n"
            f"Your deposit of {amount} {currency} (${amount_usd:.2f}) has been recorded.\n"
            f"Your account will be funded within 3-4 hours after admin verification.\n"
            f"You will be notified once the deposit is approved."
        )
        
        # Create approve button for admin
        approve_button = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"✅ Approve Deposit (${amount_usd:.2f})",
                callback_data=f"approve_deposit_{user_id}_{amount}"
            )]
        ])
        
        # Notify all admins
        for admin_id in ADMINS:
            try:
                await client.send_message(
                    admin_id,
                    f"🛎️ New Deposit Request\n\n"
                    f"User: @{callback_query.from_user.username or callback_query.from_user.first_name}\n"
                    f"Deposit ID: {deposit_id}\n"
                    f"payment ID: {payment_id}\n"
                    f"Amount: {amount} {currency} (${amount_usd:.2f})\n\n"
                    f"Click the button below to approve:",
                    reply_markup=approve_button
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
                
    except Exception as e:
        print(f"Error completing deposit: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)
        # Reset to deposit menu
        await show_deposit_menu(client, callback_query)

@Bot.on_callback_query(filters.regex("^approve_deposit_"))
async def handle_approve_deposit_callback(client: Client, callback_query: CallbackQuery):
    """Handle deposit approval from callback"""
    print("Received deposit approval callback")
    
    # Check if user is admin
    if callback_query.from_user.id not in ADMINS:
        print(f"Non-admin user {callback_query.from_user.id} attempted to approve deposit")
        await callback_query.answer("❌ You are not authorized to approve deposits.", show_alert=True)
        return
    
    try:
        # Parse callback data
        print(f"Callback data: {callback_query.data}")
        # Remove 'approve_deposit_' prefix and split the rest
        data = callback_query.data.replace('approve_deposit_', '')
        user_id, amount = data.split('_', 1)
        user_id = int(user_id)
        print(f"Processing approval for user {user_id}, amount {amount}")
        
        # Get user info
        user = await db.get_user(user_id)
        if not user:
            print(f"User {user_id} not found")
            await callback_query.answer("❌ User not found.", show_alert=True)
            return
        
        print("Getting and approving pending deposit...")
        # Get and approve pending deposit
        deposit = await db.approve_deposit(user_id)
        if not deposit:
            print(f"No pending deposit found for user {user_id}")
            await callback_query.answer("❌ No pending deposit found.", show_alert=True)
            return
        
        print("Getting updated user info...")
        # Get updated user info
        user = await db.get_user(user_id)
        new_deposited = user.get("deposited_balance", 0)
        print(f"New deposited balance: {new_deposited}")
        
        # Send confirmation to admin first
        await callback_query.answer("✅ Deposit approved successfully!", show_alert=True)
        
        # Notify user
        try:
            print(f"Sending notification to user {user_id}")
            await client.send_message(
                user_id,
                f"✅ Your deposit has been approved!\n\n"
                f"Amount: ${deposit['amount_usd']:.2f}\n"
                f"💰 New deposited balance: ${new_deposited:.2f}"
            )
            # Send message to channel after successful user notification
            try:
                # Get user details for the channel message
                user_info = await client.get_users(user_id)
                username = user_info.username or "No username"
                first_name = user_info.first_name or "No name"
                
                # Format the channel message
                channel_message = (
                    f"📥 New Deposit 📥\n\n"
                    f"🔸Name: {first_name}\n"
                    f"🔸Username: @{username}\n"
                    f"🔸ID: {user_id}\n"
                    f"💸 Amount: {deposit['amount']} {deposit['currency']} (${deposit['amount_usd']:.2f})\n\n"
                    f"Deposit has been approved! ❤️\n\n"
                    f"🤖 Bot: BTS Trading ({BOT_LINK})"
                )
                
                # Send to channel
                await client.send_message(
                    "BTS_bot_payment",
                    channel_message
                )
                print("Successfully sent deposit notification to channel")
                
            except Exception as e:
                print(f"Failed to send channel message: {e}")
            
            print("Deleting approval message...")
            # If user notification was successful, delete the approval message
            await callback_query.message.delete()
            print("Approval process completed successfully")
            
        except Exception as e:
            print(f"Failed to notify user {user_id}: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # If user notification fails, update the message to show error
            await callback_query.edit_message_text(
                f"⚠️ Deposit approved but user notification failed!\n\n"
                f"User: {user_id}\n"
                f"Amount: {deposit['amount']} {deposit['currency']} (${deposit['amount_usd']:.2f})\n"
                f"New deposited balance: ${new_deposited:.2f}\n\n"
                f"Error: {str(e)}\n"
                f"Please notify the user manually."
            )
            
    except Exception as e:
        print(f"Error in approve_deposit_callback: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        await callback_query.answer("❌ An error occurred", show_alert=True)
        # Keep the message and button if there was an error

@Bot.on_callback_query(filters.regex("^deposit_cancel$"))
async def handle_cancel_deposit(client: Client, callback_query: CallbackQuery):
    """Cancel deposit process"""
    user_id = callback_query.from_user.id
    if user_id in deposit_states:
        del deposit_states[user_id]
    
    await callback_query.edit_message_text("❌ Deposit cancelled.")

@Bot.on_message(filters.private & filters.command(["approve_deposit"]))
async def handle_approve_deposit_command(client: Client, message: Message):
    """Handle deposit approval command"""
    # Check if user is admin
    if message.chat.id not in ADMINS:
        await message.reply_text("❌ You are not authorized to use this command.")
        return
    
    # Parse command arguments
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text("❌ Invalid command format. Use: /approve_deposit <user_id>")
            return
        
        user_id = int(args[1])
        
        # Get user info
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text(f"❌ User {user_id} not found.")
            return
        
        # Get and approve pending deposit
        deposit = await db.approve_deposit(user_id)
        if not deposit:
            await message.reply_text(f"❌ No pending deposit found for user {user_id}.")
            return
        
        # Get updated user info
        user = await db.get_user(user_id)
        new_balance = user.get("balance", 0)
        
        # Send confirmation to admin
        await message.reply_text(
            f"✅ Deposit approved!\n\n"
            f"User: {user_id}\n"
            f"Amount: {deposit['amount']} {deposit['currency']}\n"
            f"Tokens added: {deposit['handyearn_amount']} 🏵 + {deposit['bonus']} 🏵\n"
            f"New balance: {new_balance} 🏵"
        )
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                f"✅ Your deposit has been approved!\n\n"
                f"You have received:\n"
                f"• {deposit['handyearn_amount']} 🏵 (Deposit)\n"
                f"• {deposit['bonus']} 🏵 (Bonus)\n"
                f"💰 New balance: {new_balance} 🏵"
            )
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")
            await message.reply_text(f"⚠️ User notification failed: {e}")
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a valid number.")
    except Exception as e:
        print(f"Error approving deposit: {e}")
        await message.reply_text(f"❌ An error occurred: {e}") 