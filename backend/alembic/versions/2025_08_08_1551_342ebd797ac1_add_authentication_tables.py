# backend/alembic/script.py.mako - Migration Template

"""Add authentication tables

Revision ID: 342ebd797ac1
Revises: df1052ae30b8
Create Date: 2025-08-08 15:51:38.584685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '342ebd797ac1'
down_revision: Union[str, None] = 'df1052ae30b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create auth_users table
    op.create_table(
        'auth_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('verification_token', sa.String(255), nullable=True),
        sa.Column('verification_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reset_token', sa.String(255), nullable=True),
        sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('language', sa.String(10), nullable=False, default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Create indexes for auth_users
    op.create_index('ix_auth_users_id', 'auth_users', ['id'])
    op.create_index('ix_auth_users_username', 'auth_users', ['username'])
    op.create_index('ix_auth_users_email', 'auth_users', ['email'])
    op.create_index('ix_auth_users_email_active', 'auth_users', ['email', 'is_active'])
    op.create_index('ix_auth_users_username_active', 'auth_users', ['username', 'is_active'])
    op.create_index('ix_auth_users_verification', 'auth_users', ['verification_token'])
    op.create_index('ix_auth_users_reset', 'auth_users', ['reset_token'])
    op.create_index('ix_auth_users_locked', 'auth_users', ['locked_until'])
    op.create_index('ix_auth_users_created_at', 'auth_users', ['created_at'])
    op.create_index('ix_auth_users_deleted_at', 'auth_users', ['deleted_at'])
    
    # Create unique constraints
    op.create_unique_constraint('uq_auth_users_username', 'auth_users', ['username'])
    op.create_unique_constraint('uq_auth_users_email', 'auth_users', ['email'])
    
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('replaced_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Create indexes for refresh_tokens
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'])
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_index('ix_refresh_tokens_user_active', 'refresh_tokens', ['user_id', 'is_revoked', 'expires_at'])
    op.create_index('ix_refresh_tokens_cleanup', 'refresh_tokens', ['expires_at', 'is_revoked'])
    op.create_index('ix_refresh_tokens_created_at', 'refresh_tokens', ['created_at'])
    op.create_index('ix_refresh_tokens_deleted_at', 'refresh_tokens', ['deleted_at'])
    
    # Create unique constraint
    op.create_unique_constraint('uq_refresh_tokens_token', 'refresh_tokens', ['token'])
    
    # Create login_attempts table
    op.create_table(
        'login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('username_or_email', sa.String(255), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('failure_reason', sa.String(100), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Create indexes for login_attempts
    op.create_index('ix_login_attempts_username_or_email', 'login_attempts', ['username_or_email'])
    op.create_index('ix_login_attempts_success', 'login_attempts', ['success'])
    op.create_index('ix_login_attempts_ip_address', 'login_attempts', ['ip_address'])
    op.create_index('ix_login_attempts_user_id', 'login_attempts', ['user_id'])
    op.create_index('ix_login_attempts_attempted_at', 'login_attempts', ['attempted_at'])
    op.create_index('ix_login_attempts_user_time', 'login_attempts', ['username_or_email', 'attempted_at'])
    op.create_index('ix_login_attempts_ip_time', 'login_attempts', ['ip_address', 'attempted_at'])
    op.create_index('ix_login_attempts_success_time', 'login_attempts', ['success', 'attempted_at'])
    op.create_index('ix_login_attempts_created_at', 'login_attempts', ['created_at'])
    op.create_index('ix_login_attempts_deleted_at', 'login_attempts', ['deleted_at'])


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop tables in reverse order
    op.drop_table('login_attempts')
    op.drop_table('refresh_tokens')
    op.drop_table('auth_users')
