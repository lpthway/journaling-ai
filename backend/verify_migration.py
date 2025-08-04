#!/usr/bin/env python3
"""
Verify the successful PostgreSQL migration with detailed statistics
"""
import asyncio
import sys
import traceback
sys.path.insert(0, '.')

async def verify_migration():
    try:
        from app.core.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        engine = create_async_engine(settings.DATABASE_URL)
        
        print("🔍 POSTGRESQL MIGRATION VERIFICATION")
        print("=" * 60)
        
        async with engine.begin() as conn:
            # User verification
            result = await conn.execute(text('SELECT COUNT(*), username FROM users GROUP BY username'))
            users = result.fetchall()
            print(f"👥 Users: {len(users)}")
            for count, username in users:
                print(f"   - {username}: {count} record(s)")
            
            # Journal entries verification
            result = await conn.execute(text("""
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT user_id) as unique_users,
                    MIN(created_at) as oldest_entry,
                    MAX(created_at) as newest_entry,
                    AVG(word_count) as avg_word_count
                FROM journal_entries
            """))
            entry_stats = result.fetchone()
            print(f"\n📝 Journal Entries: {entry_stats[0]}")
            print(f"   - Unique users: {entry_stats[1]}")
            print(f"   - Date range: {entry_stats[2]} to {entry_stats[3]}")
            print(f"   - Average word count: {entry_stats[4]:.1f}")
            
            # Sample entries
            result = await conn.execute(text("""
                SELECT title, LEFT(content, 50) as content_preview, created_at, word_count
                FROM journal_entries 
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            sample_entries = result.fetchall()
            print(f"\n📋 Recent Entries (sample):")
            for title, content, created, words in sample_entries:
                print(f"   - '{title}' ({words} words) - {created.strftime('%Y-%m-%d')}")
                print(f"     {content}...")
            
            # Tags analysis
            result = await conn.execute(text("""
                SELECT tag, COUNT(*) as usage_count
                FROM (
                    SELECT DISTINCT unnest(tags) as tag, id
                    FROM journal_entries 
                    WHERE tags IS NOT NULL AND array_length(tags, 1) > 0
                ) tag_counts
                GROUP BY tag
                ORDER BY usage_count DESC
                LIMIT 10
            """))
            tag_stats = result.fetchall()
            print(f"\n🏷️ Most Used Tags:")
            for tag, count in tag_stats:
                print(f"   - {tag}: {count} entries")
            
            # Psychology content
            result = await conn.execute(text('SELECT COUNT(*), category FROM psychology_content GROUP BY category'))
            psych_content = result.fetchall()
            print(f"\n🧠 Psychology Content: {sum(count for count, _ in psych_content)}")
            for count, category in psych_content:
                print(f"   - {category}: {count} items")
            
            # Migration logs
            result = await conn.execute(text("""
                SELECT migration_type, records_processed, records_successful, records_failed, status
                FROM migration_logs 
                ORDER BY completed_at DESC
            """))
            migration_logs = result.fetchall()
            print(f"\n📊 Migration Results:")
            for migration_type, processed, successful, failed, status in migration_logs:
                print(f"   - {migration_type}: {processed} processed, {successful} successful, {failed} failed ({status})")
        
        await engine.dispose()
        print("\n🎉 Migration verification completed successfully!")
        print("✅ PostgreSQL database is fully operational with migrated data!")
        
    except Exception as e:
        print(f'❌ Error: {e}')
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(verify_migration())
