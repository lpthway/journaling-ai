#!/usr/bin/env python3
"""
Script to recreate the database from scratch with correct schema
and migrate data from JSON files
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import uuid

from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
import asyncpg

from app.core.config import settings
from app.models.simple_models import Base, Entry, Topic  # Use simplified models
from app.core.database import database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def drop_and_recreate_database():
    """Drop all tables and recreate them with correct schema"""
    try:
        # Connect to database and drop all tables
        logger.info("🗑️ Dropping existing tables...")
        
        # Use asyncpg to connect directly
        conn = await asyncpg.connect(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
        
        # Drop all tables in public schema
        await conn.execute("""
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO postgres;
            GRANT ALL ON SCHEMA public TO public;
        """)
        
        await conn.close()
        logger.info("✅ All tables dropped successfully")
        
        # Now create tables with correct schema
        logger.info("🔨 Creating new tables with correct schema...")
        
        # Create async engine for SQLAlchemy
        engine = create_async_engine(settings.DATABASE_URL)
        
        async with engine.begin() as conn:
            # Create all tables from models
            await conn.run_sync(Base.metadata.create_all)
        
        await engine.dispose()
        logger.info("✅ New tables created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error recreating database: {e}")
        raise

def load_json_data(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ Error loading {file_path}: {e}")
        return {}

def parse_datetime(date_str: str) -> datetime:
    """Parse datetime string from JSON"""
    try:
        # Try different datetime formats
        for fmt in ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If none work, try fromisoformat
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except Exception as e:
        logger.warning(f"Could not parse datetime '{date_str}': {e}")
        return datetime.utcnow()

async def migrate_entries_from_json():
    """Migrate entry data from JSON file"""
    logger.info("📝 Migrating entries from JSON...")
    
    entries_file = Path(__file__).parent / "data" / "entries.json"
    if not entries_file.exists():
        logger.warning(f"Entries file not found: {entries_file}")
        return
    
    entries_data = load_json_data(str(entries_file))
    if not entries_data:
        logger.warning("No entries data found")
        return
    
    # Initialize database
    await database.initialize()
    
    success_count = 0
    error_count = 0
    
    async with database.get_session() as session:
        for entry_id, entry_data in entries_data.items():
            try:
                # Skip entries that are just metadata or incomplete
                if not entry_data.get('title') or not entry_data.get('content'):
                    continue
                
                # Create Entry object
                entry = Entry(
                    id=uuid.UUID(entry_id) if entry_id != entry_data.get('id') else uuid.UUID(entry_data['id']),
                    title=entry_data['title'],
                    content=entry_data['content'],
                    user_id=uuid.UUID('00000000-0000-0000-0000-000000000001'),  # Default user UUID
                    topic_id=uuid.UUID(entry_data['topic_id']) if entry_data.get('topic_id') and entry_data['topic_id'] else None,
                    word_count=entry_data.get('word_count', len(entry_data['content'].split())),
                    reading_time_minutes=entry_data.get('reading_time_minutes', max(1, len(entry_data['content'].split()) // 200)),
                    mood=entry_data.get('mood'),
                    sentiment_score=entry_data.get('sentiment_score'),
                    tags=entry_data.get('tags', []),
                    auto_tags=[],  # Empty for now
                    psychology_tags=[],  # Empty for now
                    is_favorite=entry_data.get('is_favorite', False),
                    is_private=entry_data.get('is_private', False),
                    version=1,
                    psychology_metadata=entry_data.get('metadata', {}),
                    analysis_results={},
                    created_at=parse_datetime(entry_data['created_at']) if entry_data.get('created_at') else datetime.utcnow(),
                    updated_at=parse_datetime(entry_data['updated_at']) if entry_data.get('updated_at') else datetime.utcnow()
                )
                
                session.add(entry)
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error migrating entry {entry_id}: {e}")
                error_count += 1
                continue
        
        try:
            await session.commit()
            logger.info(f"✅ Successfully migrated {success_count} entries ({error_count} errors)")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error committing entries: {e}")

async def migrate_topics_from_json():
    """Migrate topic data from JSON file"""
    logger.info("🏷️ Migrating topics from JSON...")
    
    topics_file = Path(__file__).parent / "data" / "topics.json"
    if not topics_file.exists():
        logger.warning(f"Topics file not found: {topics_file}")
        return
    
    topics_data = load_json_data(str(topics_file))
    if not topics_data:
        logger.warning("No topics data found")
        return
    
    # Initialize database
    await database.initialize()
    
    success_count = 0
    error_count = 0
    
    async with database.get_session() as session:
        for topic_id, topic_data in topics_data.items():
            try:
                # Create Topic object
                topic = Topic(
                    id=uuid.UUID(topic_id),
                    name=topic_data.get('name', 'Untitled Topic'),
                    description=topic_data.get('description'),
                    color=topic_data.get('color', '#3B82F6'),
                    icon=topic_data.get('icon'),
                    user_id=uuid.UUID('00000000-0000-0000-0000-000000000001'),  # Default user UUID
                    tags=topic_data.get('tags', []),
                    psychology_domains=topic_data.get('psychology_domains', []),
                    topic_metadata=topic_data.get('metadata', {}),
                    entry_count=topic_data.get('entry_count', 0),
                    last_entry_date=parse_datetime(topic_data['last_entry_date']) if topic_data.get('last_entry_date') else None,
                    usage_statistics=topic_data.get('usage_statistics', {}),
                    created_at=parse_datetime(topic_data['created_at']) if topic_data.get('created_at') else datetime.utcnow(),
                    updated_at=parse_datetime(topic_data['updated_at']) if topic_data.get('updated_at') else datetime.utcnow()
                )
                
                session.add(topic)
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error migrating topic {topic_id}: {e}")
                error_count += 1
                continue
        
        try:
            await session.commit()
            logger.info(f"✅ Successfully migrated {success_count} topics ({error_count} errors)")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error committing topics: {e}")

async def main():
    """Main function to recreate database and migrate data"""
    logger.info("🚀 Starting database recreation and migration...")
    
    try:
        # Step 1: Drop and recreate database schema
        await drop_and_recreate_database()
        
        # Step 2: Migrate topics FIRST (since entries reference topics)
        await migrate_topics_from_json()
        
        # Step 3: Migrate entries AFTER topics exist
        await migrate_entries_from_json()
        
        logger.info("🎉 Database recreation and migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
