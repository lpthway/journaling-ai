#!/usr/bin/env python3
"""
Test PostgreSQL connection with proper SQLAlchemy 2.0 syntax
"""
import asyncio
import sys
import traceback
sys.path.insert(0, '.')

async def test_connection():
    try:
        from app.core.config import settings
        print(f'Database URL: {settings.DATABASE_URL}')
        
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        engine = create_async_engine(settings.DATABASE_URL)
        
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute(text('SELECT 1 as test'))
            row = result.fetchone()
            print(f'✅ Database connection successful! Test query result: {row}')
            
        # Test table existence
        async with engine.begin() as conn:
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            result = await conn.execute(query)
            tables = result.fetchall()
            table_names = [table[0] for table in tables]
            print(f'📋 Tables in database ({len(table_names)}): {table_names}')
            
        # Test user count
        async with engine.begin() as conn:
            result = await conn.execute(text('SELECT COUNT(*) FROM users'))
            user_count = result.scalar()
            print(f'👥 Total users: {user_count}')
            
        # Test journal entries count
        async with engine.begin() as conn:
            result = await conn.execute(text('SELECT COUNT(*) FROM journal_entries'))
            entry_count = result.scalar()
            print(f'📝 Total journal entries: {entry_count}')
            
        await engine.dispose()
        print('🔌 Connection closed successfully')
        print('\n🎉 PostgreSQL integration is working perfectly!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_connection())
