# backend/app/models/base.py
"""
Base model class for all database models.
"""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import Optional, List


class Base(AsyncAttrs, DeclarativeBase):
    """Enhanced base class with common patterns for all models."""
    
    # Common audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Soft deletion support
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    
    @hybrid_property
    def is_active(self) -> bool:
        """Check if record is not soft-deleted."""
        return self.deleted_at is None