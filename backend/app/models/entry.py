### app/models/entry.py

from pydantic import BaseModel, Field
from datetime import datetime, date
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
    template_id: Optional[str] = None

class EntryCreate(EntryBase):
    user_id: Optional[str] = None  # Allow user_id to be provided during creation
    created_at: Optional[datetime] = None  # Allow custom creation timestamp for historical data

class Entry(EntryBase):
    id: str
    user_id: Optional[str] = None  # Include user_id in response
    created_at: datetime
    updated_at: datetime
    mood: Optional[MoodType] = None
    sentiment_score: Optional[float] = None
    word_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_favorite: bool = False
    version: int = 1
    parent_entry_id: Optional[str] = None  # For versioning
    emotion_analysis: Optional[Dict[str, Any]] = None  # AI emotion analysis results
    ai_analysis: Optional[Dict[str, Any]] = None  # General AI analysis results

class EntryResponse(Entry):
    model_config = {"from_attributes": True, "use_enum_values": True}

class EntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None

class EntryVersion(BaseModel):
    id: str
    entry_id: str
    version: int
    title: str
    content: str
    tags: List[str]
    created_at: datetime
    mood: Optional[MoodType] = None
    sentiment_score: Optional[float] = None
    word_count: int

class EntryTemplate(BaseModel):
    id: str
    name: str
    description: str
    content_template: str
    prompts: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    category: str
    created_at: datetime

class EntryTemplateCreate(BaseModel):
    name: str
    description: str
    content_template: str
    prompts: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    category: str

class AdvancedSearchFilter(BaseModel):
    query: Optional[str] = None
    mood: Optional[MoodType] = None
    tags: Optional[List[str]] = None
    topic_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    word_count_min: Optional[int] = None
    word_count_max: Optional[int] = None
    is_favorite: Optional[bool] = None
    limit: int = 20
    offset: int = 0