# backend/app/models/analytics.py - Analytics Caching Models

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class AnalyticsType(str, Enum):
    """Types of analytics that can be cached"""
    MOOD_TRENDS = "mood_trends"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ENTRY_STATS = "entry_stats"
    CHAT_STATS = "chat_stats" 
    TOPIC_ANALYSIS = "topic_analysis"
    WEEKLY_INSIGHTS = "weekly_insights"
    MONTHLY_INSIGHTS = "monthly_insights"
    YEAR_OVERVIEW = "year_overview"

class CacheStatus(str, Enum):
    """Status of cached analytics"""
    FRESH = "fresh"           # Recently computed, up to date
    STALE = "stale"           # Needs refresh but usable
    COMPUTING = "computing"   # Currently being processed
    FAILED = "failed"         # Last computation failed

class EntryAnalytics(BaseModel):
    """Individual entry analysis results"""
    entry_id: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    mood: str
    emotion_scores: Dict[str, float] = Field(default_factory=dict)
    detected_topics: List[str] = Field(default_factory=list)
    word_count: int
    reading_time_minutes: float
    language: Optional[str] = None
    analyzed_at: datetime
    
class SessionAnalytics(BaseModel):
    """Individual chat session analysis results"""
    session_id: str
    session_type: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    mood: str
    message_count: int
    user_message_count: int
    avg_message_length: float
    total_conversation_time_minutes: Optional[float] = None
    detected_topics: List[str] = Field(default_factory=list)
    analyzed_at: datetime

class AnalyticsCache(BaseModel):
    """Cached analytics computation results"""
    id: str
    analytics_type: AnalyticsType
    time_period_start: Optional[datetime] = None
    time_period_end: Optional[datetime] = None
    data: Dict[str, Any]  # The actual analytics results
    status: CacheStatus = CacheStatus.FRESH
    computed_at: datetime
    expires_at: Optional[datetime] = None  # When cache should be refreshed
    computation_time_seconds: Optional[float] = None
    entries_analyzed: int = 0
    sessions_analyzed: int = 0
    
class AnalyticsCacheCreate(BaseModel):
    """Create new analytics cache entry"""
    analytics_type: AnalyticsType
    time_period_start: Optional[datetime] = None
    time_period_end: Optional[datetime] = None
    data: Dict[str, Any]
    computation_time_seconds: Optional[float] = None
    entries_analyzed: int = 0
    sessions_analyzed: int = 0

class AnalyticsCacheUpdate(BaseModel):
    """Update analytics cache entry"""
    data: Optional[Dict[str, Any]] = None
    status: Optional[CacheStatus] = None
    expires_at: Optional[datetime] = None
    computation_time_seconds: Optional[float] = None
    entries_analyzed: Optional[int] = None
    sessions_analyzed: Optional[int] = None

class ProcessingStatus(BaseModel):
    """Track processing status for background tasks"""
    id: str
    task_type: str  # "entry_analysis", "session_analysis", "cache_refresh"
    status: str     # "pending", "processing", "completed", "failed"
    target_id: Optional[str] = None  # ID of entry/session being processed
    analytics_type: Optional[AnalyticsType] = None
    progress_percentage: float = 0.0
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class InsightsRequest(BaseModel):
    """Request for insights with caching preferences"""
    time_range_days: Optional[int] = 30
    force_refresh: bool = False
    include_cache_info: bool = False
    analytics_types: Optional[List[AnalyticsType]] = None

class InsightsResponse(BaseModel):
    """Response with insights and cache information"""
    data: Dict[str, Any]
    cache_info: Optional[Dict[str, Any]] = None
    last_updated: datetime
    is_fresh: bool
    computation_time_ms: Optional[float] = None
    entries_count: int
    sessions_count: int
