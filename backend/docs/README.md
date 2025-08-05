# Journaling AI Backend Documentation

## Project Overview

### Project Name
**Journaling AI Backend** - Enterprise-grade FastAPI application for AI-powered journaling and psychological analysis

### Purpose
A sophisticated backend system that provides:
- AI-powered journaling with sentiment analysis and emotional insights
- Psychology knowledge database for personalized mental health guidance
- Vector similarity search for intelligent content discovery
- Real-time analytics and performance monitoring
- Enterprise-grade caching and session management
- PostgreSQL database with advanced search capabilities

### Current Status
**✅ WORKING** - Production-ready with comprehensive testing
- PostgreSQL database fully operational (408MB active data)
- Redis caching system integrated
- AI models loaded and functional (4.2GB total)
- FastAPI application with async architecture
- Alembic migrations system configured

### Technology Stack
- **Framework**: FastAPI 0.104.1 with async/await patterns
- **Database**: PostgreSQL 14+ with asyncpg driver
- **ORM**: SQLAlchemy 2.0 with async support
- **Caching**: Redis with async connections
- **AI/ML**: Transformers, sentence-transformers, PyTorch
- **Migrations**: Alembic with PostgreSQL extensions
- **Server**: Uvicorn with auto-reload
- **Authentication**: JWT with bcrypt hashing
- **Monitoring**: Custom performance monitoring system

### Dependencies
External packages, APIs, and services required:
- **System Dependencies**: Python 3.9+, PostgreSQL 14+, Redis 6+
- **Python Packages**: 147 packages in requirements.txt
- **AI Models**: 8 pre-trained models (4.2GB total)
- **External APIs**: HuggingFace model downloads
- **Infrastructure**: 5GB+ disk space, 8GB+ RAM recommended

### Entry Points
- **Main Application**: `run.py` → `app.main:app`
- **Development Server**: `python run.py` (host=0.0.0.0:8000)
- **Production**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Database Migrations**: `alembic upgrade head`
- **Health Check**: `curl http://localhost:8000/health`

## Getting Started

### For New Developers
1. [Installation Guide](./setup/installation.md) - Complete setup from scratch
2. [Configuration](./setup/configuration.md) - Environment variables and settings
3. [Architecture Overview](./architecture/overview.md) - System design and components

### For Existing Team Members
- [Development Setup](./setup/development.md) - Quick development environment
- [Code Structure](./code/) - Module and component documentation
- [Testing Guidelines](./testing/) - How to write and run tests

### For Operations/DevOps
- [Deployment Guide](./setup/deployment.md) - Production deployment
- [Monitoring](./operations/monitoring.md) - Performance and health monitoring
- [Troubleshooting](./operations/troubleshooting.md) - Common issues and solutions

## Reference Documentation

### API Documentation
- [Endpoints](./api/endpoints.md) - All API routes and methods
- [Authentication](./api/authentication.md) - JWT auth flow
- [Examples](./api/examples.md) - Request/response samples

### Database Documentation
- [Schema](./database/schema.md) - Tables, relationships, indexes
- [Migrations](./database/migrations.md) - Migration history and notes
- [Queries](./database/queries.md) - Common SQL operations

### Code Documentation
- [Modules](./code/modules/) - Per-module detailed documentation
- [Functions](./code/functions.md) - Key functions and purposes
- [Classes](./code/classes.md) - Class documentation and relationships

### Operations Documentation
- [Monitoring](./operations/monitoring.md) - Logs, metrics, alerts
- [Backup & Recovery](./operations/backup.md) - Data backup procedures
- [Security](./operations/security.md) - Security practices and considerations

## Quick Reference

### Development Commands
```bash
# Start development server
python run.py

# Run tests
pytest

# Database migration
alembic upgrade head

# Clear Redis cache
redis-cli FLUSHALL
```

### Production Commands
```bash
# Start production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Check application health
curl http://localhost:8000/health

# Monitor logs
tail -f logs/journaling-ai.log
```

### Important File Locations
- **Configuration**: `app/core/config.py`
- **Database Models**: `app/models/enhanced_models.py`
- **API Routes**: `app/api/`
- **Business Logic**: `app/services/`
- **Data Access**: `app/repositories/`
- **AI Models**: `models/` (4.2GB)
- **Application Data**: `data/` (408MB)

## Recent Updates

See [CHANGELOG.md](../CHANGELOG.md) for complete history.

**Latest Changes (2025-08-05)**:
- Phase 2 cleanup: Archived 10 migration scripts
- Production-ready structure achieved
- Comprehensive documentation restructured

## Support and Contributing

### Getting Help
- **Documentation Issues**: Update relevant docs in `docs/` folder
- **Code Issues**: Check [troubleshooting guide](./operations/troubleshooting.md)
- **Performance Issues**: See [monitoring guide](./operations/monitoring.md)

### Contributing
- **Code Style**: Follow [development guidelines](./setup/development.md)
- **Testing**: See [testing strategy](./testing/strategy.md)
- **Documentation**: Update docs with any changes

---

**Documentation Version**: 2.1.0  
**Last Updated**: August 5, 2025  
**Next Review**: September 5, 2025
