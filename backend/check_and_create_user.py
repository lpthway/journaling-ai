#!/usr/bin/env python3
"""
Script to check if default user exists and create if needed
"""
import asyncio
import sys
from app.core.database import database
from sqlalchemy import text
import uuid

DEFAULT_USER_ID = "11111111-1111-1111-1111-111111111111"
DEFAULT_EMAIL = "default@journaling.ai"

async def check_and_create_user():
    """Check if default user exists, create if not"""
    try:
        # Initialize database
        await database.initialize()
        
        async with database.get_session() as session:
            # Check if default user exists
            result = await session.execute(
                text("SELECT id, email, is_active FROM users WHERE id = :user_id"),
                {"user_id": DEFAULT_USER_ID}
            )
            user = result.fetchone()
            
            if user:
                print(f"✅ Default user exists: ID={user[0]}, Email={user[1]}, Active={user[2]}")
                return True
            
            print(f"❌ Default user {DEFAULT_USER_ID} not found. Creating...")
            
            # Create default user
            await session.execute(
                text("""
                    INSERT INTO users (id, username, email, display_name, timezone, language, preferences, psychology_profile, is_active, created_at, updated_at)
                    VALUES (:id, :username, :email, :display_name, :timezone, :language, :preferences, :psychology_profile, true, now(), now())
                """),
                {
                    "id": DEFAULT_USER_ID,
                    "username": "default_user",
                    "email": DEFAULT_EMAIL,
                    "display_name": "Default User",
                    "timezone": "UTC",
                    "language": "en",
                    "preferences": "{}",
                    "psychology_profile": "{}"
                }
            )
            await session.commit()
            print(f"✅ Created default user: {DEFAULT_USER_ID}")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(check_and_create_user())
    sys.exit(0 if success else 1)
