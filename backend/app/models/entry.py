### app/models/entry.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class MoodType(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class EntryType(str, Enum):
    JOURNAL = "journal"
    TOPIC = "topic"

class EntryBase(BaseModel):
    title: str
    content: str
    entry_type: EntryType
    topic_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class EntryCreate(EntryBase):
    pass

class Entry(EntryBase):
    id: str
    created_at: datetime
    updated_at: datetime
    mood: Optional[MoodType] = None
    sentiment_score: Optional[float] = None
    word_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EntryResponse(Entry):
    pass

class EntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None