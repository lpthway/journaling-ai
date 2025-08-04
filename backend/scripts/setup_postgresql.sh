#!/bin/bash
# backend/scripts/setup_postgresql.sh - PostgreSQL Setup and Migration Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DB_NAME="journaling_ai"
DB_USER="postgres"
DB_PASSWORD="password"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="./backups"

echo -e "${BLUE}🐘 PostgreSQL Setup and Migration Script${NC}"
echo -e "${BLUE}======================================${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if PostgreSQL is installed
check_postgresql() {
    print_info "Checking PostgreSQL installation..."
    
    if command -v psql &> /dev/null; then
        print_status "PostgreSQL client found"
        psql --version
    else
        print_error "PostgreSQL client not found. Please install PostgreSQL."
        print_info "Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
        print_info "macOS: brew install postgresql"
        print_info "Windows: Download from https://www.postgresql.org/download/"
        exit 1
    fi
}

# Check if PostgreSQL server is running
check_postgresql_server() {
    print_info "Checking PostgreSQL server status..."
    
    if pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
        print_status "PostgreSQL server is running"
    else
        print_error "PostgreSQL server is not running or not accessible"
        print_info "Please start PostgreSQL server:"
        print_info "Ubuntu/Debian: sudo systemctl start postgresql"
        print_info "macOS: brew services start postgresql"
        print_info "Docker: docker run --name postgres -e POSTGRES_PASSWORD=$DB_PASSWORD -p 5432:5432 -d postgres:15"
        exit 1
    fi
}

# Create database if it doesn't exist
create_database() {
    print_info "Creating database '$DB_NAME'..."
    
    # Check if database exists
    if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        print_warning "Database '$DB_NAME' already exists"
    else
        # Create database
        createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
        print_status "Database '$DB_NAME' created successfully"
    fi
}

# Enable PostgreSQL extensions
enable_extensions() {
    print_info "Enabling PostgreSQL extensions..."
    
    # Extensions for full-text search and performance
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        CREATE EXTENSION IF NOT EXISTS btree_gin;
        CREATE EXTENSION IF NOT EXISTS uuid-ossp;
        CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    " &> /dev/null
    
    print_status "PostgreSQL extensions enabled"
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install asyncpg sqlalchemy[asyncio] alembic psycopg2-binary
        print_status "PostgreSQL Python dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Initialize Alembic migrations
initialize_alembic() {
    print_info "Initializing Alembic migrations..."
    
    if [ ! -d "alembic" ]; then
        print_error "Alembic directory not found. Please run this script from the backend directory."
        exit 1
    fi
    
    # Create initial migration
    python -m alembic revision --autogenerate -m "Initial PostgreSQL schema"
    print_status "Initial migration created"
}

# Run database migrations
run_migrations() {
    print_info "Running database migrations..."
    
    # Apply migrations
    python -m alembic upgrade head
    print_status "Database migrations completed"
}

# Backup existing JSON data
backup_json_data() {
    print_info "Creating backup of existing JSON data..."
    
    # Create backup directory
    mkdir -p $BACKUP_DIR
    
    # Backup data files with timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    if [ -d "../data" ]; then
        cp -r ../data "$BACKUP_DIR/json_backup_$TIMESTAMP"
        print_status "JSON data backed up to $BACKUP_DIR/json_backup_$TIMESTAMP"
    else
        print_warning "No ../data directory found to backup"
    fi
}

# Run data migration
migrate_data() {
    print_info "Starting data migration from JSON to PostgreSQL..."
    
    # Set environment variables
    export DATABASE_URL="postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    
    # Run migration script
    python scripts/migrate_to_postgresql.py
    
    if [ $? -eq 0 ]; then
        print_status "Data migration completed successfully"
    else
        print_error "Data migration failed. Check migration.log for details."
        exit 1
    fi
}

# Verify migration
verify_migration() {
    print_info "Verifying migration results..."
    
    # Count records in database
    USERS_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM users;" | xargs)
    ENTRIES_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM journal_entries;" | xargs)
    SESSIONS_COUNT=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM chat_sessions;" | xargs)
    
    print_status "Migration verification:"
    echo "  Users: $USERS_COUNT"
    echo "  Journal Entries: $ENTRIES_COUNT"
    echo "  Chat Sessions: $SESSIONS_COUNT"
}

# Create database performance monitoring
setup_monitoring() {
    print_info "Setting up database performance monitoring..."
    
    # Create monitoring queries
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        -- Enable query statistics
        SELECT pg_stat_reset();
        
        -- Create performance monitoring view
        CREATE OR REPLACE VIEW query_performance AS
        SELECT 
            query,
            calls,
            total_exec_time,
            mean_exec_time,
            max_exec_time,
            stddev_exec_time
        FROM pg_stat_statements 
        WHERE calls > 0
        ORDER BY mean_exec_time DESC;
    " &> /dev/null
    
    print_status "Performance monitoring configured"
}

# Main execution
main() {
    echo -e "${BLUE}Starting PostgreSQL setup process...${NC}\n"
    
    # Pre-flight checks
    check_postgresql
    check_postgresql_server
    
    # Database setup
    create_database
    enable_extensions
    
    # Python environment
    install_dependencies
    
    # Schema migration
    initialize_alembic
    run_migrations
    
    # Data migration
    backup_json_data
    migrate_data
    verify_migration
    
    # Performance setup
    setup_monitoring
    
    echo -e "\n${GREEN}🎉 PostgreSQL setup completed successfully!${NC}"
    echo -e "${BLUE}Database Details:${NC}"
    echo -e "  Host: $DB_HOST:$DB_PORT"
    echo -e "  Database: $DB_NAME"
    echo -e "  User: $DB_USER"
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo -e "  1. Update your .env file with DATABASE_URL"
    echo -e "  2. Start your application with PostgreSQL support"
    echo -e "  3. Monitor performance with: psql -c 'SELECT * FROM query_performance;'"
    echo -e "\n${YELLOW}Performance Target: <50ms query response times${NC}"
}

# Handle script arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "migrate-only")
        print_info "Running data migration only..."
        migrate_data
        verify_migration
        ;;
    "backup")
        print_info "Creating backup only..."
        backup_json_data
        ;;
    "verify")
        print_info "Verifying migration only..."
        verify_migration
        ;;
    "help")
        echo -e "${BLUE}PostgreSQL Setup Script Usage:${NC}"
        echo -e "  ./setup_postgresql.sh setup      - Full setup and migration"
        echo -e "  ./setup_postgresql.sh migrate-only - Run data migration only"
        echo -e "  ./setup_postgresql.sh backup     - Create JSON backup only"
        echo -e "  ./setup_postgresql.sh verify     - Verify migration results"
        echo -e "  ./setup_postgresql.sh help       - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        echo -e "Use './setup_postgresql.sh help' for usage information"
        exit 1
        ;;
esac
