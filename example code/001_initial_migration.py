# alembic/versions/001_initial_migration.py
"""
Initial database schema migration from JSON to PostgreSQL.

Features:
- Complete schema creation with proper constraints
- Advanced indexing strategy for performance
- Full-text search setup
- JSONB column optimization
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
import uuid

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create initial database schema with enterprise-grade features."""
    
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')  # For similarity search
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')  # For composite indexes
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=True, unique=True),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('language', sa.String(10), nullable=False, default='en'),
        sa.Column('preferences', JSONB, nullable=False, default={}),
        sa.Column('psychology_profile', JSONB, nullable=False, default={}),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Users indexes
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_active_created', 'users', ['is_active', 'created_at'])
    op.create_index('ix_users_preferences_gin', 'users', ['preferences'], postgresql_using='gin')
    
    # Topics table
    op.create_table(
        'topics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('color', sa.String(7), nullable=False, default='#3B82F6'),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('parent_id', UUID(as_uuid=True), nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, default=0),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('tags', JSONB, nullable=False, default=[]),
        sa.Column('psychology_domains', JSONB, nullable=False, default=[]),
        sa.Column('metadata', JSONB, nullable=False, default={}),
        sa.Column('entry_count', sa.Integer, nullable=False, default=0),
        sa.Column('last_entry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_statistics', JSONB, nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'name', 'parent_id', name='uq_topics_user_name_parent'),
        sa.CheckConstraint('entry_count >= 0', name='ck_topics_entry_count_positive'),
    )
    
    # Topics indexes
    op.create_index('ix_topics_user_name', 'topics', ['user_id', 'name'])
    op.create_index('ix_topics_parent_sort', 'topics', ['parent_id', 'sort_order'])
    op.create_index('ix_topics_psychology_gin', 'topics', ['psychology_domains'], postgresql_using='gin')
    
    # Entry templates table
    op.create_table(
        'entry_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('content_template', sa.Text, nullable=False),
        sa.Column('prompts', JSONB, nullable=False, default=[]),
        sa.Column('guided_questions', JSONB, nullable=False, default=[]),
        sa.Column('psychology_domains', JSONB, nullable=False, default=[]),
        sa.Column('therapeutic_techniques', JSONB, nullable=False, default=[]),
        sa.Column('tags', JSONB, nullable=False, default=[]),
        sa.Column('difficulty_level', sa.String(20), nullable=False, default='beginner'),
        sa.Column('estimated_time_minutes', sa.Integer, nullable=False, default=10),
        sa.Column('is_public', sa.Boolean, nullable=False, default=False),
        sa.Column('usage_count', sa.Integer, nullable=False, default=0),
        sa.Column('effectiveness_rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('created_by_user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.CheckConstraint('usage_count >= 0', name='ck_templates_usage_count_positive'),
        sa.CheckConstraint('estimated_time_minutes > 0', name='ck_templates_time_positive'),
    )
    
    # Entry templates indexes
    op.create_index('ix_templates_category_public', 'entry_templates', ['category', 'is_public'])
    op.create_index('ix_templates_psychology_gin', 'entry_templates', ['psychology_domains'], postgresql_using='gin')
    op.create_index('ix_templates_usage', 'entry_templates', ['usage_count', 'effectiveness_rating'])
    
    # Entries table (main journaling table)
    op.create_table(
        'entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('entry_type', sa.String(50), nullable=False, default='journal'),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('topic_id', UUID(as_uuid=True), nullable=True),
        sa.Column('word_count', sa.Integer, nullable=False, default=0),
        sa.Column('reading_time_minutes', sa.Integer, nullable=False, default=1),
        sa.Column('mood', sa.String(50), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('emotion_analysis', JSONB, nullable=False, default={}),
        sa.Column('tags', JSONB, nullable=False, default=[]),
        sa.Column('auto_tags', JSONB, nullable=False, default=[]),
        sa.Column('psychology_tags', JSONB, nullable=False, default=[]),
        sa.Column('is_favorite', sa.Boolean, nullable=False, default=False),
        sa.Column('is_private', sa.Boolean, nullable=False, default=True),
        sa.Column('version', sa.Integer, nullable=False, default=1),
        sa.Column('parent_entry_id', UUID(as_uuid=True), nullable=True),
        sa.Column('template_id', UUID(as_uuid=True), nullable=True),
        sa.Column('search_vector', TSVECTOR, nullable=True),
        sa.Column('psychology_metadata', JSONB, nullable=False, default={}),
        sa.Column('analysis_results', JSONB, nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_entry_id'], ['entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['entry_templates.id'], ondelete='SET NULL'),
        sa.CheckConstraint('word_count >= 0', name='ck_entries_word_count_positive'),
        sa.CheckConstraint('version >= 1', name='ck_entries_version_positive'),
        sa.CheckConstraint('sentiment_score BETWEEN -1 AND 1', name='ck_entries_sentiment_range'),
    )
    
    # Entries indexes (optimized for performance)
    op.create_index('ix_entries_user_created', 'entries', ['user_id', 'created_at'])
    op.create_index('ix_entries_topic_created', 'entries', ['topic_id', 'created_at'])
    op.create_index('ix_entries_mood_sentiment', 'entries', ['mood', 'sentiment_score'])
    op.create_index('ix_entries_favorites', 'entries', ['user_id', 'is_favorite', 'created_at'])
    op.create_index('ix_entries_search_vector', 'entries', ['search_vector'], postgresql_using='gin')
    op.create_index('ix_entries_title_text', 'entries', ['title'], postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'})
    op.create_index('ix_entries_tags_gin', 'entries', ['tags'], postgresql_using='gin')
    op.create_index('ix_entries_psychology_gin', 'entries', ['psychology_metadata'], postgresql_using='gin')
    op.create_index('ix_entries_analysis_gin', 'entries', ['analysis_results'], postgresql_using='gin')
    
    # Chat sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('session_type', sa.String(50), nullable=False),
        sa.Column('personality_config', JSONB, nullable=False, default={}),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message_count', sa.Integer, nullable=False, default=0),
        sa.Column('total_duration_minutes', sa.Integer, nullable=False, default=0),
        sa.Column('average_response_time_ms', sa.Integer, nullable=True),
        sa.Column('psychology_insights', JSONB, nullable=False, default={}),
        sa.Column('coaching_notes', JSONB, nullable=False, default={}),
        sa.Column('progress_tracking', JSONB, nullable=False, default={}),
        sa.Column('tags', JSONB, nullable=False, default=[]),
        sa.Column('auto_tags', JSONB, nullable=False, default=[]),
        sa.Column('metadata', JSONB, nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('message_count >= 0', name='ck_sessions_message_count_positive'),
        sa.CheckConstraint('total_duration_minutes >= 0', name='ck_sessions_duration_positive'),
    )
    
    #