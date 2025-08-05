# Installation Guide

## Prerequisites

### System Requirements

#### Minimum Requirements
- **OS**: Ubuntu 20.04 LTS, macOS 10.15+, or Windows 10/11 with WSL2
- **RAM**: 8GB (16GB recommended for AI model loading)
- **Storage**: 10GB free space (20GB recommended)
- **CPU**: 4 cores (8 cores recommended for AI processing)
- **Network**: Stable internet connection for model downloads

#### Recommended Development Setup
- **OS**: Ubuntu 22.04 LTS or macOS 12+
- **RAM**: 16GB+ (for comfortable AI model loading)
- **Storage**: 25GB+ SSD storage
- **CPU**: 8+ cores with virtualization support
- **Network**: High-speed internet for initial model downloads

### Required Software

#### Core Dependencies
```bash
# Python 3.11+ (Required)
python3 --version  # Should be 3.11.0 or higher

# PostgreSQL 14+ (Required)
postgres --version  # Should be 14.0 or higher

# Redis 6+ (Required)
redis-server --version  # Should be 6.0 or higher

# Git (Required)
git --version  # Should be 2.25 or higher
```

#### Optional but Recommended
```bash
# Docker & Docker Compose (for containerized deployment)
docker --version
docker-compose --version

# Node.js 18+ (for frontend development)
node --version  # Should be 18.0 or higher

# Nginx (for production deployment)
nginx -v  # Should be 1.18 or higher
```

## Quick Start (5 Minutes)

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/your-org/journaling-ai.git
cd journaling-ai/backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Start PostgreSQL (varies by system)
sudo systemctl start postgresql  # Ubuntu/Debian
brew services start postgresql   # macOS
net start postgresql-x64-14     # Windows

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE journaling_ai;"
sudo -u postgres psql -c "CREATE USER journaling_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE journaling_ai TO journaling_user;"
```

### 3. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env  # Add your database credentials
```

### 4. Initialize and Run
```bash
# Run database migrations
alembic upgrade head

# Start Redis
redis-server &

# Start the application
python run.py
```

### 5. Verify Installation
```bash
# Test the API
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-08-05T10:00:00Z"}
```

## Detailed Installation

### Python Environment Setup

#### Using pyenv (Recommended)
```bash
# Install pyenv (if not already installed)
curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.9
pyenv global 3.11.9

# Verify Python version
python --version  # Should show: Python 3.11.9
```

#### Virtual Environment Management
```bash
# Create virtual environment
python -m venv journaling-ai-env

# Activate virtual environment
source journaling-ai-env/bin/activate  # Linux/macOS
# or
journaling-ai-env\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi  # Should show FastAPI and version
```

### PostgreSQL Setup

#### Ubuntu/Debian Installation
```bash
# Update package list
sudo apt update

# Install PostgreSQL and contrib packages
sudo apt install postgresql postgresql-contrib postgresql-client

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check service status
sudo systemctl status postgresql
```

#### macOS Installation
```bash
# Using Homebrew
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create initial database
createdb $(whoami)
```

#### Windows Installation
```powershell
# Download from: https://www.postgresql.org/download/windows/
# Follow installer instructions

# Verify installation
psql --version
```

#### Database Configuration
```bash
# Switch to postgres user
sudo -i -u postgres

# Access PostgreSQL prompt
psql

# Create database and user
CREATE DATABASE journaling_ai;
CREATE USER journaling_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE journaling_ai TO journaling_user;

# Grant additional permissions
GRANT USAGE ON SCHEMA public TO journaling_user;
GRANT CREATE ON SCHEMA public TO journaling_user;

# Exit PostgreSQL
\q
exit
```

#### Install Required Extensions
```sql
-- Connect to the journaling_ai database
\c journaling_ai

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Verify extensions
\dx
```

### Redis Setup

#### Ubuntu/Debian Installation
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis to start on boot
sudo systemctl enable redis-server

# Start Redis service
sudo systemctl start redis-server

# Test Redis connection
redis-cli ping  # Should return: PONG
```

#### macOS Installation
```bash
# Using Homebrew
brew install redis

# Start Redis service
brew services start redis

# Test connection
redis-cli ping  # Should return: PONG
```

#### Redis Configuration
```bash
# Edit Redis configuration (optional)
sudo nano /etc/redis/redis.conf

# Key settings to review:
# maxmemory 2gb
# maxmemory-policy allkeys-lru
# save 900 1
# appendonly yes
```

### Environment Configuration

#### Environment Variables Setup
```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file
nano .env
```

#### Complete .env Configuration
```bash
# Database Configuration
DATABASE_URL=postgresql://journaling_user:your_secure_password@localhost/journaling_ai
DB_HOST=localhost
DB_PORT=5432
DB_NAME=journaling_ai
DB_USER=journaling_user
DB_PASSWORD=your_secure_password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Leave empty for local development

# Application Configuration
SECRET_KEY=your-super-secret-key-here-change-this-in-production
API_V1_STR=/api/v1
PROJECT_NAME=Journaling AI Backend
DEBUG=True
ENVIRONMENT=development

# Security Settings
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
ALGORITHM=HS256

# AI Model Configuration
MODELS_PATH=./models
HUGGINGFACE_CACHE_DIR=./models
SENTENCE_TRANSFORMERS_HOME=./models

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# CORS Settings (for frontend development)
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
ALLOWED_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
ALLOWED_HEADERS=["*"]

# File Upload Settings
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
UPLOAD_PATH=./uploads

# Performance Settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
REDIS_CONNECTION_POOL_SIZE=10
```

### Database Migration

#### Initialize Alembic (First Time Only)
```bash
# If alembic.ini doesn't exist, initialize it
alembic init alembic

# Edit alembic.ini database URL
nano alembic.ini
# Set: sqlalchemy.url = postgresql://journaling_user:password@localhost/journaling_ai
```

#### Run Migrations
```bash
# Check current migration status
alembic current

# Run all pending migrations
alembic upgrade head

# Verify database tables were created
psql -U journaling_user -d journaling_ai -c "\dt"
```

#### Create Initial Data (Optional)
```bash
# Run the data initialization script
python scripts/init_data.py

# Or manually create an admin user
python -c "
from app.core.security import get_password_hash
print('Hashed password:', get_password_hash('admin123'))
"
```

### AI Models Setup

#### Automatic Model Download
```bash
# Start the application - models will download automatically
python run.py

# Monitor download progress in logs
tail -f logs/app.log
```

#### Manual Model Download (Optional)
```python
# Run this Python script to pre-download models
from sentence_transformers import SentenceTransformer
from transformers import pipeline

# Download sentence transformers
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

# Download sentiment analysis models
pipeline('sentiment-analysis', model='cardiffnlp/twitter-roberta-base-sentiment-latest')
pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base')

print("All models downloaded successfully!")
```

#### Verify Model Loading
```bash
# Test model loading endpoint
curl http://localhost:8000/api/v1/models/status

# Expected response:
# {
#   "models_loaded": 8,
#   "models": ["sentiment-analysis", "emotion-analysis", ...],
#   "status": "ready"
# }
```

## Docker Setup (Alternative)

### Docker Compose Installation
```bash
# Clone repository
git clone https://github.com/your-org/journaling-ai.git
cd journaling-ai

# Copy environment file
cp .env.example .env
# Edit .env with your preferences

# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Check service status
docker-compose ps
```

### Docker Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://journaling_user:password@postgres:5432/journaling_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend/models:/app/models
      - ./backend/data:/app/data

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: journaling_ai
      POSTGRES_USER: journaling_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Verification and Testing

### Health Check
```bash
# Test API health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-08-05T10:00:00Z",
  "version": "2.1.0",
  "database": "connected",
  "redis": "connected",
  "models": "loaded"
}
```

### Database Connection Test
```bash
# Test database connection
python -c "
import asyncio
from app.core.database import get_database_service

async def test():
    db = get_database_service()
    result = await db.test_connection()
    print('Database connection:', result)

asyncio.run(test())
"
```

### API Endpoints Test
```bash
# Test API documentation
curl http://localhost:8000/docs

# Test authentication endpoint
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Test journal entry creation
curl -X POST http://localhost:8000/api/v1/entries/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"title":"Test Entry","content":"This is a test journal entry"}'
```

### Performance Test
```bash
# Install wrk (load testing tool)
# Ubuntu: sudo apt install wrk
# macOS: brew install wrk

# Run basic load test
wrk -t12 -c400 -d30s http://localhost:8000/health

# Expected output should show reasonable latency and no errors
```

## Troubleshooting

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If version is too old, use pyenv or update system Python
# Ubuntu:
sudo apt update && sudo apt install python3.11 python3.11-venv

# macOS:
brew install python@3.11
```

#### Database Connection Issues
```bash
# Check PostgreSQL service status
sudo systemctl status postgresql

# Check if database exists
psql -U journaling_user -d journaling_ai -c "SELECT version();"

# Reset database if needed
dropdb journaling_ai
createdb journaling_ai
alembic upgrade head
```

#### Redis Connection Issues
```bash
# Check Redis service status
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

#### Model Download Issues
```bash
# Check available disk space
df -h

# Check internet connectivity
curl -I https://huggingface.co

# Clear model cache if corrupted
rm -rf ./models/*
python run.py  # Will re-download models
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x run.py
chown -R $USER:$USER ./models ./data

# Fix PostgreSQL permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE journaling_ai TO journaling_user;"
```

### Performance Issues

#### Slow Startup
```bash
# Monitor startup process
python run.py --log-level DEBUG

# Check model loading time
tail -f logs/app.log | grep "Loading model"

# Consider pre-downloading models
python scripts/download_models.py
```

#### Memory Issues
```bash
# Check memory usage
free -h
htop

# Reduce model memory usage (in .env)
MODELS_DEVICE=cpu  # Use CPU instead of GPU
MAX_CONCURRENT_REQUESTS=5  # Reduce concurrent processing
```

### Development Issues

#### IDE Configuration
```bash
# VS Code Python path configuration
# Create .vscode/settings.json:
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black"
}
```

#### Hot Reload Issues
```bash
# Use uvicorn directly for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with specific Python path
python -m uvicorn app.main:app --reload
```

## Next Steps

### Development Setup
1. **IDE Configuration**: Set up your IDE with Python debugging
2. **Pre-commit Hooks**: Install code quality tools
3. **Testing**: Run the test suite to ensure everything works
4. **Documentation**: Read the API documentation at `/docs`

### Production Deployment
1. **Security Review**: Update all default passwords and secrets
2. **SSL Certificates**: Configure HTTPS with proper certificates
3. **Monitoring**: Set up application and infrastructure monitoring
4. **Backups**: Configure automated database backups

### Useful Commands Reference
```bash
# Development
python run.py                    # Start development server
alembic upgrade head            # Apply database migrations
pytest                         # Run test suite
black .                        # Format code
flake8 .                       # Lint code

# Database
psql -U journaling_user -d journaling_ai  # Connect to database
alembic revision --autogenerate -m "description"  # Create migration
pg_dump journaling_ai > backup.sql              # Backup database

# Docker
docker-compose up              # Start all services
docker-compose logs backend    # View backend logs
docker-compose exec backend bash  # Access backend container
```

---

**Document Version**: 1.0  
**Last Updated**: August 5, 2025  
**Review Date**: September 5, 2025  
**Owner**: DevOps Team
