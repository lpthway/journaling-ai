#!/usr/bin/env python3
"""
Simple migration to enhanced models
Recreates tables with enhanced schema while preserving data
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models.enhanced_models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Update database schema to enhanced models"""
    
    # Get database connection
    database_url = settings.DATABASE_URL
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            logger.info("Creating enhanced model tables...")
            
            # Create all tables with enhanced models
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            
            logger.info("✅ Database successfully updated to enhanced models!")
            
    except Exception as e:
        logger.error(f"❌ Error updating database: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
