from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from .database import db
from .vars import ADMINS, BOT_LINK
from .client import Bot
from .admin import add_user
from .constants import ROBOT_PRICES, ROBOT_RATES
from datetime import datetime
from .clear_states import clear_stale_states, upgrade_states_object

upgrade_states = {}

# Upgrade buttons
UPGRADE_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("💳 Upgrade", callback_data="upgrade")],
    [InlineKeyboardButton("❌ Cancel", callback_data="upgrade_cancel")]
])

CONFIRM_UPGRADE_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ Confirm Upgrade", callback_data="confirm_upgrade")],
    [InlineKeyboardButton("❌ Cancel", callback_data="upgrade_cancel")]
])

@Bot.on_message(filters.private & filters.command(["upgrade"]))
async def handle_upgrade_command(client: Client, message: Message):
    """Handle /upgrade command"""
    await clear_stale_states()
    print("[DEBUG] Upgrade command received from user:", message.chat.id)
    user_id = message.chat.id
    upgrade_states_object["user_id"] = user_id
    upgrade_states_object["state"] = "select_robot"
    # Ensure user exists
    await add_user(user_id)
    
    # Get current robot level and counts
    current_level = await db.get_robot_level(user_id)
    robot_counts = await db.get_robot_counts(user_id)
    total_mining_rate = await db.calculate_mining_rate(user_id)
    print(f"[DEBUG] Current level: {current_level}, Robot counts: {robot_counts}, Total mining rate: {total_mining_rate}")
    
    # Store state for upgrade input with select_robot step
    upgrade_states[user_id] = {
        "step": "select_robot",
        "message_id": message.id,
        "timestamp": datetime.now(),
        "current_level": current_level,
        "robot_counts": robot_counts
    }
    print(f"[DEBUG] Created upgrade state for user {user_id}: {upgrade_states[user_id]}")
    print(f"[DEBUG] All upgrade states: {upgrade_states}")
    
    # Build upgrade options message
    message_text = f"🤖 Current Robot Level: {current_level}\n"
    message_text += f"💰 Total Mining Rate: {total_mining_rate} BTS/hour\n\n"
    message_text += "Your Robots:\n"
    for level, count in robot_counts.items():
        if count > 0:
            message_text += f"• Robot {level}: {count}x ({ROBOT_RATES[int(level)]} BTS/hour each)\n"
    
    message_text += "\nAvailable Upgrades:\n"
    for level, price in ROBOT_PRICES.items():
        if level >= current_level:  # Allow buying same level or higher
            message_text += f"• Robot {level}: ${price} ({ROBOT_RATES[level]} BTS/hour)\n"
    
    message_text += "\n1000 BTS = $1\n"
    message_text += "Upgrade your mining robots to increase your mining rate!\n"
    message_text += "\nTo upgrade, enter the number of the robot you want to purchase (1-7)"
    
    await message.reply_text(message_text)

async def handle_upgrade_input_logic(client: Client, message: Message, text:str):
    """Handle upgrade robot selection"""
    user_id = message.chat.id
    print(f"[DEBUG] Processing upgrade input for user {user_id}: {text}")
    print(f"[DEBUG] Current upgrade states: {upgrade_states}")
    
    if user_id not in upgrade_states:
        print(f"[DEBUG] No upgrade state found for user {user_id}, creating new state")
        # Create new state if missing
        current_level = await db.get_robot_level(user_id)
        robot_counts = await db.get_robot_counts(user_id)
        upgrade_states[user_id] = {
            "step": "select_robot",
            "message_id": message.id,
            "timestamp": datetime.now(),
            "current_level": current_level,
            "robot_counts": robot_counts
        }
        print(f"[DEBUG] Created new upgrade state: {upgrade_states[user_id]}")
        
    state = upgrade_states[user_id]
    print(f"[DEBUG] Current upgrade state: {state}")
    
    if state["step"] != "select_robot":
        print(f"[DEBUG] Invalid step in upgrade state: {state['step']}")
        await message.reply_text("❌ Please use /upgrade to start the upgrade process.")
        return
    
    try:
        # Parse selected robot level
        target_level = int(text.strip())
        print(f"[DEBUG] Parsed target level: {target_level}")
        
        # Validate robot level (1-7)
        if target_level < 1 or target_level > 7:
            print(f"[DEBUG] Invalid robot level: {target_level}")
            await message.reply_text(
                "❌ Invalid robot level. Please enter a number between 1 and 7."
            )
            return
        
        # Get current level from state
        current_level = state["current_level"]
        print(f"[DEBUG] Current robot level: {current_level}")
        
        # Allow buying same level or higher (no downgrading)
        if target_level < current_level:
            print(f"[DEBUG] Target level {target_level} is lower than current level {current_level}")
            await message.reply_text(
                f"❌ You cannot downgrade to a lower level robot. Your current level is {current_level}."
            )
            return
        
        # Calculate upgrade cost
        upgrade_cost = ROBOT_PRICES[target_level]
        print(f"[DEBUG] Upgrade cost: ${upgrade_cost}")
        
        # Calculate new mining rate after upgrade
        current_robot_counts = state["robot_counts"].copy()
        if str(target_level) not in current_robot_counts:
            current_robot_counts[str(target_level)] = 0
        current_robot_counts[str(target_level)] += 1
        
        new_total_rate = 0
        for level, count in current_robot_counts.items():
            if count > 0:
                new_total_rate += ROBOT_RATES[int(level)] * count
        
        # Store upgrade details
        upgrade_states[user_id].update({
            "target_level": target_level,
            "cost": upgrade_cost,
            "new_total_rate": new_total_rate,
            "step": "confirm"
        })
        print(f"[DEBUG] Updated upgrade state: {upgrade_states[user_id]}")
        
        # Show confirmation message
        await message.reply_text(
            f"🤖 Upgrade Confirmation\n\n"
            f"Current Level: {current_level}\n"
            f"Target Level: {target_level}\n"
            f"Cost: ${upgrade_cost}\n"
            f"New Robot Mining Rate: {ROBOT_RATES[target_level]} BTS/hour\n"
            f"New Total Mining Rate: {new_total_rate} BTS/hour\n\n"
            f"Click the button below to proceed with payment:",
            reply_markup=CONFIRM_UPGRADE_BUTTON
        )
        
    except ValueError:
        print(f"[DEBUG] Invalid number format: {text}")
        await message.reply_text(
            "❌ Please enter a valid number for the robot level."
        )
    except Exception as e:
        print(f"[DEBUG] Error processing upgrade selection: {str(e)}")
        await message.reply_text(
            "❌ An error occurred. Please try again later."
        )



@Bot.on_callback_query(filters.regex("^confirm_upgrade$"))
async def handle_confirm_upgrade(client: Client, callback_query: CallbackQuery):
    """Handle upgrade confirmation"""
    user_id = callback_query.from_user.id
    if user_id not in upgrade_states or upgrade_states[user_id]["step"] != "confirm":
        await callback_query.answer("Invalid upgrade state", show_alert=True)
        return
    try:
        # Get upgrade details
        state = upgrade_states[user_id]
        target_level = state["target_level"]
        cost = state["cost"]
        current_level = await db.get_robot_level(user_id)
        # Check deposited balance
        user = await db.get_user(user_id)
        deposited_balance = user.get("deposited_balance", 0)
        if deposited_balance < cost:
            await callback_query.answer(
                f"❌ Not enough deposited funds to upgrade. You need ${cost}, but you have only ${deposited_balance:.2f} deposited. Please deposit more to upgrade.",
                show_alert=True
            )
            return
        # Deduct the upgrade cost from deposited_balance
        new_deposited_balance = deposited_balance - cost
        await db.col.update_one(
            {"id": int(user_id)},
            {"$set": {"deposited_balance": new_deposited_balance}}
        )
        if user_id in db.cache:
            del db.cache[user_id]
        # Store as pending upgrade
        await db.add_pending_upgrade(user_id, current_level, target_level, cost)
        # Clear upgrade state
        del upgrade_states[user_id]
        # Create approve button for admin
        approve_button = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"✅ Approve Upgrade to Robot {target_level}",
                callback_data=f"approve_upgrade_{user_id}_{target_level}"
            )]
        ])
        # Notify user
        await callback_query.edit_message_text(
            f"✅ Upgrade request submitted!\n\n"
            f"Current Level: {current_level}\n"
            f"Target Level: {target_level}\n"
            f"Cost: ${cost}\n"
            f"New Total Mining Rate: {state.get('new_total_rate', 'N/A')} BTS/hour\n\n"
            f"Your upgrade is being processed. You will be notified once it's approved."
        )
        # Notify admins
        for admin_id in ADMINS:
            try:
                await client.send_message(
                    admin_id,
                    f"🛎️ New Upgrade Request\n\n"
                    f"User: @{callback_query.from_user.username or callback_query.from_user.first_name}\n"
                    f"Current Level: {current_level}\n"
                    f"Target Level: {target_level}\n"
                    f"Cost: ${cost}\n\n"
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
                f"📈 New Upgrade Request\n\n"
                f"🔸Name: {first_name}\n"
                f"🔸Username: @{username}\n"
                f"🔸ID: {user_id}\n"
                f"💸 Amount: ${cost}\n"
                f"🤖 Current Level: {current_level}\n"
                f"🤖 Target Level: {target_level}\n\n"
                f"Upgrade is being processed...\n\n"
                f"🤖 Bot: BTS Trading ({BOT_LINK}) ™"
            )
        except Exception as e:
            print(f"Failed to send channel message: {e}")
    except Exception as e:
        print(f"Error in confirm_upgrade: {e}")
        await callback_query.answer("An error occurred. Please try again.", show_alert=True)

@Bot.on_callback_query(filters.regex("^approve_upgrade_"))
async def handle_approve_upgrade_callback(client: Client, callback_query: CallbackQuery):
    """Handle upgrade approval from callback"""
    # Check if user is admin
    if callback_query.from_user.id not in ADMINS:
        await callback_query.answer("❌ You are not authorized to approve upgrades.", show_alert=True)
        return
    
    try:
        # Parse callback data
        data = callback_query.data.replace('approve_upgrade_', '')
        user_id, target_level = data.split('_', 1)
        user_id = int(user_id)
        target_level = int(target_level)
        
        # Get and approve pending upgrade
        upgrade = await db.approve_upgrade(user_id)
        if not upgrade:
            await callback_query.answer("❌ No pending upgrade found.", show_alert=True)
            return
        
        # Get updated user info
        user = await db.get_user(user_id)
        robot_counts = user.get("robot_counts", {"0": 1})
        
        # Send confirmation to admin
        await callback_query.answer("✅ Upgrade approved successfully!", show_alert=True)
        
        # Notify user
        try:
            # Calculate new total mining rate
            new_total_rate = await db.calculate_mining_rate(user_id)
            
            await client.send_message(
                user_id,
                f"✅ Your upgrade has been approved!\n\n"
                f"🤖 New Robot Level: {target_level}\n"
                f"💰 New Total Mining Rate: {new_total_rate} BTS/hour\n\n"
                f"Your robots:\n" + 
                "\n".join([f"• Robot {level}: {count}x ({ROBOT_RATES[int(level)]} BTS/hour each)" for level, count in robot_counts.items() if count > 0])
            )
            
            # Send message to channel
            try:
                # Get user details for the channel message
                user_info = await client.get_users(user_id)
                username = user_info.username or "No username"
                first_name = user_info.first_name or "No name"
                
                await client.send_message(
                    "BTS_bot_payment",
                    f"✅ Upgrade Completed ✅\n\n"
                    f"🔸Name: {first_name}\n"
                    f"🔸Username: @{username}\n"
                    f"🔸ID: {user_id}\n"
                    f"🤖 New Robot Level: {target_level}\n"
                    f"💰 New Mining Rate: {ROBOT_RATES[target_level]} BTS/hour\n\n"
                    f"Upgrade has been processed successfully!\n\n"
                    f"🤖 Bot: BTS Trading ({BOT_LINK}) ™"
                )
            except Exception as e:
                print(f"Failed to send channel message: {e}")
            
            # Delete the approval message
            await callback_query.message.delete()
            
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")
            await callback_query.edit_message_text(
                f"⚠️ Upgrade approved but user notification failed!\n\n"
                f"User: {user_id}\n"
                f"New Level: {target_level}\n\n"
                f"Error: {str(e)}\n"
                f"Please notify the user manually."
            )
            
    except Exception as e:
        print(f"Error in approve_upgrade_callback: {e}")
        await callback_query.answer("❌ An error occurred", show_alert=True)

@Bot.on_callback_query(filters.regex("^upgrade_cancel$"))
async def handle_cancel_upgrade(client: Client, callback_query: CallbackQuery):
    """Cancel upgrade process"""
    user_id = callback_query.from_user.id
    if user_id in upgrade_states:
        del upgrade_states[user_id]
    
    await callback_query.edit_message_text("❌ Upgrade cancelled.")