#!/usr/bin/env python3
"""
Manual table creation script to fix database schema issues
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import database
from sqlalchemy import text

async def create_missing_tables():
    """Create the missing tables that the application expects"""
    try:
        await database.initialize()
        
        async with database.get_session() as session:
            # Check if journal_entries exists
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'journal_entries'
                );
            """))
            has_journal_entries = result.scalar()
            
            if has_journal_entries:
                print("✅ Found journal_entries table")
                
                # Create entries table by copying structure from journal_entries
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS entries (LIKE journal_entries INCLUDING ALL);
                """))
                print("✅ Created entries table")
                
                # Copy data from journal_entries to entries if needed
                await session.execute(text("""
                    INSERT INTO entries 
                    SELECT * FROM journal_entries 
                    WHERE NOT EXISTS (SELECT 1 FROM entries WHERE entries.id = journal_entries.id);
                """))
                print("✅ Copied data to entries table")
            
            # Create topics table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS topics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    color VARCHAR(7) DEFAULT '#3B82F6',
                    icon VARCHAR(50),
                    parent_id UUID,
                    sort_order INTEGER DEFAULT 0,
                    user_id VARCHAR(255) NOT NULL DEFAULT 'default_user',
                    tags JSONB DEFAULT '[]'::jsonb,
                    psychology_domains JSONB DEFAULT '{}'::jsonb,
                    topic_metadata JSONB DEFAULT '{}'::jsonb,
                    entry_count INTEGER DEFAULT 0,
                    last_entry_date TIMESTAMP WITH TIME ZONE,
                    usage_statistics JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    deleted_at TIMESTAMP WITH TIME ZONE
                );
            """))
            print("✅ Created topics table")
            
            # Create indexes for topics
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_topics_user_name ON topics(user_id, name);
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_topics_created_at ON topics(created_at);
            """))
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_topics_deleted_at ON topics(deleted_at);
            """))
            print("✅ Created topics indexes")
            
            await session.commit()
            print("🎉 All tables created successfully!")
            
            # List all tables to verify
            result = await session.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            print("📋 Tables in database:", tables)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(create_missing_tables())
    sys.exit(0 if success else 1)
