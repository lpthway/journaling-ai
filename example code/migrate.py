# migrate.py
"""
Command-line tool for database migration from JSON to PostgreSQL.

Usage:
    python migrate.py validate          # Validate source data only
    python migrate.py migrate           # Run full migration
    python migrate.py status            # Check migration status
    python migrate.py rollback          # Rollback migration (if possible)
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

from backend.app.core.database import DatabaseManager, DatabaseConfig
from backend.app.services.data_migration_service import DataMigrationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)

class MigrationCLI:
    """Command-line interface for database migration operations."""
    
    def __init__(self):
        self.db_config = DatabaseConfig(
            url="postgresql+asyncpg://postgres:password@localhost/journaling_assistant",
            pool_size=5,  # Smaller pool for migration
            max_overflow=2,
            echo=False
        )
        self.db_manager = DatabaseManager(self.db_config)
        self.migration_service = None
        
    async def initialize(self):
        """Initialize database connection and migration service."""
        await self.db_manager.initialize()
        self.migration_service = DataMigrationService(
            self.db_manager, 
            data_dir=Path("./data")
        )
        logger.info("✅ Migration CLI initialized")
    
    async def validate_command(self) -> Dict[str, Any]:
        """Validate source JSON data without migrating."""
        logger.info("🔍 Starting data validation...")
        
        result = await self.migration_service.migrate_all_data(
            batch_size=1000,
            validate_only=True
        )
        
        if result['success']:
            logger.info("✅ Data validation completed successfully")
            self._print_validation_results(result['details'])
        else:
            logger.error("❌ Data validation failed")
            self._print_errors(result.get('details', {}))
        
        return result
    
    async def migrate_command(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Run the full migration process."""
        logger.info("🚀 Starting database migration...")
        
        # First validate
        validation_result = await self.validate_command()
        if not validation_result['success']:
            logger.error("❌ Cannot proceed with migration - validation failed")
            return validation_result
        
        # Run migration
        result = await self.migration_service.migrate_all_data(
            batch_size=batch_size,
            validate_only=False
        )
        
        if result['success']:
            logger.info("✅ Migration completed successfully")
            self._print_migration_results(result)
            self._save_migration_report(result)
        else:
            logger.error("❌ Migration failed")
            self._print_errors(result)
        
        return result
    
    async def status_command(self) -> Dict[str, Any]:
        """Check migration status and database health."""
        logger.info("📊 Checking migration status...")
        
        try:
            # Check database connectivity
            health_check = await self.db_manager.health_check()
            if not health_check:
                return {
                    'success': False,
                    'error': 'Database not accessible'
                }
            
            # Get pool status
            pool_status = await self.db_manager.get_pool_status()
            
            # Check if migration has been run
            async with self.db_manager.get_session() as session:
                from backend.app.models.database_models import User, Entry, ChatSession
                from sqlalchemy import select, func
                
                user_count = await session.scalar(select(func.count(User.id)))
                entry_count = await session.scalar(select(func.count(Entry.id)))
                session_count = await session.scalar(select(func.count(ChatSession.id)))
                
                status = {
                    'success': True,
                    'database_health': 'healthy' if health_check else 'unhealthy',
                    'pool_status': pool_status,
                    'migration_status': 'completed' if user_count > 0 else 'not_started',
                    'statistics': {
                        'users': user_count,
                        'entries': entry_count,
                        'sessions': session_count
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                logger.info("✅ Status check completed")
                self._print_status(status)
                return status
                
        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def rollback_command(self) -> Dict[str, Any]:
        """Rollback migration (truncate all tables)."""
        logger.warning("⚠️  Starting migration rollback...")
        
        try:
            async with self.db_manager.get_session() as session:
                # Truncate tables in reverse dependency order
                await session.execute("TRUNCATE chat_messages CASCADE")
                await session.execute("TRUNCATE chat_sessions CASCADE")
                await session.execute("TRUNCATE entries CASCADE")
                await session.execute("TRUNCATE entry_templates CASCADE")
                await session.execute("TRUNCATE topics CASCADE")
                await session.execute("TRUNCATE users CASCADE")
                await session.commit()
                
                logger.info("✅ Rollback completed - all data removed")
                return {'success': True, 'message': 'Migration rolled back successfully'}
                
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _print_validation_results(self, details: Dict[str, Any]):
        """Print validation results in a readable format."""
        print("\n" + "="*60)
        print("📋 VALIDATION RESULTS")
        print("="*60)
        
        print(f"Overall Status: {'✅ VALID' if details['valid'] else '❌ INVALID'}")
        print(f"\nFiles Found:")
        for filename, found in details['files_found'].items():
            status = "✅" if found else "❌"
            count = details['record_counts'].get(filename, 0)
            print(f"  {status} {filename}: {count} records")
        
        if details['issues']:
            print(f"\n⚠️  Issues Found:")
            for issue in details['issues']:
                print(f"  • {issue}")
        
        print("="*60 + "\n")
    
    def _print_migration_results(self, result: Dict[str, Any]):
        """Print migration results in a readable format."""
        stats = result['statistics']
        
        print("\n" + "="*60)
        print("🎉 MIGRATION COMPLETED")
        print("="*60)
        
        print(f"Duration: {result['duration_seconds']:.2f} seconds")
        print(f"\nMigrated Records:")
        print(f"  👤 Users: {stats['users_migrated']}")
        print(f"  📁 Topics: {stats['topics_migrated']}")
        print(f"  📝 Entries: {stats['entries_migrated']}")
        print(f"  💬 Sessions: {stats['sessions_migrated']}")
        print(f"  💭 Messages: {stats['messages_migrated']}")
        
        if stats['errors']:
            print(f"\n⚠️  Errors ({len(stats['errors'])}):")
            for error in stats['errors'][:5]:  # Show first 5 errors
                print(f"  • {error}")
            if len(stats['errors']) > 5:
                print(f"  ... and {len(stats['errors']) - 5} more errors")
        
        print("="*60 + "\n")
    
    def _print_status(self, status: Dict[str, Any]):
        """Print status information in a readable format."""
        print("\n" + "="*60)
        print("📊 DATABASE STATUS")
        print("="*60)
        
        print(f"Health: {'✅ Healthy' if status['database_health'] == 'healthy' else '❌ Unhealthy'}")
        print(f"Migration: {'✅ Completed' if status['migration_status'] == 'completed' else '⏳ Not Started'}")
        
        print(f"\nRecord Counts:")
        for table, count in status['statistics'].items():
            print(f"  {table.title()}: {count:,}")
        
        pool = status['pool_status']
        print(f"\nConnection Pool:")
        print(f"  Size: {pool.get('size', 'N/A')}")
        print(f"  Checked out: {pool.get('checked_out', 'N/A')}")
        print(f"  Available: {pool.get('checked_in', 'N/A')}")
        
        print("="*60 + "\n")
    
    def _print_errors(self, errors: Dict[str, Any]):
        """Print error information."""
        print("\n" + "="*60)
        print("❌ ERRORS")
        print("="*60)
        
        if isinstance(errors, dict):
            for key, value in errors.items():
                print(f"{key}: {value}")
        else:
            print(str(errors))
        
        print("="*60 + "\n")
    
    def _save_migration_report(self, result: Dict[str, Any]):
        """Save detailed migration report to file."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = f"migration_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"📄 Migration report saved to {report_file}")
        except Exception as e:
            logger.warning(f"Failed to save migration report: {e}")
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.db_manager:
            await self.db_manager.close()
        logger.info("🔄 Migration CLI cleanup completed")

async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database Migration Tool - JSON to PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate.py validate                    # Validate source data
  python migrate.py migrate                     # Run full migration  
  python migrate.py migrate --batch-size 500   # Custom batch size
  python migrate.py status                      # Check status
  python migrate.py rollback                    # Rollback migration
        """
    )
    
    parser.add_argument(
        'command',
        choices=['validate', 'migrate', 'status', 'rollback'],
        help='Migration command to execute'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for migration processing (default: 1000)'
    )
    
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path('./data'),
        help='Directory containing JSON data files (default: ./data)'
    )
    
    parser.add_argument(
        '--db-url',
        type=str,
        default="postgresql+asyncpg://postgres:password@localhost/journaling_assistant",
        help='Database connection URL'
    )
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = MigrationCLI()
    cli.db_config.url = args.db_url
    cli.migration_service = DataMigrationService(cli.db_manager, args.data_dir)
    
    try:
        await cli.initialize()
        
        # Execute command
        if args.command == 'validate':
            result = await cli.validate_command()
        elif args.command == 'migrate':
            result = await cli.migrate_command(args.batch_size)
        elif args.command == 'status':
            result = await cli.status_command()
        elif args.command == 'rollback':
            result = await cli.rollback_command()
        
        # Exit with appropriate code
        sys.exit(0 if result['success'] else 1)
        
    except KeyboardInterrupt:
        logger.info("⏹️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)
    finally:
        await cli.cleanup()

if __name__ == "__main__":
    asyncio.run(main())