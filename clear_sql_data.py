#!/usr/bin/env python3
"""
Quick SQL Database Clear Script
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import text
from app.core.database import database

async def clear_database():
    """Clear all data from PostgreSQL database"""
    print("🗃️ Initializing database connection...")
    
    # Initialize database
    await database.initialize()
    
    print("🧹 Clearing PostgreSQL database...")
    
    async with database.get_session() as session:
        try:
            total_deleted = 0
            
            # First, check what tables exist
            result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Found tables: {', '.join(tables)}")
            
            # Delete from tables that exist
            tables_to_clear = ['entries', 'sessions', 'messages', 'topics']
            
            for table in tables_to_clear:
                if table in tables:
                    try:
                        result = await session.execute(text(f'DELETE FROM {table}'))
                        await session.commit()
                        rows_deleted = result.rowcount
                        total_deleted += rows_deleted
                        print(f'✅ Deleted from {table}: {rows_deleted} rows')
                    except Exception as e:
                        print(f'⚠️ Error deleting from {table}: {e}')
                        await session.rollback()
                else:
                    print(f'⚠️ Table {table} does not exist, skipping')
            
            print("\n📊 Verification - Remaining counts:")
            
            # Check remaining counts for existing tables
            for table in tables_to_clear:
                if table in tables:
                    try:
                        result = await session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                        count = result.scalar()
                        print(f'   {table.capitalize()}: {count}')
                    except Exception as e:
                        print(f'   {table.capitalize()}: Error checking count ({e})')
            
            print(f"\n🎯 Database cleanup complete!")
            print(f"   Total deleted: {total_deleted} rows")
            
        except Exception as e:
            await session.rollback()
            print(f'❌ Error during database clearing: {e}')
            raise
        finally:
            await database.close()

if __name__ == "__main__":
    print("🤖 Quick SQL Database Clear")
    print("=" * 40)
    asyncio.run(clear_database())
