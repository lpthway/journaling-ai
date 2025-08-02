### app/models/topic.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#3B82F6"  # Default blue color
    tags: List[str] = Field(default_factory=list)

class TopicCreate(TopicBase):
    pass

class Topic(TopicBase):
    id: str
    created_at: datetime
    updated_at: datetime
    entry_count: int = 0
    last_entry_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TopicResponse(Topic):
    pass

class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None