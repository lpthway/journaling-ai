#!/usr/bin/env python3
"""
Update database from simple models to enhanced models
Adds additional columns and indexes while preserving existing data
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings
from app.models.enhanced_models import Base, Entry, Topic
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Update database schema to enhanced models"""
    
    # Get database connection
    database_url = settings.DATABASE_URL
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            logger.info("Updating database schema to enhanced models...")
            
            # Add new columns to entries table if they don't exist
            logger.info("Adding new columns to entries table...")
            
            # Check if columns exist and add them if needed
            columns_to_add = [
                ("mood", "VARCHAR"),
                ("sentiment_score", "DOUBLE PRECISION"),
                ("word_count", "INTEGER DEFAULT 0"),
                ("reading_time", "INTEGER DEFAULT 0"),
                ("tags", "JSONB DEFAULT '[]'::jsonb"),
                ("psychology_metadata", "JSONB DEFAULT '{}'::jsonb"),
                ("analysis_results", "JSONB DEFAULT '{}'::jsonb"),
                ("search_vector", "tsvector"),
                ("version", "INTEGER DEFAULT 1"),
                ("is_favorite", "BOOLEAN DEFAULT FALSE"),
                ("ai_summary", "TEXT"),
                ("ai_insights", "JSONB DEFAULT '[]'::jsonb"),
                ("embedding", "vector(384)"),
                ("similarity_score", "DOUBLE PRECISION"),
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE entries 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """))
                    logger.info(f"Added column {column_name}")
                except Exception as e:
                    logger.warning(f"Could not add column {column_name}: {e}")
            
            # Add new columns to topics table if they don't exist
            logger.info("Adding new columns to topics table...")
            
            topic_columns_to_add = [
                ("color", "VARCHAR DEFAULT '#3B82F6'"),
                ("icon", "VARCHAR"),
                ("is_active", "BOOLEAN DEFAULT TRUE"),
                ("entry_count", "INTEGER DEFAULT 0"),
                ("psychology_category", "VARCHAR"),
                ("ai_suggestions", "JSONB DEFAULT '[]'::jsonb"),
                ("embedding", "vector(384)"),
            ]
            
            for column_name, column_type in topic_columns_to_add:
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE topics 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type}
                    """))
                    logger.info(f"Added column {column_name} to topics")
                except Exception as e:
                    logger.warning(f"Could not add column {column_name} to topics: {e}")
            
            # Create indexes (excluding the problematic gin_trgm_ops one)
            logger.info("Creating performance indexes...")
            
            indexes_to_create = [
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_entries_user_created ON entries (user_id, created_at)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_entries_topic_created ON entries (topic_id, created_at)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_entries_mood_sentiment ON entries (mood, sentiment_score)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_entries_favorites ON entries (user_id, is_favorite, created_at)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_entries_search_vector ON entries USING gin (search_vector)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_entries_tags_gin ON entries USING gin (tags)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_entries_psychology_gin ON entries USING gin (psychology_metadata)",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_entries_analysis_gin ON entries USING gin (analysis_results)",
            ]
            
            for index_sql in indexes_to_create:
                try:
                    await conn.execute(text(index_sql))
                    logger.info(f"Created index: {index_sql.split()[-1]}")
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")
            
            # Add constraints
            logger.info("Adding constraints...")
            
            constraints_to_add = [
                "ALTER TABLE entries ADD CONSTRAINT IF NOT EXISTS ck_entries_word_count_positive CHECK (word_count >= 0)",
                "ALTER TABLE entries ADD CONSTRAINT IF NOT EXISTS ck_entries_version_positive CHECK (version >= 1)",
                "ALTER TABLE entries ADD CONSTRAINT IF NOT EXISTS ck_entries_sentiment_range CHECK (sentiment_score BETWEEN -1 AND 1)",
            ]
            
            for constraint_sql in constraints_to_add:
                try:
                    await conn.execute(text(constraint_sql))
                    logger.info(f"Added constraint")
                except Exception as e:
                    logger.warning(f"Could not add constraint: {e}")
            
            # Update entry_count for topics
            logger.info("Updating topic entry counts...")
            await conn.execute(text("""
                UPDATE topics 
                SET entry_count = (
                    SELECT COUNT(*) 
                    FROM entries 
                    WHERE entries.topic_id = topics.id
                )
            """))
            
            logger.info("✅ Database successfully updated to enhanced models!")
            
    except Exception as e:
        logger.error(f"❌ Error updating database: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
