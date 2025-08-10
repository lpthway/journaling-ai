#!/usr/bin/env python3
"""
Direct PostgreSQL Database Cleanup Script for Journaling AI

This script connects directly to PostgreSQL to clean all user data.
"""

import asyncio
import asyncpg
import sys
import os
from typing import List, Tuple

class PostgreSQLCleaner:
    def __init__(self):
        # Get database connection info from environment or use defaults
        self.db_url = os.getenv(
            "DB_URL", 
            "postgresql://postgres:password@localhost:5432/journaling_ai"
        ).replace("postgresql+asyncpg://", "postgresql://")
        
        self.test_user_id = "00000000-0000-0000-0000-000000000001"
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            print("✅ Connected to PostgreSQL database")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            await self.conn.close()
            print("🔗 Database connection closed")
    
    async def get_table_counts(self) -> List[Tuple[str, int]]:
        """Get row counts for main tables"""
        tables = ['entries', 'topics', 'chat_sessions', 'chat_messages', 'entry_templates']
        counts = []
        
        for table in tables:
            try:
                count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                counts.append((table, count))
            except Exception as e:
                print(f"⚠️  Could not count {table}: {e}")
                counts.append((table, 0))
        
        return counts
    
    async def truncate_tables(self):
        """Truncate all main tables"""
        # Order matters due to foreign key constraints
        tables_to_truncate = [
            'chat_messages',        # References chat_sessions
            'chat_sessions',        # Main chat sessions table
            'entries',              # Main entries table
            'topics',               # Main topics table
            'entry_templates',      # Entry templates table
        ]
        
        print("🗑️  Truncating database tables...")
        
        # Disable foreign key checks temporarily
        await self.conn.execute("SET session_replication_role = replica")
        
        for table in tables_to_truncate:
            try:
                await self.conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                print(f"   ✅ Truncated {table}")
            except Exception as e:
                print(f"   ⚠️  Could not truncate {table}: {e}")
        
        # Re-enable foreign key checks
        await self.conn.execute("SET session_replication_role = DEFAULT")
        
        print("✅ Database truncation complete")
    
    async def cleanup_database(self):
        """Clean all data from the PostgreSQL database"""
        print("🧹 PostgreSQL Database Cleanup Starting...")
        print("=" * 50)
        print(f"🔗 Database: {self.db_url}")
        print()
        
        # Connect to database
        if not await self.connect():
            return False
        
        try:
            # Get current data counts
            print("📊 Checking current database content...")
            counts = await self.get_table_counts()
            
            total_records = sum(count for _, count in counts)
            
            print("Current data:")
            for table, count in counts:
                if count > 0:
                    print(f"  📋 {table}: {count} records")
            
            if total_records == 0:
                print("✅ Database is already clean!")
                return True
            
            print(f"\n📊 Total records to delete: {total_records}")
            print()
            
            # Truncate all tables
            await self.truncate_tables()
            
            # Verify cleanup
            print("\n🔍 Verifying cleanup...")
            counts_after = await self.get_table_counts()
            remaining_records = sum(count for _, count in counts_after)
            
            if remaining_records == 0:
                print("✅ Database successfully cleaned!")
                print("🎯 Ready for fresh data population.")
            else:
                print(f"⚠️  Some records remain: {remaining_records}")
                for table, count in counts_after:
                    if count > 0:
                        print(f"  📋 {table}: {count} records")
            
            return remaining_records == 0
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            return False
        finally:
            await self.close()

async def main():
    """Main cleanup function"""
    print("🤖 PostgreSQL Database Cleanup Tool")
    print("⚠️  This will delete ALL data from the PostgreSQL database!")
    print("📋 Tables: entries, topics, chat_sessions, chat_messages, entry_templates")
    print()
    
    # Safety confirmation
    try:
        confirm = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
        if confirm.lower() != 'yes':
            print("❌ Cleanup cancelled.")
            return
        print()
    except KeyboardInterrupt:
        print("\n❌ Cleanup cancelled.")
        return
    
    cleaner = PostgreSQLCleaner()
    success = await cleaner.cleanup_database()
    
    if success:
        print()
        print("🚀 Next steps:")
        print("  • Run: python populate_data.py --week")
        print("  • Test with a week of fresh data")
        print("  • Verify all features work with new data")
    else:
        print("\n❌ Cleanup incomplete - please check the errors above")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Cleanup interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        sys.exit(1)
