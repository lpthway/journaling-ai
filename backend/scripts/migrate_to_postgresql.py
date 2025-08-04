# backend/scripts/migrate_to_postgresql.py - Data Migration Script

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import DatabaseConfig
from app.models.postgresql import (
    Base, User, JournalEntry, ChatSession, Conversation, 
    PsychologyContent, UserAnalytics, MigrationLog
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataMigrator:
    """Enterprise-grade data migration from JSON to PostgreSQL"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        self.engine = None
        self.async_session = None
        self.data_path = Path(settings.JSON_DATA_PATH)
        self.migration_stats = {
            'users': {'processed': 0, 'successful': 0, 'failed': 0},
            'entries': {'processed': 0, 'successful': 0, 'failed': 0},
            'sessions': {'processed': 0, 'successful': 0, 'failed': 0},
            'conversations': {'processed': 0, 'successful': 0, 'failed': 0},
            'psychology': {'processed': 0, 'successful': 0, 'failed': 0}
        }
    
    async def initialize_database(self):
        """Initialize database connection and create tables"""
        logger.info("Initializing PostgreSQL database...")
        
        try:
            # Create async engine
            self.engine = create_async_engine(
                settings.DATABASE_URL,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_recycle=settings.DB_POOL_RECYCLE,
                echo=settings.DB_ECHO
            )
            
            # Create session factory
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            
            # Create all tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    async def migrate_users(self) -> bool:
        """Migrate user data from JSON"""
        logger.info("🔄 Migrating users...")
        
        try:
            async with self.async_session() as session:
                # Check if default user already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(User).where(User.username == "default_user")
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    logger.info("✅ Default user already exists, using existing user")
                    self.default_user_id = existing_user.id
                    self.migration_stats['users']['processed'] = 1
                    self.migration_stats['users']['successful'] = 1
                else:
                    # Create default user since original system was single-user
                    default_user = User(
                        id=str(uuid.uuid4()),
                        username="default_user",
                        full_name="Journal User",
                        is_active=True,
                        preferences={
                            "language": "en",
                            "timezone": "UTC",
                            "ai_model": settings.OLLAMA_MODEL,
                            "sentiment_analysis": True,
                            "psychology_insights": True,
                            "notification_settings": {
                                "daily_reflection": True,
                                "weekly_summary": False,
                                "mood_alerts": True
                            }
                        },
                        created_at=datetime.now()
                    )
                    
                    session.add(default_user)
                    await session.commit()
                    
                    # Store default user ID for other migrations
                    self.default_user_id = default_user.id
                    
                    self.migration_stats['users']['processed'] = 1
                    self.migration_stats['users']['successful'] = 1
                    logger.info("✅ Default user created successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ User migration failed: {e}")
            self.migration_stats['users']['failed'] = 1
            return False
    
    async def migrate_journal_entries(self) -> bool:
        """Migrate journal entries from entries.json"""
        logger.info("🔄 Migrating journal entries...")
        
        entries_file = self.data_path / "entries.json"
        if not entries_file.exists():
            logger.warning("⚠️ entries.json not found, skipping...")
            return True
        
        try:
            with open(entries_file, 'r', encoding='utf-8') as f:
                entries_dict = json.load(f)
            
            # Handle both dict and list formats
            if isinstance(entries_dict, dict):
                entries_data = list(entries_dict.values())
            else:
                entries_data = entries_dict
            
            logger.info(f"📊 Found {len(entries_data)} entries to migrate")
            
            batch_size = settings.MIGRATION_BATCH_SIZE
            batch = []
            
            async with self.async_session() as session:
                # Get existing entry IDs to avoid duplicates
                from sqlalchemy import select
                result = await session.execute(select(JournalEntry.id))
                existing_ids = {row[0] for row in result.fetchall()}
                logger.info(f"📋 Found {len(existing_ids)} existing entries in database")
                
                for entry_data in entries_data:
                    try:
                        entry_id = entry_data.get('id', str(uuid.uuid4()))
                        
                        # Skip if entry already exists
                        if entry_id in existing_ids:
                            logger.debug(f"⏭️ Skipping existing entry: {entry_id}")
                            continue
                        
                        # Parse entry date - try different date fields
                        date_str = entry_data.get('date') or entry_data.get('created_at', '2024-01-01')
                        if 'T' in date_str:
                            entry_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                        else:
                            entry_date = datetime.fromisoformat(date_str).date()
                        
                        # Calculate word count
                        content = entry_data.get('content', '')
                        word_count = len(content.split()) if content else 0
                        
                        # Extract mood score
                        mood_score = entry_data.get('mood_score')
                        if mood_score and (mood_score < 1 or mood_score > 10):
                            mood_score = None
                        
                        # Create journal entry
                        entry = JournalEntry(
                            id=entry_id,
                            user_id=self.default_user_id,
                            title=entry_data.get('title'),
                            content=content,
                            entry_date=entry_date,
                            mood_score=mood_score,
                            word_count=word_count,
                            language=entry_data.get('language', 'en'),
                            sentiment_analysis=entry_data.get('sentiment_analysis'),
                            emotion_analysis=entry_data.get('emotion_analysis'),
                            topic_analysis=entry_data.get('topic_analysis'),
                            psychology_insights=entry_data.get('psychology_insights'),
                            categories=entry_data.get('categories', []),
                            tags=entry_data.get('tags', []),
                            is_private=entry_data.get('is_private', True),
                            created_at=datetime.fromisoformat(
                                entry_data.get('created_at', datetime.now().isoformat()).replace('Z', '+00:00')
                            )
                        )
                        
                        batch.append(entry)
                        self.migration_stats['entries']['processed'] += 1
                        
                        # Process batch
                        if len(batch) >= batch_size:
                            session.add_all(batch)
                            await session.commit()
                            self.migration_stats['entries']['successful'] += len(batch)
                            logger.info(f"✅ Processed {len(batch)} entries")
                            batch = []
                    
                    except Exception as e:
                        logger.error(f"❌ Failed to process entry {entry_data.get('id', 'unknown')}: {e}")
                        self.migration_stats['entries']['failed'] += 1
                        continue
                
                # Process remaining batch
                if batch:
                    session.add_all(batch)
                    await session.commit()
                    self.migration_stats['entries']['successful'] += len(batch)
                    logger.info(f"✅ Processed final batch of {len(batch)} entries")
            
            logger.info(f"✅ Journal entries migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Journal entries migration failed: {e}")
            return False
    
    async def migrate_chat_sessions(self) -> bool:
        """Migrate chat sessions from sessions.json"""
        logger.info("🔄 Migrating chat sessions...")
        
        sessions_file = self.data_path / "sessions.json"
        if not sessions_file.exists():
            logger.warning("⚠️ sessions.json not found, skipping...")
            return True
        
        try:
            with open(sessions_file, 'r', encoding='utf-8') as f:
                sessions_dict = json.load(f)
            
            # Handle both dict and list formats
            if isinstance(sessions_dict, dict):
                sessions_data = list(sessions_dict.values())
            else:
                sessions_data = sessions_dict
            
            session_id_mapping = {}  # Old ID -> New ID mapping
            
            async with self.async_session() as session:
                for session_data in sessions_data:
                    try:
                        new_session_id = str(uuid.uuid4())
                        old_session_id = session_data.get('id')
                        
                        chat_session = ChatSession(
                            id=new_session_id,
                            user_id=self.default_user_id,
                            title=session_data.get('title'),
                            session_type=session_data.get('type', 'general'),
                            context=session_data.get('context', {}),
                            ai_model=session_data.get('ai_model', settings.OLLAMA_MODEL),
                            system_prompt=session_data.get('system_prompt'),
                            temperature=session_data.get('temperature', 0.7),
                            is_active=session_data.get('is_active', True),
                            message_count=session_data.get('message_count', 0),
                            created_at=datetime.fromisoformat(
                                session_data.get('created_at', datetime.now().isoformat()).replace('Z', '+00:00')
                            )
                        )
                        
                        session.add(chat_session)
                        session_id_mapping[old_session_id] = new_session_id
                        self.migration_stats['sessions']['processed'] += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to process session: {e}")
                        self.migration_stats['sessions']['failed'] += 1
                        continue
                
                await session.commit()
                self.migration_stats['sessions']['successful'] = len(session_id_mapping)
                
                # Store mapping for conversation migration
                self.session_id_mapping = session_id_mapping
            
            logger.info("✅ Chat sessions migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Chat sessions migration failed: {e}")
            return False
    
    async def migrate_conversations(self) -> bool:
        """Migrate conversations from messages.json"""
        logger.info("🔄 Migrating conversations...")
        
        messages_file = self.data_path / "messages.json"
        if not messages_file.exists():
            logger.warning("⚠️ messages.json not found, skipping...")
            return True
        
        try:
            with open(messages_file, 'r', encoding='utf-8') as f:
                messages_dict = json.load(f)
            
            # Handle both dict and list formats
            if isinstance(messages_dict, dict):
                messages_data = list(messages_dict.values())
            else:
                messages_data = messages_dict
            
            batch_size = settings.MIGRATION_BATCH_SIZE
            batch = []
            
            async with self.async_session() as session:
                for message_data in messages_data:
                    try:
                        old_session_id = message_data.get('session_id')
                        new_session_id = getattr(self, 'session_id_mapping', {}).get(old_session_id)
                        
                        if not new_session_id:
                            logger.warning(f"⚠️ Session ID {old_session_id} not found in mapping, skipping")
                            continue
                        
                        conversation = Conversation(
                            id=str(uuid.uuid4()),
                            session_id=new_session_id,
                            user_message=message_data.get('user_message', ''),
                            ai_response=message_data.get('ai_response', ''),
                            processing_time_ms=message_data.get('processing_time_ms'),
                            ai_model_used=message_data.get('ai_model_used', settings.OLLAMA_MODEL),
                            token_usage=message_data.get('token_usage'),
                            sources_used=message_data.get('sources_used'),
                            citations=message_data.get('citations'),
                            confidence_score=message_data.get('confidence_score'),
                            user_feedback=message_data.get('user_feedback'),
                            created_at=datetime.fromisoformat(
                                message_data.get('created_at', datetime.now().isoformat()).replace('Z', '+00:00')
                            )
                        )
                        
                        batch.append(conversation)
                        self.migration_stats['conversations']['processed'] += 1
                        
                        # Process batch
                        if len(batch) >= batch_size:
                            session.add_all(batch)
                            await session.commit()
                            self.migration_stats['conversations']['successful'] += len(batch)
                            logger.info(f"✅ Processed {len(batch)} conversations")
                            batch = []
                    
                    except Exception as e:
                        logger.error(f"❌ Failed to process conversation: {e}")
                        self.migration_stats['conversations']['failed'] += 1
                        continue
                
                # Process remaining batch
                if batch:
                    session.add_all(batch)
                    await session.commit()
                    self.migration_stats['conversations']['successful'] += len(batch)
                    logger.info(f"✅ Processed final batch of {len(batch)} conversations")
            
            logger.info("✅ Conversations migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Conversations migration failed: {e}")
            return False
    
    async def migrate_psychology_content(self) -> bool:
        """Migrate psychology content"""
        logger.info("🔄 Migrating psychology content...")
        
        # Create sample psychology content since we don't have existing data
        sample_content = [
            {
                "category": "CBT",
                "subcategory": "Thought Challenging",
                "content_type": "technique",
                "title": "Cognitive Restructuring",
                "content": "A technique to identify and challenge negative thought patterns by examining evidence for and against automatic thoughts.",
                "summary": "Challenge negative thoughts with evidence-based questioning.",
                "source": "Beck, A.T. (1976). Cognitive Therapy and the Emotional Disorders",
                "evidence_level": "high",
                "tags": ["anxiety", "depression", "thoughts"],
                "keywords": ["cognitive", "restructuring", "thoughts", "challenge"]
            },
            {
                "category": "Mindfulness",
                "subcategory": "Meditation",
                "content_type": "exercise",
                "title": "Body Scan Meditation",
                "content": "A mindfulness practice that involves systematic attention to different parts of the body to develop awareness and relaxation.",
                "summary": "Develop awareness through systematic body attention.",
                "source": "Kabat-Zinn, J. (1994). Wherever You Go, There You Are",
                "evidence_level": "high",
                "tags": ["mindfulness", "relaxation", "body awareness"],
                "keywords": ["body", "scan", "meditation", "awareness"]
            }
        ]
        
        try:
            async with self.async_session() as session:
                for content_data in sample_content:
                    try:
                        psychology_content = PsychologyContent(
                            id=str(uuid.uuid4()),
                            category=content_data['category'],
                            subcategory=content_data.get('subcategory'),
                            content_type=content_data['content_type'],
                            title=content_data['title'],
                            content=content_data['content'],
                            summary=content_data.get('summary'),
                            source=content_data.get('source'),
                            evidence_level=content_data.get('evidence_level', 'moderate'),
                            tags=content_data.get('tags', []),
                            keywords=content_data.get('keywords', []),
                            usage_count=0,
                            created_at=datetime.now()
                        )
                        
                        session.add(psychology_content)
                        self.migration_stats['psychology']['processed'] += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to process psychology content: {e}")
                        self.migration_stats['psychology']['failed'] += 1
                        continue
                
                await session.commit()
                self.migration_stats['psychology']['successful'] = self.migration_stats['psychology']['processed']
            
            logger.info("✅ Psychology content migration completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Psychology content migration failed: {e}")
            return False
    
    async def log_migration_results(self):
        """Log migration results to database and file"""
        logger.info("📊 Logging migration results...")
        
        try:
            async with self.async_session() as session:
                for migration_type, stats in self.migration_stats.items():
                    migration_log = MigrationLog(
                        id=str(uuid.uuid4()),
                        migration_type=migration_type,
                        source_file=f"{migration_type}.json",
                        records_processed=stats['processed'],
                        records_successful=stats['successful'],
                        records_failed=stats['failed'],
                        status="completed" if stats['failed'] == 0 else "completed_with_errors",
                        validation_passed=stats['failed'] == 0,
                        completed_at=datetime.now()
                    )
                    session.add(migration_log)
                
                await session.commit()
            
            # Print summary
            logger.info("\n" + "="*60)
            logger.info("📊 MIGRATION SUMMARY")
            logger.info("="*60)
            total_processed = sum(stats['processed'] for stats in self.migration_stats.values())
            total_successful = sum(stats['successful'] for stats in self.migration_stats.values())
            total_failed = sum(stats['failed'] for stats in self.migration_stats.values())
            
            for migration_type, stats in self.migration_stats.items():
                logger.info(f"{migration_type.capitalize():12} | {stats['processed']:8} | {stats['successful']:8} | {stats['failed']:8}")
            
            logger.info("-" * 60)
            logger.info(f"{'TOTAL':12} | {total_processed:8} | {total_successful:8} | {total_failed:8}")
            logger.info("="*60)
            
            if total_failed == 0:
                logger.info("🎉 Migration completed successfully!")
            else:
                logger.warning(f"⚠️ Migration completed with {total_failed} failures")
            
        except Exception as e:
            logger.error(f"❌ Failed to log migration results: {e}")
    
    async def cleanup(self):
        """Cleanup database connections"""
        if self.engine:
            await self.engine.dispose()
    
    async def run_migration(self):
        """Run complete data migration"""
        start_time = datetime.now()
        logger.info("🚀 Starting PostgreSQL migration...")
        
        try:
            # Initialize database
            if not await self.initialize_database():
                return False
            
            # Run migrations in order
            migrations = [
                ("Users", self.migrate_users),
                ("Journal Entries", self.migrate_journal_entries),
                ("Chat Sessions", self.migrate_chat_sessions),
                ("Conversations", self.migrate_conversations),
                ("Psychology Content", self.migrate_psychology_content)
            ]
            
            for name, migration_func in migrations:
                logger.info(f"\n📋 Starting {name} migration...")
                if not await migration_func():
                    logger.error(f"❌ {name} migration failed")
                    return False
            
            # Log results
            await self.log_migration_results()
            
            # Calculate total time
            total_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"\n⏱️ Total migration time: {total_time:.2f} seconds")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        
        finally:
            await self.cleanup()

async def main():
    """Main migration entry point"""
    migrator = DataMigrator()
    success = await migrator.run_migration()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
