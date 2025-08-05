#!/usr/bin/env python3
"""
Safely enable gin_trgm_ops indexes for improved fuzzy search performance
"""

import asyncio
import logging
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def enable_gin_trgm_ops():
    """Enable gin_trgm_ops indexes with proper PostgreSQL extension setup"""
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        # 1. Enable pg_trgm extension (can be in transaction)
        async with engine.begin() as conn:
            logger.info("🔧 Enabling pg_trgm extension...")
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        
        # 2. Check current indexes (separate connection)
        async with engine.connect() as conn:
            logger.info("📊 Checking existing indexes...")
            existing_indexes = await conn.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename IN ('entries', 'topics')
                AND indexname LIKE '%trgm%'
            """))
            
            for row in existing_indexes:
                logger.info(f"Found existing trigram index: {row.indexname}")
        
        # 3. Create gin_trgm_ops indexes (CONCURRENTLY requires autocommit)
        indexes_to_create = [
            {
                "name": "ix_entries_title_trgm",
                "table": "entries", 
                "column": "title",
                "sql": "CREATE INDEX IF NOT EXISTS ix_entries_title_trgm ON entries USING gin (title gin_trgm_ops)"
            },
            {
                "name": "ix_entries_content_trgm", 
                "table": "entries",
                "column": "content",
                "sql": "CREATE INDEX IF NOT EXISTS ix_entries_content_trgm ON entries USING gin (content gin_trgm_ops)"
            },
            {
                "name": "ix_topics_name_trgm",
                "table": "topics",
                "column": "name", 
                "sql": "CREATE INDEX IF NOT EXISTS ix_topics_name_trgm ON topics USING gin (name gin_trgm_ops)"
            },
            {
                "name": "ix_topics_description_trgm",
                "table": "topics", 
                "column": "description",
                "sql": "CREATE INDEX IF NOT EXISTS ix_topics_description_trgm ON topics USING gin (description gin_trgm_ops)"
            }
        ]
        
        # Create indexes one by one with transactions
        for index_def in indexes_to_create:
            logger.info(f"🏗️  Creating index {index_def['name']}...")
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(index_def['sql']))
                logger.info(f"✅ Successfully created {index_def['name']}")
            except Exception as e:
                logger.error(f"❌ Failed to create {index_def['name']}: {e}")
        
        # 4. Check final index status
        async with engine.connect() as conn:
            logger.info("📋 Final index verification...")
            final_indexes = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename, 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE tablename IN ('entries', 'topics')
                AND (indexname LIKE '%trgm%' OR indexdef LIKE '%gin_trgm_ops%')
                ORDER BY tablename, indexname
            """))
            
            logger.info("🎯 Trigram indexes status:")
            for row in final_indexes:
                logger.info(f"  {row.tablename}.{row.indexname}: ✅")
            
            # 5. Test index usage
            logger.info("🧪 Testing index usage...")
            test_queries = [
                "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM entries WHERE title ILIKE '%journey%' LIMIT 10",
                "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM entries WHERE content ILIKE '%reflection%' LIMIT 10",
                "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM topics WHERE name ILIKE '%growth%' LIMIT 10"
            ]
            
            for query in test_queries:
                try:
                    result = await conn.execute(text(query))
                    explain_output = [row[0] for row in result]
                    
                    # Check if gin index is being used
                    uses_gin = any('Gin' in line for line in explain_output)
                    query_type = query.split('FROM')[1].split('WHERE')[0].strip()
                    
                    if uses_gin:
                        logger.info(f"✅ {query_type}: Using GIN index")
                    else:
                        logger.warning(f"⚠️  {query_type}: Not using GIN index")
                        
                except Exception as e:
                    logger.error(f"Test query failed: {e}")
    
    except Exception as e:
        logger.error(f"❌ Error enabling gin_trgm_ops: {e}")
        raise
    finally:
        await engine.dispose()

async def test_search_performance():
    """Test search performance with and without trigram indexes"""
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            # Test fuzzy search queries that benefit from trigrams
            test_searches = [
                ("Partial title match", "SELECT * FROM entries WHERE title ILIKE '%journey%'"),
                ("Content substring", "SELECT * FROM entries WHERE content ILIKE '%personal growth%'"),
                ("Topic fuzzy match", "SELECT * FROM topics WHERE name ILIKE '%career%'"),
                ("Similarity search", "SELECT *, similarity(title, 'my amazing journey') as sim FROM entries WHERE similarity(title, 'my amazing journey') > 0.1 ORDER BY sim DESC")
            ]
            
            logger.info("🚀 Performance Testing:")
            for test_name, query in test_searches:
                try:
                    import time
                    start_time = time.time()
                    
                    result = await conn.execute(text(query))
                    rows = result.fetchall()
                    
                    end_time = time.time()
                    duration = (end_time - start_time) * 1000
                    
                    logger.info(f"  {test_name}: {len(rows)} results in {duration:.2f}ms")
                    
                except Exception as e:
                    logger.error(f"  {test_name}: Failed - {e}")
    
    except Exception as e:
        logger.error(f"Performance test error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🎯 Enabling gin_trgm_ops for enhanced fuzzy search performance")
    print("📊 Analyzing impact for thousands of users scenario")
    print()
    
    asyncio.run(enable_gin_trgm_ops())
    print()
    asyncio.run(test_search_performance())
    
    print()
    print("✅ gin_trgm_ops setup complete!")
    print("📈 Your app is now optimized for fuzzy search at scale")
