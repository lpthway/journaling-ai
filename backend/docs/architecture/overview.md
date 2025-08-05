# Architecture Overview

## High-Level System Design

### System Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Applications                          │
├─────────────────────────────────────────────────────────────────────┤
│                          Load Balancer                              │
├─────────────────────────────────────────────────────────────────────┤
│                        FastAPI Application                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   API       │  │   Auth      │  │  Monitoring │  │   Health    │  │
│  │  Routes     │  │ Middleware  │  │   System    │  │   Checks    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Business   │  │    AI/ML    │  │   Cache     │  │  Background │  │
│  │  Services   │  │  Services   │  │  Services   │  │    Tasks    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Repositories│  │  Database   │  │   Vector    │  │ Performance │  │
│  │    Layer    │  │  Adapters   │  │   Store     │  │  Monitors   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                          Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ PostgreSQL  │  │    Redis    │  │  AI Models  │  │   Vector    │  │
│  │ Database    │  │   Cache     │  │  Storage    │  │  Database   │  │
│  │   408MB     │  │             │  │   4.2GB     │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Architectural Principles

1. **Layered Architecture**: Clear separation of concerns
   - **Presentation Layer**: FastAPI routes and middleware
   - **Business Logic Layer**: Services and domain logic
   - **Data Access Layer**: Repositories and database adapters
   - **Infrastructure Layer**: External services and utilities

2. **Async-First Design**: Built for high concurrency
   - Async/await patterns throughout the application
   - Non-blocking database operations
   - Concurrent AI model processing
   - Streaming response capabilities

3. **Microservice-Ready**: Modular design for future scaling
   - Service interfaces for easy extraction
   - Database per service pattern ready
   - API versioning support
   - Independent deployability

4. **Enterprise Patterns**: Production-ready patterns
   - Repository pattern for data access
   - Service layer for business logic
   - Dependency injection for testing
   - Observer pattern for monitoring

## Technology Stack Rationale

### Backend Framework: FastAPI
**Why FastAPI over Django/Flask?**
- **Performance**: 3-5x faster than Django for API workloads
- **Async Native**: Built-in async support for I/O operations
- **Type Safety**: Pydantic integration for request/response validation
- **Documentation**: Automatic OpenAPI/Swagger generation
- **Modern Python**: Takes advantage of Python 3.6+ features

### Database: PostgreSQL
**Why PostgreSQL over MySQL/MongoDB?**
- **JSON Support**: JSONB for flexible document storage
- **Full-Text Search**: Built-in trigram similarity search
- **ACID Compliance**: Strong consistency for financial/health data
- **Extensions**: Rich ecosystem (pg_trgm, btree_gin, etc.)
- **Vector Support**: Future pgvector integration planned

### Caching: Redis
**Why Redis over Memcached/In-Memory?**
- **Data Structures**: Lists, sets, hashes for complex caching
- **Persistence**: Optional data persistence for session storage
- **Pub/Sub**: Real-time notification capabilities
- **Clustering**: Horizontal scaling support
- **Performance**: Sub-millisecond latency for cache operations

### ORM: SQLAlchemy 2.0
**Why SQLAlchemy over Django ORM/Raw SQL?**
- **Async Support**: Native async/await patterns
- **Performance**: Lazy loading and query optimization
- **Type Safety**: Full type hint support
- **Migrations**: Alembic integration for schema changes
- **Flexibility**: Raw SQL when needed, ORM for productivity

## Scalability Design

### Horizontal Scaling Strategy
```
┌─────────────────────────────────────────────────────────────────────┐
│                         Load Balancer (nginx)                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   FastAPI   │  │   FastAPI   │  │   FastAPI   │  │   FastAPI   │  │
│  │ Instance 1  │  │ Instance 2  │  │ Instance 3  │  │ Instance N  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                          Shared Services                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ PostgreSQL  │  │    Redis    │  │  AI Model   │  │   Vector    │  │
│  │  Cluster    │  │  Cluster    │  │   Server    │  │   Store     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Performance Targets
- **Concurrent Users**: 1000+ simultaneous connections
- **Response Time**: <200ms for 95% of requests
- **Throughput**: 5000+ requests per second
- **Availability**: 99.9% uptime (8.76 hours downtime/year)
- **Data Growth**: Support for 100GB+ application data

### Bottleneck Identification
1. **AI Model Loading**: 15-30 second startup time
   - **Solution**: Model caching and lazy loading
   - **Priority**: Medium (affects deployment time)

2. **Vector Similarity Search**: Memory usage scales with data
   - **Solution**: PostgreSQL pgvector extension
   - **Priority**: High (affects large users)

3. **Database Connections**: 20 connection limit
   - **Solution**: Connection pooling optimization
   - **Priority**: Medium (affects concurrent users)

## Security Architecture

### Authentication & Authorization Flow
```
1. Client Request → 2. JWT Validation → 3. User Context → 4. Resource Access
     ↓                      ↓                  ↓               ↓
   API Key           Token Decode        Permission      Database
  Validation        & Verification       Checking        Query
```

### Security Layers
1. **Transport Security**: HTTPS/TLS 1.2+ for all communications
2. **API Security**: JWT tokens with configurable expiration
3. **Database Security**: Parameterized queries, SQL injection prevention
4. **Input Validation**: Pydantic models for request validation
5. **Output Sanitization**: Response model validation
6. **Rate Limiting**: Configurable per-endpoint rate limits

### Data Protection
- **Encryption at Rest**: PostgreSQL TDE (Transparent Data Encryption)
- **Encryption in Transit**: TLS 1.2+ for all network communication
- **Data Anonymization**: Psychology analysis without PII storage
- **Audit Logging**: Comprehensive logging of data access
- **Backup Encryption**: Encrypted database backups

## Integration Architecture

### External Service Integration
```
┌─────────────────────────────────────────────────────────────────────┐
│                      Journaling AI Backend                          │
├─────────────────────────────────────────────────────────────────────┤
│  External APIs                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ HuggingFace │  │  OpenAI API │  │  Email/SMS  │  │  Analytics  │  │
│  │   Models    │  │ (Future)    │  │  Services   │  │  Services   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                                     │
│  Internal Services                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Frontend   │  │   Mobile    │  │  Admin      │  │  Monitoring │  │
│  │   React     │  │    App      │  │  Dashboard  │  │   Grafana   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### API Design Patterns
- **RESTful Design**: Standard HTTP methods and status codes
- **Resource-Based URLs**: `/api/v1/entries/{id}` pattern
- **Versioning**: URL-based versioning for backward compatibility
- **Content Negotiation**: JSON primary, with extension points
- **Error Handling**: Consistent error response format

### Event-Driven Architecture (Future)
```
Producer Services → Message Queue (Redis/RabbitMQ) → Consumer Services
     ↓                         ↓                           ↓
Entry Creation          Analytics Events              Insight Generation
User Actions           Notification Events           Email Processing
AI Analysis            Backup Events                 Report Generation
```

## Development Architecture

### Code Organization Philosophy
```
backend/
├── app/                    # Application core
│   ├── api/               # API layer (routes, validation)
│   ├── core/              # Core infrastructure (config, db, etc.)
│   ├── models/            # Data models (SQLAlchemy)
│   ├── services/          # Business logic layer
│   ├── repositories/      # Data access layer
│   └── decorators/        # Cross-cutting concerns
├── data/                  # Application data (408MB)
├── models/                # AI models (4.2GB)
├── docs/                  # Documentation
├── tests/                 # Test suites
└── scripts/               # Utility scripts
```

### Dependency Injection Pattern
```python
# Service Registry Pattern
class ServiceRegistry:
    def __init__(self):
        self.database_service = UnifiedDatabaseService()
        self.redis_service = RedisService()
        self.ai_service = SentimentService()
        self.vector_service = VectorService()

# Dependency Injection in Routes
@router.post("/entries/")
async def create_entry(
    entry: EntryCreate,
    db_service: UnifiedDatabaseService = Depends(get_database_service)
):
    return await db_service.create_entry(entry)
```

### Testing Architecture
```
tests/
├── unit/                  # Unit tests (isolated components)
├── integration/           # Integration tests (service interactions)
├── api/                   # API endpoint tests
├── load/                  # Performance/load tests
├── fixtures/              # Test data and mocks
└── conftest.py           # Pytest configuration
```

## Performance Architecture

### Caching Strategy
```
┌─────────────────────────────────────────────────────────────────────┐
│                         Caching Layers                              │
├─────────────────────────────────────────────────────────────────────┤
│  L1: Application Cache (In-Memory)                                  │
│  ├── AI Model Cache: Loaded models in memory                       │
│  ├── Config Cache: Environment variables and settings              │
│  └── Session Cache: Active user sessions                           │
├─────────────────────────────────────────────────────────────────────┤
│  L2: Redis Cache (Distributed)                                     │
│  ├── API Response Cache: TTL-based response caching                │
│  ├── Database Query Cache: Expensive query results                 │
│  ├── User Session Store: JWT refresh tokens                        │
│  └── Analytics Cache: Pre-computed insights                        │
├─────────────────────────────────────────────────────────────────────┤
│  L3: Database Query Optimization                                   │
│  ├── Connection Pooling: Reuse database connections                │
│  ├── Query Optimization: Indexed queries and query plans          │
│  ├── Materialized Views: Pre-computed complex queries             │
│  └── Lazy Loading: Load data only when needed                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Monitoring & Observability
```
Application Metrics → Prometheus → Grafana Dashboards
       ↓                 ↓              ↓
  - Request/Response  - Time Series   - Visual
  - Error Rates       - Storage       - Dashboards
  - Performance       - Alerting      - Alerts
  - Resource Usage    - Retention     - Reports
```

### Database Performance
- **Connection Pool**: 20 connections with overflow handling
- **Query Optimization**: EXPLAIN ANALYZE for complex queries
- **Indexing Strategy**: GiST indexes for text search, B-tree for lookups
- **Partitioning**: Date-based partitioning for large tables (future)

## Future Architecture Considerations

### Microservice Migration Path
1. **Phase 1**: Extract AI services to separate containers
2. **Phase 2**: Separate user management and authentication
3. **Phase 3**: Break apart data services by domain
4. **Phase 4**: Event-driven communication between services

### Cloud-Native Readiness
- **Container Support**: Docker containerization completed
- **Kubernetes Ready**: Health checks and graceful shutdown
- **12-Factor App**: Environment-based configuration
- **Stateless Design**: Session data in Redis, not application memory

### AI/ML Pipeline Evolution
```
Current: Embedded Models → Future: Model Serving Infrastructure
     ↓                            ↓
- Local model loading     - Dedicated model servers
- In-process inference    - gRPC/REST model APIs  
- Memory constraints      - Horizontal model scaling
- Deployment coupling     - Independent model deployment
```

---

**Document Version**: 1.0  
**Last Updated**: August 5, 2025  
**Review Date**: September 5, 2025  
**Owner**: Backend Architecture Team
