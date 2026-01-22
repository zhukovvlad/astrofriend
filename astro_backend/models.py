"""
Astro-Soulmate: Database Models
SQLModel ORM with PostgreSQL
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
import uuid


# ============================================
# USER MODEL
# ============================================
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)
    telegram_id: Optional[int] = Field(default=None, unique=True, index=True)
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    ai_characters: List["AICharacter"] = Relationship(back_populates="user")


class UserCreate(SQLModel):
    """Schema for user registration"""
    email: str
    password: str


class UserRead(SQLModel):
    """Schema for user response (no password)"""
    id: uuid.UUID
    email: str
    telegram_id: Optional[int]
    is_active: bool
    created_at: datetime


# ============================================
# AI CHARACTER (AI PERSONA) MODEL
# ============================================
class BirthData(SQLModel):
    """Nested schema for astrological birth data"""
    name: str
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    city: str = "Moscow"
    nation: str = "RU"


class AICharacterBase(SQLModel):
    name: str = Field(max_length=100, index=True)
    gender: str = Field(default="male", max_length=20)  # "male" or "female"
    birth_data: dict = Field(default={}, sa_column=Column(JSON))
    system_prompt: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class AICharacter(AICharacterBase, table=True):
    __tablename__ = "ai_characters"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: User = Relationship(back_populates="ai_characters")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="ai_character")


class AICharacterCreate(SQLModel):
    """Schema for creating an AI character persona"""
    name: str
    gender: str = "male"  # "male" or "female"
    birth_data: BirthData


class AICharacterRead(SQLModel):
    """Schema for AI character response"""
    id: uuid.UUID
    name: str
    gender: str
    birth_data: dict
    system_prompt: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime


# ============================================
# CHAT SESSION MODEL
# ============================================
class ChatMessage(SQLModel):
    """Schema for a single chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatSessionBase(SQLModel):
    title: Optional[str] = Field(default="New Chat", max_length=200)
    history: List[dict] = Field(default=[], sa_column=Column(JSON))


class ChatSession(ChatSessionBase, table=True):
    __tablename__ = "chat_sessions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ai_character_id: uuid.UUID = Field(foreign_key="ai_characters.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    ai_character: AICharacter = Relationship(back_populates="chat_sessions")


class ChatSessionCreate(SQLModel):
    """Schema for creating a chat session"""
    ai_character_id: uuid.UUID
    title: Optional[str] = "New Chat"


class ChatSessionRead(SQLModel):
    """Schema for chat session response"""
    id: uuid.UUID
    ai_character_id: uuid.UUID
    title: Optional[str]
    history: List[dict]
    created_at: datetime


# ============================================
# CHAT REQUEST/RESPONSE SCHEMAS
# ============================================
class ChatRequest(SQLModel):
    """Schema for chat API request"""
    ai_character_id: uuid.UUID
    message: str
    session_id: Optional[uuid.UUID] = None


class ChatResponse(SQLModel):
    """Schema for chat API response"""
    session_id: uuid.UUID
    ai_character_id: uuid.UUID
    user_message: str
    ai_response: str


# ============================================
# AUTH SCHEMAS
# ============================================
class Token(SQLModel):
    """JWT Token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    """Data encoded in JWT"""
    user_id: Optional[str] = None
    email: Optional[str] = None
