from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
from bot import Bot
from database.database import DatabaseManager
from config import OWNER_ID
from datetime import datetime
from pytz import timezone

@Bot.on_message(filters.command('addpaid') & filters.user(OWNER_ID))
async def add_premium_user_command(client: Client, msg: Message):
    if len(msg.command) != 4:
        await msg.reply_text("Usage: /addpaid <user_id> <time_value> <time_unit (m/d)>")
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()

        # Call add_premium function from DatabaseManager
        expiration_time = await DatabaseManager.add_premium(user_id, time_value, time_unit)

        # Notify admin
        await msg.reply_text(
            f"✅ User {user_id} added as premium for {time_value}{time_unit}\n"
            f"⏳ Expires: {expiration_time}"
        )

        # Notify user
        try:
            await client.send_message(
                chat_id=user_id,
                text=(
                    "🎉 <b>Premium Activated!</b>\n\n"
                    f"⏳ <b>Duration:</b> {time_value}{time_unit}\n"
                    f"📅 <b>Expires:</b> {expiration_time}\n\n"
                    "Thank you for subscribing!"
                )
            )
        except Exception as e:
            await msg.reply_text(f"User notification failed: {e}")

    except ValueError as ve:
        await msg.reply_text(f"Invalid input: {ve}")
    except Exception as e:
        await msg.reply_text(f"Error: {str(e)}")

@Bot.on_message(filters.command('removepaid') & filters.user(OWNER_ID))
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("Usage: /removepaid <user_id>")
        return
    
    try:
        user_id = int(msg.command[1])
        await DatabaseManager.remove_premium(user_id)
        await msg.reply_text(f"❌ User {user_id} removed from premium")
        
        # Notify user if possible
        try:
            await client.send_message(
                chat_id=user_id,
                text="⚠️ Your premium access has been removed by admin"
            )
        except:
            pass
            
    except ValueError:
        await msg.reply_text("Invalid user ID")
    except Exception as e:
        await msg.reply_text(f"Error: {str(e)}")

@Bot.on_message(filters.command('listpaid') & filters.user(OWNER_ID))
async def list_premium_users_command(client: Client, message: Message):
    try:
        premium_users = await DatabaseManager.list_premium_users()
        
        if not premium_users:
            await message.reply_text("No active premium users found")
            return
            
        response = ["<b>Active Premium Users:</b>\n"]
        
        for user in premium_users:
            try:
                user_info = await client.get_users(user["user_id"])
                username = f"@{user_info.username}" if user_info.username else "No Username"
                response.append(
                    f"\n👤 <b>User:</b> {username}\n"
                    f"🆔 <b>ID:</b> <code>{user['user_id']}</code>\n"
                    f"⏳ <b>Remaining:</b> {user['remaining']}\n"
                    f"📅 <b>Expires:</b> {user['expiry_time']}\n"
                    "━━━━━━━━━━━━━━"
                )
            except Exception as e:
                response.append(
                    f"\n⚠️ <b>User ID:</b> <code>{user['user_id']}</code>\n"
                    f"❌ <b>Error:</b> {str(e)}\n"
                    "━━━━━━━━━━━━━━"
                )
        
        # Split long messages to avoid Telegram limits
        for i in range(0, len(response), 10):
            await message.reply_text(
                "".join(response[i:i+10]),
                disable_web_page_preview=True
            )
            
    except Exception as e:
        await message.reply_text(f"Error fetching premium users: {str(e)}")

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        status = await DatabaseManager.check_user_plan(user_id)
        
        await message.reply_text(
            f"<b>Your Premium Status:</b>\n\n{status}",
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.reply_text(f"Error checking your plan: {str(e)}")
