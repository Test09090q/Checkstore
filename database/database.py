#(©)CodeXBotz
#recoded by @Its_Oreki_Hotarou

import os
from config import DB_URI, DB_NAME
import motor.motor_asyncio
from pytz import timezone
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Union

# Create async MongoDB client
dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

# Database collections
user_data = database['users']
premium_users = database['premium']
collection = premium_users  # Alias for backward compatibility

class DatabaseManager:
    @staticmethod
    async def present_user(user_id: int) -> bool:
        """Check if user exists in database"""
        return await user_data.find_one({'_id': user_id}) is not None

    @staticmethod
    async def add_user(user_id: int) -> None:
        """Add new user to database"""
        if not await DatabaseManager.present_user(user_id):
            await user_data.insert_one({'_id': user_id})

    @staticmethod
    async def full_userbase() -> List[int]:
        """Get list of all user IDs"""
        return [doc['_id'] async for doc in user_data.find({})]

    @staticmethod
    async def del_user(user_id: int) -> None:
        """Remove user from database"""
        await user_data.delete_one({'_id': user_id})

    @staticmethod
    async def is_premium_user(user_id: int) -> bool:
        """Check if user has active premium status"""
        user = await premium_users.find_one({"user_id": user_id})
        if not user:
            return False
            
        expiration_time = datetime.fromisoformat(user["expiration_timestamp"])
        return datetime.now(timezone("Asia/Kolkata")) < expiration_time

    @staticmethod
    async def remove_premium(user_id: int) -> None:
        """Remove premium status from user"""
        await premium_users.delete_one({"user_id": user_id})

    @staticmethod
    async def remove_expired_users() -> int:
        """Remove all expired premium users and return count"""
        current_time = datetime.now(timezone("Asia/Kolkata")).isoformat()
        result = await premium_users.delete_many(
            {"expiration_timestamp": {"$lte": current_time}}
        )
        return result.deleted_count

    @staticmethod
    async def list_premium_users() -> List[Dict[str, Union[int, str]]:
        """Get detailed list of active premium users"""
        ist = timezone("Asia/Kolkata")
        now = datetime.now(ist)
        active_users = []
        
        async for user in premium_users.find({}):
            expiration_time = datetime.fromisoformat(
                user["expiration_timestamp"]
            ).astimezone(ist)
            
            if expiration_time > now:
                remaining = expiration_time - now
                days, remainder = divmod(remaining.seconds, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                active_users.append({
                    "user_id": user["user_id"],
                    "expiry_time": expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST'),
                    "remaining": f"{days}d {hours}h {minutes}m {seconds}s"
                })
        
        return active_users

    @staticmethod
    async def add_premium(
        user_id: int, 
        time_value: int, 
        time_unit: str
    ) -> str:
        """Add premium access with expiration time"""
        ist = timezone("Asia/Kolkata")
        now = datetime.now(ist)
        
        if time_unit == 'm':
            delta = timedelta(minutes=time_value)
        elif time_unit == 'd':
            delta = timedelta(days=time_value)
        else:
            raise ValueError("Invalid time unit. Use 'm' for minutes or 'd' for days.")
        
        expiration_time = now + delta
        expiry_str = expiration_time.isoformat()
        
        await premium_users.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "expiration_timestamp": expiry_str,
                "added_on": now.isoformat(),
                "duration": f"{time_value}{time_unit}"
            }},
            upsert=True
        )
        
        return expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST')

    @staticmethod
    async def check_user_plan(user_id: int) -> str:
        """Check user's premium status and remaining time"""
        user = await premium_users.find_one({"user_id": user_id})
        if not user:
            return "You don't have an active premium plan."
            
        ist = timezone("Asia/Kolkata")
        expiration_time = datetime.fromisoformat(
            user["expiration_timestamp"]
        ).astimezone(ist)
        now = datetime.now(ist)
        
        if now >= expiration_time:
            await DatabaseManager.remove_premium(user_id)
            return "Your premium plan has expired."
        
        remaining = expiration_time - now
        days, remainder = divmod(remaining.seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return (
            f"🌟 Premium Status: Active\n"
            f"⏳ Remaining: {days}d {hours}h {minutes}m {seconds}s\n"
            f"📅 Expires on: {expiration_time.strftime('%d %b %Y at %I:%M %p IST')}\n"
            f"⌛ Duration: {user.get('duration', 'N/A')}"
        )
