#!/usr/bin/env python3
"""
Simple script to check and manage users in the database
"""
import asyncio
import sys
from app.core.database import get_db
from app.auth.models import AuthUser
from passlib.context import CryptContext
from sqlalchemy import text

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

async def main():
    # Initialize database first
    from app.core.database import database
    await database.initialize()
    
    # Get database session
    async for db in get_db():
        try:
            # Get all users
            result = await db.execute(text("SELECT id, username, email, role, is_active, password_hash FROM auth_users"))
            users = result.fetchall()
            
            print('Current users in database:')
            for user in users:
                print(f'  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[3]}, Active: {user[4]}')
            
            # Set passwords for both users
            # Test user password
            result = await db.execute(text("SELECT id, username, password_hash FROM auth_users WHERE username = 'testuser'"))
            test_user = result.fetchone()
            
            if test_user:
                user_id, username, current_hash = test_user
                new_hash = pwd_context.hash('password123')
                await db.execute(
                    text("UPDATE auth_users SET password_hash = :hash WHERE id = :id"),
                    {"hash": new_hash, "id": user_id}
                )
                print(f'✅ Test user "{username}" password set to: password123')
            
            # Default admin user password
            result = await db.execute(text("SELECT id, username, password_hash FROM auth_users WHERE username = 'default_user'"))
            admin_user = result.fetchone()
            
            if admin_user:
                user_id, username, current_hash = admin_user
                new_hash = pwd_context.hash('admin123')
                await db.execute(
                    text("UPDATE auth_users SET password_hash = :hash WHERE id = :id"),
                    {"hash": new_hash, "id": user_id}
                )
                print(f'✅ Admin user "{username}" password set to: admin123')
            
            await db.commit()
            
            break  # Exit the async generator loop
            
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    asyncio.run(main())