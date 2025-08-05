#!/usr/bin/env python3
"""
Create default user in database
"""

import asyncio
import logging
from app.core.config import settings
from app.models.enhanced_models import Base, User
from app.services.unified_database_service import DEFAULT_USER_UUID
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Create default user if it doesn't exist"""
    
    database_url = settings.DATABASE_URL
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Create all tables first
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        
        # Use a session for user creation
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            # Check if default user exists
            result = await session.execute(
                select(User).where(User.id == DEFAULT_USER_UUID)
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Create default user using ORM
                user = User(
                    id=DEFAULT_USER_UUID,
                    username='default_user',
                    display_name='Default User',
                    timezone='UTC',
                    language='en',
                    preferences={},
                    psychology_profile={}
                )
                
                session.add(user)
                await session.commit()
                logger.info(f"✅ Created default user with ID: {DEFAULT_USER_UUID}")
            else:
                logger.info(f"✅ Default user already exists with ID: {DEFAULT_USER_UUID}")
            
    except Exception as e:
        logger.error(f"❌ Error creating default user: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
