# Database Architecture

## Overview

The Journaling AI backend uses a multi-layer data architecture combining relational (PostgreSQL), cache (Redis), and vector storage for optimal performance and scalability.

## PostgreSQL Primary Database

### Schema Design

#### Core Tables Structure
```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    profile JSONB
);

-- Journal Entries (Core Entity)
CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    content TEXT NOT NULL,
    entry_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    mood_score DECIMAL(3,2) CHECK (mood_score >= -1 AND mood_score <= 1),
    word_count INTEGER GENERATED ALWAYS AS (
        array_length(string_to_array(trim(content), ' '), 1)
    ) STORED,
    content_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(title, '') || ' ' || content)
    ) STORED
);

-- Sentiment Analysis Results
CREATE TABLE sentiment_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id UUID REFERENCES journal_entries(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    sentiment_label VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    emotions JSONB, -- {"joy": 0.8, "sadness": 0.2, ...}
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(entry_id, model_name)
);

-- Topics and Themes
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_system_topic BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, name)
);

-- Entry-Topic Relationships (Many-to-Many)
CREATE TABLE entry_topics (
    entry_id UUID REFERENCES journal_entries(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2) DEFAULT 1.0,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (entry_id, topic_id)
);

-- User Sessions and Activity
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    activities JSONB, -- {"pages_visited": [], "time_spent": 1200}
    ip_address INET,
    user_agent TEXT
);

-- Psychology Insights
CREATE TABLE psychology_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL,
    insight_data JSONB NOT NULL,
    confidence_level DECIMAL(3,2),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

### Indexing Strategy

#### Performance Indexes
```sql
-- Primary Performance Indexes
CREATE INDEX idx_journal_entries_user_date ON journal_entries(user_id, entry_date DESC);
CREATE INDEX idx_journal_entries_created ON journal_entries(created_at DESC);
CREATE INDEX idx_sentiment_analysis_entry ON sentiment_analysis(entry_id);

-- Full-Text Search Indexes
CREATE INDEX idx_journal_entries_content_gin ON journal_entries USING GIN(content_vector);
CREATE INDEX idx_journal_entries_title_gin ON journal_entries USING GIN(to_tsvector('english', title));

-- Trigram Similarity Indexes (for fuzzy search)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_journal_entries_content_trgm ON journal_entries USING GIN(content gin_trgm_ops);
CREATE INDEX idx_topics_name_trgm ON topics USING GIN(name gin_trgm_ops);

-- JSONB Indexes for Psychology Data
CREATE INDEX idx_sentiment_emotions_gin ON sentiment_analysis USING GIN(emotions);
CREATE INDEX idx_psychology_insights_data ON psychology_insights USING GIN(insight_data);
CREATE INDEX idx_users_profile_gin ON users USING GIN(profile);

-- Composite Indexes for Common Queries
CREATE INDEX idx_entry_topics_composite ON entry_topics(topic_id, relevance_score DESC);
CREATE INDEX idx_user_sessions_active ON user_sessions(user_id, session_start DESC) 
    WHERE session_end IS NULL;
```

### Advanced Features

#### Full-Text Search Implementation
```sql
-- Weighted Full-Text Search
SELECT 
    e.id,
    e.title,
    ts_rank_cd(
        setweight(to_tsvector('english', coalesce(e.title, '')), 'A') ||
        setweight(to_tsvector('english', e.content), 'B'),
        plainto_tsquery('english', $1)
    ) AS rank,
    ts_headline(
        'english', 
        e.content, 
        plainto_tsquery('english', $1),
        'MaxWords=35, MinWords=15, MaxFragments=3'
    ) AS snippet
FROM journal_entries e
WHERE (
    setweight(to_tsvector('english', coalesce(e.title, '')), 'A') ||
    setweight(to_tsvector('english', e.content), 'B')
) @@ plainto_tsquery('english', $1)
AND e.user_id = $2
ORDER BY rank DESC
LIMIT 20;
```

#### Similarity Search with Trigrams
```sql
-- Fuzzy Topic Matching
SELECT 
    t.name,
    similarity(t.name, $1) as sim_score
FROM topics t
WHERE t.name % $1  -- Trigram similarity operator
   OR similarity(t.name, $1) > 0.3
ORDER BY sim_score DESC
LIMIT 10;
```

#### Time-Series Analytics
```sql
-- Mood Trends Over Time
SELECT 
    date_trunc('week', e.entry_date) as week,
    AVG(e.mood_score) as avg_mood,
    COUNT(*) as entry_count,
    STDDEV(e.mood_score) as mood_variance
FROM journal_entries e
WHERE e.user_id = $1
  AND e.entry_date >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY week
ORDER BY week;
```

### Data Integrity & Constraints

#### Business Logic Constraints
```sql
-- Ensure mood scores are within valid range
ALTER TABLE journal_entries 
ADD CONSTRAINT check_mood_range 
CHECK (mood_score >= -1 AND mood_score <= 1);

-- Ensure confidence scores are percentages
ALTER TABLE sentiment_analysis 
ADD CONSTRAINT check_confidence_range 
CHECK (confidence_score >= 0 AND confidence_score <= 1);

-- Prevent empty content
ALTER TABLE journal_entries 
ADD CONSTRAINT check_content_not_empty 
CHECK (trim(content) != '');

-- Ensure session logic
ALTER TABLE user_sessions 
ADD CONSTRAINT check_session_duration 
CHECK (session_end IS NULL OR session_end >= session_start);
```

#### Cascading Rules
```sql
-- User deletion cascades appropriately
-- journal_entries: CASCADE (delete user's entries)
-- topics: CASCADE (delete user's custom topics)
-- sentiment_analysis: CASCADE via journal_entries
-- psychology_insights: CASCADE (delete user's insights)
-- user_sessions: CASCADE (delete user's sessions)
```

## Redis Caching Layer

### Cache Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                         Redis Cache Structure                       │
├─────────────────────────────────────────────────────────────────────┤
│  Namespace: auth:*                                                  │
│  ├── auth:sessions:{user_id} → JWT session data (TTL: 7 days)      │
│  ├── auth:refresh:{token_hash} → Refresh token (TTL: 30 days)      │
│  └── auth:rate_limit:{ip} → Rate limiting counters (TTL: 1 hour)   │
├─────────────────────────────────────────────────────────────────────┤
│  Namespace: api:*                                                   │
│  ├── api:response:{route_hash} → Cached API responses (TTL: 5 min)  │
│  ├── api:user_data:{user_id} → User profile cache (TTL: 1 hour)    │
│  └── api:analytics:{user_id} → Pre-computed insights (TTL: 6 hours) │
├─────────────────────────────────────────────────────────────────────┤
│  Namespace: models:*                                                │
│  ├── models:embeddings:{text_hash} → Vector embeddings (TTL: 1 day) │
│  ├── models:sentiment:{text_hash} → Sentiment results (TTL: 1 day)  │
│  └── models:topics:{user_id} → Topic suggestions (TTL: 2 hours)    │
├─────────────────────────────────────────────────────────────────────┤
│  Namespace: tasks:*                                                 │
│  ├── tasks:queue:ai_analysis → Background AI processing queue      │
│  ├── tasks:status:{task_id} → Task status tracking (TTL: 1 hour)   │
│  └── tasks:results:{task_id} → Task results cache (TTL: 1 day)     │
└─────────────────────────────────────────────────────────────────────┘
```

### Caching Patterns

#### Cache-Aside Pattern (Manual)
```python
async def get_user_analytics(user_id: str) -> Dict:
    # Try cache first
    cache_key = f"api:analytics:{user_id}"
    cached_data = await redis.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Cache miss - compute and store
    analytics = await compute_user_analytics(user_id)
    await redis.setex(
        cache_key, 
        timedelta(hours=6).total_seconds(),
        json.dumps(analytics)
    )
    return analytics
```

#### Write-Through Pattern (Automatic)
```python
async def update_user_profile(user_id: str, profile_data: Dict):
    # Update database
    await db.update_user_profile(user_id, profile_data)
    
    # Update cache immediately
    cache_key = f"api:user_data:{user_id}"
    await redis.setex(
        cache_key,
        timedelta(hours=1).total_seconds(),
        json.dumps(profile_data)
    )
```

#### Cache Invalidation Strategy
```python
# Pattern-based invalidation
async def invalidate_user_cache(user_id: str):
    patterns = [
        f"api:user_data:{user_id}",
        f"api:analytics:{user_id}",
        f"models:topics:{user_id}"
    ]
    
    for pattern in patterns:
        await redis.delete(pattern)
```

### Redis Configuration

#### Performance Settings
```redis
# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used keys

# Persistence settings (for session data)
save 900 1    # Save if at least 1 key changed in 900 seconds
save 300 10   # Save if at least 10 keys changed in 300 seconds
save 60 10000 # Save if at least 10000 keys changed in 60 seconds

# Networking
tcp-keepalive 300
timeout 0

# Logging
loglevel notice
logfile "/var/log/redis/redis-server.log"
```

## Vector Storage (ChromaDB)

### Vector Database Structure
```
chroma_db/
├── collections/
│   ├── user_embeddings/     # User-specific document embeddings
│   ├── topic_embeddings/    # Topic and theme vectors  
│   ├── insight_embeddings/  # Psychology insight vectors
│   └── global_embeddings/   # Cross-user pattern vectors
├── indexes/
│   ├── faiss_indexes/       # FAISS indexes for fast similarity
│   └── metadata_indexes/    # Metadata filtering indexes
└── config/
    ├── collection_config.json
    └── model_config.json
```

### Embedding Strategy

#### Text Embedding Pipeline
```python
class EmbeddingService:
    def __init__(self):
        # Sentence transformers for semantic similarity
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.mpnet_model = SentenceTransformer('all-mpnet-base-v2')
    
    async def embed_journal_entry(self, entry: str) -> List[float]:
        # Combine title and content for richer embeddings
        full_text = f"{entry.title}\n\n{entry.content}"
        
        # Use higher quality model for journal entries
        embedding = self.mpnet_model.encode(
            full_text,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding.tolist()
    
    async def embed_topic(self, topic_name: str, description: str = "") -> List[float]:
        topic_text = f"{topic_name} {description}".strip()
        
        # Use lighter model for topics
        embedding = self.sentence_model.encode(
            topic_text,
            normalize_embeddings=True
        )
        return embedding.tolist()
```

#### Similarity Search Implementation
```python
async def find_similar_entries(
    query_text: str, 
    user_id: str, 
    limit: int = 10,
    similarity_threshold: float = 0.7
) -> List[Dict]:
    # Get query embedding
    query_embedding = await embedding_service.embed_text(query_text)
    
    # Search in user's collection
    results = chroma_client.query(
        collection_name=f"user_{user_id}_entries",
        query_embeddings=[query_embedding],
        n_results=limit,
        where={"user_id": user_id},
        include=["metadatas", "documents", "distances"]
    )
    
    # Filter by similarity threshold
    filtered_results = [
        {
            "entry_id": result["id"],
            "content": result["document"],
            "similarity": 1 - result["distance"],  # Convert distance to similarity
            "metadata": result["metadata"]
        }
        for result in results["documents"][0]
        if (1 - result["distance"]) >= similarity_threshold
    ]
    
    return filtered_results
```

## Database Operations

### Connection Management

#### SQLAlchemy Configuration
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Database configuration
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/journaling_ai"

# Engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging in development
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections every 30 minutes
    connect_args={
        "server_settings": {
            "application_name": "journaling_ai_backend",
            "jit": "off"  # Disable JIT for consistent performance
        }
    }
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

#### Connection Pool Monitoring
```python
async def get_connection_pool_status():
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.checkedin() + pool.checkedout()
    }
```

### Transaction Management

#### Repository Pattern with Transactions
```python
class DatabaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_entry_with_analysis(
        self, 
        entry_data: Dict, 
        sentiment_data: Dict
    ) -> JournalEntry:
        try:
            # Start transaction (implicit with session)
            entry = JournalEntry(**entry_data)
            self.session.add(entry)
            await self.session.flush()  # Get entry.id without committing
            
            # Create related sentiment analysis
            sentiment = SentimentAnalysis(
                entry_id=entry.id,
                **sentiment_data
            )
            self.session.add(sentiment)
            
            # Commit transaction
            await self.session.commit()
            await self.session.refresh(entry)
            
            return entry
            
        except Exception as e:
            await self.session.rollback()
            raise e
```

#### Bulk Operations
```python
async def bulk_insert_sentiments(sentiment_records: List[Dict]):
    """Efficiently insert multiple sentiment records"""
    async with AsyncSessionLocal() as session:
        # Use bulk insert for better performance
        await session.execute(
            insert(SentimentAnalysis),
            sentiment_records
        )
        await session.commit()

async def bulk_update_mood_scores(mood_updates: List[Dict]):
    """Bulk update mood scores with optimistic locking"""
    async with AsyncSessionLocal() as session:
        stmt = (
            update(JournalEntry)
            .where(JournalEntry.id == bindparam('entry_id'))
            .values(
                mood_score=bindparam('mood_score'),
                updated_at=func.now()
            )
        )
        await session.execute(stmt, mood_updates)
        await session.commit()
```

## Performance Optimization

### Query Optimization

#### Efficient Pagination
```sql
-- Cursor-based pagination (better than OFFSET for large datasets)
SELECT id, title, content, created_at
FROM journal_entries
WHERE user_id = $1
  AND created_at < $2  -- cursor from previous page
ORDER BY created_at DESC
LIMIT 20;
```

#### Materialized Views for Analytics
```sql
-- Pre-computed user statistics
CREATE MATERIALIZED VIEW user_statistics AS
SELECT 
    user_id,
    COUNT(*) as total_entries,
    AVG(mood_score) as avg_mood,
    MIN(entry_date) as first_entry_date,
    MAX(entry_date) as last_entry_date,
    COUNT(DISTINCT date_trunc('month', entry_date)) as active_months
FROM journal_entries
GROUP BY user_id;

-- Refresh strategy (daily)
CREATE OR REPLACE FUNCTION refresh_user_statistics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_statistics;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh
SELECT cron.schedule('refresh-stats', '0 2 * * *', 'SELECT refresh_user_statistics();');
```

### Monitoring Queries

#### Slow Query Detection
```sql
-- Enable query logging (postgresql.conf)
log_min_duration_statement = 1000  -- Log queries taking > 1 second
log_statement_stats = on
log_lock_waits = on

-- Query to find slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;
```

#### Index Usage Analysis
```sql
-- Find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_tup_read = 0
ORDER BY schemaname, tablename, indexname;

-- Find missing indexes (tables with high sequential scans)
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    seq_tup_read / seq_scan as avg_rows_per_scan
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;
```

## Backup and Recovery

### Backup Strategy

#### Automated Backup Script
```bash
#!/bin/bash
# /scripts/backup_database.sh

DB_NAME="journaling_ai"
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create compressed backup
pg_dump \
    --host=localhost \
    --port=5432 \
    --username=journaling_user \
    --dbname=$DB_NAME \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="${BACKUP_FILE%.gz}" \
    && gzip "${BACKUP_FILE%.gz}"

# Upload to cloud storage (optional)
aws s3 cp $BACKUP_FILE s3://journaling-ai-backups/postgresql/

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

#### Point-in-Time Recovery Setup
```postgresql
-- Enable WAL archiving (postgresql.conf)
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/postgresql/wal/%f'
max_wal_senders = 3
```

### Data Migration Scripts

#### Schema Migration Template
```python
"""Add psychology insights table

Revision ID: 001_psychology_insights
Revises: 000_initial_schema
Create Date: 2025-08-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_psychology_insights'
down_revision = '000_initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'psychology_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('insight_type', sa.VARCHAR(length=100), nullable=False),
        sa.Column('insight_data', postgresql.JSONB(), nullable=False),
        sa.Column('confidence_level', sa.DECIMAL(precision=3, scale=2)),
        sa.Column('generated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('is_active', sa.BOOLEAN(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(
        'idx_psychology_insights_user', 
        'psychology_insights', 
        ['user_id']
    )
    op.create_index(
        'idx_psychology_insights_type', 
        'psychology_insights', 
        ['insight_type']
    )

def downgrade():
    op.drop_table('psychology_insights')
```

---

**Document Version**: 1.0  
**Last Updated**: August 5, 2025  
**Review Date**: September 5, 2025  
**Owner**: Database Architecture Team
