### app/services/database_service.py

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiofiles
import logging
from app.models.entry import Entry, EntryCreate, EntryUpdate, MoodType
from app.models.topic import Topic, TopicCreate, TopicUpdate

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.entries_file = self.data_dir / "entries.json"
        self.topics_file = self.data_dir / "topics.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        if not self.entries_file.exists():
            with open(self.entries_file, 'w') as f:
                json.dump({}, f)
        
        if not self.topics_file.exists():
            with open(self.topics_file, 'w') as f:
                json.dump({}, f)
    
    async def _read_entries(self) -> Dict[str, Any]:
        """Read entries from JSON file"""
        try:
            async with aiofiles.open(self.entries_file, 'r') as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except Exception as e:
            logger.error(f"Error reading entries: {e}")
            return {}
    
    async def _write_entries(self, entries: Dict[str, Any]):
        """Write entries to JSON file"""
        try:
            async with aiofiles.open(self.entries_file, 'w') as f:
                await f.write(json.dumps(entries, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error writing entries: {e}")
    
    async def _read_topics(self) -> Dict[str, Any]:
        """Read topics from JSON file"""
        try:
            async with aiofiles.open(self.topics_file, 'r') as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except Exception as e:
            logger.error(f"Error reading topics: {e}")
            return {}
    
    async def _write_topics(self, topics: Dict[str, Any]):
        """Write topics to JSON file"""
        try:
            async with aiofiles.open(self.topics_file, 'w') as f:
                await f.write(json.dumps(topics, indent=2, default=str))
        except Exception as e:
            logger.error(f"Error writing topics: {e}")
    
    # Entry operations
    async def create_entry(self, entry_data: EntryCreate, mood: MoodType, 
                          sentiment_score: float) -> Entry:
        """Create a new entry"""
        entries = await self._read_entries()
        
        entry_id = str(uuid.uuid4())
        now = datetime.now()
        
        entry = Entry(
            id=entry_id,
            title=entry_data.title,
            content=entry_data.content,
            entry_type=entry_data.entry_type,
            topic_id=entry_data.topic_id,
            tags=entry_data.tags,
            created_at=now,
            updated_at=now,
            mood=mood,
            sentiment_score=sentiment_score,
            word_count=len(entry_data.content.split()),
            metadata={}
        )
        
        entries[entry_id] = entry.model_dump()
        await self._write_entries(entries)
        
        # Update topic entry count if this is a topic entry
        if entry_data.topic_id:
            await self._update_topic_stats(entry_data.topic_id, now)
        
        return entry
    
    async def get_entry(self, entry_id: str) -> Optional[Entry]:
        """Get entry by ID"""
        entries = await self._read_entries()
        entry_data = entries.get(entry_id)
        
        if entry_data:
            return Entry(**entry_data)
        return None
    
    async def get_entries(self, skip: int = 0, limit: int = 100, 
                         topic_id: Optional[str] = None,
                         date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None) -> List[Entry]:
        """Get entries with optional filtering"""
        entries = await self._read_entries()
        entry_list = []
        
        for entry_data in entries.values():
            entry = Entry(**entry_data)
            
            # Apply filters
            if topic_id and entry.topic_id != topic_id:
                continue
            
            if date_from and entry.created_at < date_from:
                continue
                
            if date_to and entry.created_at > date_to:
                continue
            
            entry_list.append(entry)
        
        # Sort by creation date (newest first)
        entry_list.sort(key=lambda x: x.created_at, reverse=True)
        
        return entry_list[skip:skip + limit]
    
    async def update_entry(self, entry_id: str, entry_update: EntryUpdate, 
                          mood: Optional[MoodType] = None, 
                          sentiment_score: Optional[float] = None) -> Optional[Entry]:
        """Update an existing entry"""
        entries = await self._read_entries()
        
        if entry_id not in entries:
            return None
        
        entry_data = entries[entry_id]
        entry = Entry(**entry_data)
        
        # Update fields
        update_data = entry_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entry, field, value)
        
        entry.updated_at = datetime.now()
        
        # Update sentiment if content changed
        if mood is not None:
            entry.mood = mood
        if sentiment_score is not None:
            entry.sentiment_score = sentiment_score
        
        # Update word count if content changed
        if entry_update.content:
            entry.word_count = len(entry_update.content.split())
        
        entries[entry_id] = entry.model_dump()
        await self._write_entries(entries)
        
        return entry
    
    async def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry"""
        entries = await self._read_entries()
        
        if entry_id in entries:
            del entries[entry_id]
            await self._write_entries(entries)
            return True
        return False
    
    # Topic operations
    async def create_topic(self, topic_data: TopicCreate) -> Topic:
        """Create a new topic"""
        topics = await self._read_topics()
        
        topic_id = str(uuid.uuid4())
        now = datetime.now()
        
        topic = Topic(
            id=topic_id,
            name=topic_data.name,
            description=topic_data.description,
            color=topic_data.color,
            tags=topic_data.tags,
            created_at=now,
            updated_at=now,
            entry_count=0,
            last_entry_date=None,
            metadata={}
        )
        
        topics[topic_id] = topic.model_dump()
        await self._write_topics(topics)
        
        return topic
    
    async def get_topic(self, topic_id: str) -> Optional[Topic]:
        """Get topic by ID"""
        topics = await self._read_topics()
        topic_data = topics.get(topic_id)
        
        if topic_data:
            return Topic(**topic_data)
        return None
    
    async def get_topics(self) -> List[Topic]:
        """Get all topics"""
        topics = await self._read_topics()
        topic_list = [Topic(**topic_data) for topic_data in topics.values()]
        
        # Sort by last entry date (most recent first)
        topic_list.sort(key=lambda x: x.last_entry_date or datetime.min, reverse=True)
        
        return topic_list
    
    async def update_topic(self, topic_id: str, topic_update: TopicUpdate) -> Optional[Topic]:
        """Update an existing topic"""
        topics = await self._read_topics()
        
        if topic_id not in topics:
            return None
        
        topic_data = topics[topic_id]
        topic = Topic(**topic_data)
        
        # Update fields
        update_data = topic_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(topic, field, value)
        
        topic.updated_at = datetime.now()
        
        topics[topic_id] = topic.model_dump()
        await self._write_topics(topics)
        
        return topic
    
    async def delete_topic(self, topic_id: str) -> bool:
        """Delete a topic"""
        topics = await self._read_topics()
        
        if topic_id in topics:
            del topics[topic_id]
            await self._write_topics(topics)
            return True
        return False
    
    async def _update_topic_stats(self, topic_id: str, entry_date: datetime):
        """Update topic statistics when new entry is added"""
        topics = await self._read_topics()
        
        if topic_id in topics:
            topic_data = topics[topic_id]
            topic_data['entry_count'] = topic_data.get('entry_count', 0) + 1
            topic_data['last_entry_date'] = entry_date.isoformat()
            topic_data['updated_at'] = datetime.now().isoformat()
            
            await self._write_topics(topics)
    
    async def get_mood_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get mood statistics for the last N days"""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        entries = await self.get_entries(date_from=start_date, date_to=end_date)
        
        mood_counts = {}
        daily_moods = {}
        
        for entry in entries:
            if entry.mood:
                mood_str = entry.mood.value
                mood_counts[mood_str] = mood_counts.get(mood_str, 0) + 1
                
                # Daily mood tracking
                date_str = entry.created_at.strftime('%Y-%m-%d')
                if date_str not in daily_moods:
                    daily_moods[date_str] = []
                daily_moods[date_str].append(mood_str)
        
        return {
            'mood_distribution': mood_counts,
            'daily_moods': daily_moods,
            'total_entries': len(entries),
            'period_days': days
        }

# Global instance
db_service = DatabaseService()