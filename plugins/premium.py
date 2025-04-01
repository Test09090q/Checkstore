from pyrogram import Client, filters
from pyrogram.types import Message
import time
import asyncio
from bot import Bot
from database.database import *
from config import OWNER_ID
from datetime import datetime, timedelta
from pytz import timezone

@Bot.on_message(filters.command('addpaid') & filters.user(OWNER_ID))
async def add_premium_user_command(client, msg):
    if len(msg.command) != 4:
        await msg.reply_text("Usage: /addpaid <user_id> <time_value> <time_unit (m/d)>")
        return

    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()  # 'm' or 'd'

        # Call add_premium function
        expiration_time = await add_premium(user_id, time_value, time_unit)

        # Notify the admin about the premium activation
        await msg.reply_text(
            f"User {user_id} added as a premium user for {time_value} {time_unit}.\n"
            f"Expiration Time: {expiration_time}"
        )

        # Notify the user about their premium status
        await client.send_message(
            chat_id=user_id,
            text=(
                f"🎉 Congratulations! You have been upgraded to premium for {time_value} {time_unit}.\n\n"
                f"Expiration Time: {expiration_time}"
            ),
        )

        # Schedule expiry check
        asyncio.create_task(schedule_expiry_check(client, user_id, expiration_time))

    except ValueError:
        await msg.reply_text("Invalid input. Please check the user_id, time_value, and time_unit.")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {str(e)}")

async def schedule_expiry_check(client, user_id, expiration_time_str):
    """Schedule a task to check and handle user expiry"""
    ist = timezone("Asia/Kolkata")
    expiration_time = datetime.fromisoformat(expiration_time_str).astimezone(ist)
    current_time = datetime.now(ist)
    
    # Calculate seconds until expiry
    seconds_until_expiry = (expiration_time - current_time).total_seconds()
    
    if seconds_until_expiry > 0:
        # Wait until expiry time
        await asyncio.sleep(seconds_until_expiry)
        
        # Check if user is still in database (might have been manually removed)
        user_data = await collection.find_one({"user_id": user_id})
        if user_data:
            # Remove the user from premium
            await remove_premium(user_id)
            
            # Notify user about expiry
            try:
                await client.send_message(
                    chat_id=user_id,
                    text="⚠️ Your premium subscription has expired. Thank you for using our service!"
                )
            except Exception as e:
                print(f"Could not notify user {user_id} about expiry: {e}")

@Bot.on_message(filters.command('removepaid') & filters.user(OWNER_ID))
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("usage: /removepaid user_id")
        return
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"User {user_id} has been removed from premium.")
    except ValueError:
        await msg.reply_text("user_id must be an integer or not available in database.")

@Bot.on_message(filters.command('listpaid') & filters.user(OWNER_ID))
async def list_premium_users_command(client, message):
    # Define IST timezone
    ist = timezone("Asia/Kolkata")

    # Retrieve all users from the collection
    premium_users_cursor = collection.find({})
    premium_user_list = ['Active Premium Users in database:']
    current_time = datetime.now(ist)  # Get current time in IST

    # Use async for to iterate over the async cursor
    async for user in premium_users_cursor:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]

        try:
            # Convert expiration_timestamp to a timezone-aware datetime object in IST
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)

            # Calculate remaining time
            remaining_time = expiration_time - current_time

            if remaining_time.total_seconds() <= 0:
                # Remove expired users from the database
                await remove_premium(user_id)
                continue  # Skip to the next user if this one is expired

            # If not expired, retrieve user info
            user_info = await client.get_users(user_id)
            username = user_info.username if user_info.username else "No Username"
            first_name = user_info.first_name

            # Calculate days, hours, minutes, seconds left
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"

            # Add user details to the list
            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"User: @{username}\n"
                f"Name: <code>{first_name}</code>\n"
                f"Expiry: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"UserID: <code>{user_id}</code>\n"
                f"Error: Unable to fetch user details ({str(e)})"
            )

    if len(premium_user_list) == 1:  # No active users found
        await message.reply_text("I found 0 active premium users in my DB")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client, message):
    user_id = message.from_user.id  # Get user ID from the message

    # Get the premium status of the user
    status_message = await check_user_plan(user_id)

    # Send the response message to the user
    await message.reply(status_message)

async def check_expired_users(client):
    """Periodic task to check and remove expired users"""
    while True:
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        # Find all users in database
        cursor = collection.find({})
        
        async for user in cursor:
            user_id = user["user_id"]
            expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
            
            if current_time >= expiration_time:
                # User has expired
                await remove_premium(user_id)
                
                # Notify user
                try:
                    await client.send_message(
                        chat_id=user_id,
                        text="⚠️ Your premium subscription has expired. Thank you for using our service!"
                    )
                except Exception as e:
                    print(f"Could not notify user {user_id} about expiry: {e}")
        
        # Check every hour
        await asyncio.sleep(3600)
