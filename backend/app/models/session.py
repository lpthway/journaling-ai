### app/models/session.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


# Enums
class SessionType(str, Enum):
    REFLECTION_BUDDY = "reflection_buddy"
    INNER_VOICE = "inner_voice"
    GROWTH_CHALLENGE = "growth_challenge"
    PATTERN_DETECTIVE = "pattern_detective"
    FREE_CHAT = "free_chat"


class SessionStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Message Models
class MessageCreate(BaseModel):
    content: str
    role: MessageRole = MessageRole.USER
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    content: str
    role: MessageRole
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageResponse(BaseModel):
    id: str
    session_id: str
    content: str
    role: MessageRole
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Session Models
class SessionCreate(BaseModel):
    session_type: SessionType
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SessionStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_type: SessionType
    title: str
    description: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = None
    message_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionResponse(BaseModel):
    id: str
    session_type: SessionType
    title: str
    description: Optional[str] = None
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    last_activity: Optional[datetime] = None
    message_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    recent_messages: Optional[List[MessageResponse]] = None


# Session Type Configuration
class SessionTypeConfig(BaseModel):
    type: SessionType
    name: str
    description: str
    icon: str
    tags: List[str]
    system_prompt: str
    initial_message: Optional[str] = None
    features: List[str] = Field(default_factory=list)


# Available session types with their configurations
SESSION_TYPE_CONFIGS = {
    SessionType.REFLECTION_BUDDY: SessionTypeConfig(
        type=SessionType.REFLECTION_BUDDY,
        name="Reflection Buddy",
        description="Chat with a curious friend who asks thoughtful questions",
        icon="💭",
        tags=["casual", "friendly", "exploration"],
        system_prompt="""You are a warm, curious friend who loves asking thoughtful questions. 
        Your goal is to help the user explore their thoughts and feelings through gentle, 
        open-ended questions. Be supportive, non-judgmental, and genuinely interested in their perspective.""",
        initial_message="Hi there! I'm excited to chat with you. What's on your mind today?",
        features=["thoughtful_questions", "active_listening", "perspective_exploration"]
    ),
    
    SessionType.INNER_VOICE: SessionTypeConfig(
        type=SessionType.INNER_VOICE,
        name="Inner Voice Assistant",
        description="Explore different perspectives on situations and decisions",
        icon="🧠",
        tags=["perspective", "wisdom", "insight"],
        system_prompt="""You are a wise inner voice that helps users explore different perspectives 
        on their situations and decisions. Ask probing questions that help them see things from 
        multiple angles and discover insights they might not have considered.""",
        initial_message="Let's explore what's happening in your inner world. What situation or decision would you like to examine together?",
        features=["perspective_shift", "decision_support", "wisdom_sharing"]
    ),
    
    SessionType.GROWTH_CHALLENGE: SessionTypeConfig(
        type=SessionType.GROWTH_CHALLENGE,
        name="Growth Challenge",
        description="Take on challenges designed to promote personal growth",
        icon="🌱",
        tags=["growth", "challenge", "development"],
        system_prompt="""You are a supportive growth coach who presents personalized challenges 
        and exercises to help users develop personally. Focus on actionable steps and gentle 
        accountability while celebrating progress.""",
        initial_message="Ready for some growth? I'd love to understand what areas you're looking to develop, so I can suggest some meaningful challenges.",
        features=["growth_challenges", "skill_development", "progress_tracking"]
    ),
    
    SessionType.PATTERN_DETECTIVE: SessionTypeConfig(
        type=SessionType.PATTERN_DETECTIVE,
        name="Pattern Detective",
        description="Discover patterns in your thoughts and behaviors",
        icon="🔍",
        tags=["patterns", "analysis", "insights"],
        system_prompt="""You are a skilled pattern detective who helps users identify recurring 
        themes, behaviors, and thought patterns in their life. Ask specific questions that 
        help uncover these patterns and their potential meanings.""",
        initial_message="Let's put on our detective hats! I'm here to help you spot patterns in your thoughts, feelings, or behaviors. What area of your life would you like to investigate?",
        features=["pattern_recognition", "behavioral_analysis", "insight_generation"]
    ),
    
    SessionType.FREE_CHAT: SessionTypeConfig(
        type=SessionType.FREE_CHAT,
        name="Free Chat",
        description="Open conversation without specific structure",
        icon="💬",
        tags=["open", "flexible", "conversation"],
        system_prompt="""You are a supportive conversational partner. Follow the user's lead 
        and adapt your style to what they need - whether that's listening, brainstorming, 
        problem-solving, or just having a friendly chat.""",
        initial_message="Hi! I'm here to chat about whatever's on your mind. What would you like to talk about?",
        features=["flexible_conversation", "adaptive_support", "open_dialogue"]
    )
}