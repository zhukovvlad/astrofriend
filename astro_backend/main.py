"""
Astro-Soulmate: FastAPI Main Application
Complete API with Auth, Boyfriends, and Chat endpoints
"""
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from config import settings
from database import get_session, init_db
from models import (
    User, UserCreate, UserRead,
    Boyfriend, BoyfriendCreate, BoyfriendRead,
    ChatSession, ChatSessionCreate, ChatSessionRead,
    ChatRequest, ChatResponse,
    Token
)
from services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id
)
from services.ai_client import ai_client


# ============================================
# APPLICATION LIFECYCLE
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    print("🚀 Starting Astro-Soulmate API...")
    await init_db()
    print("✅ Database initialized")
    yield
    # Shutdown
    print("👋 Shutting down Astro-Soulmate API...")


# ============================================
# FASTAPI APP CONFIGURATION
# ============================================
app = FastAPI(
    title=settings.app_name,
    description="AI Boyfriend Relationship Simulator - Find your Astro Soulmate! 💫",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# HEALTH CHECK
# ============================================
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "message": "Welcome to Astro-Soulmate! 💫"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "ai": "ready" if settings.google_api_key else "not configured"
    }


# ============================================
# AUTH ENDPOINTS
# ============================================
@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: Password (will be hashed)
    """
    # Check if email already exists
    statement = select(User).where(User.email == user_data.email)
    result = await session.execute(statement)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user


@app.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """
    Login and receive JWT access token.
    
    Use the returned token in the Authorization header:
    `Authorization: Bearer <token>`
    """
    # Find user by email (username field in OAuth2 form)
    statement = select(User).where(User.email == form_data.username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Generate JWT token
    access_token = create_access_token(user_id=user.id, email=user.email)
    
    return Token(access_token=access_token)


@app.get("/auth/me", response_model=UserRead, tags=["Auth"])
async def get_current_user(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get current authenticated user info."""
    statement = select(User).where(User.id == current_user_id)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# ============================================
# BOYFRIEND ENDPOINTS (Protected)
# ============================================
@app.post("/boyfriends", response_model=BoyfriendRead, status_code=status.HTTP_201_CREATED, tags=["Boyfriends"])
async def create_boyfriend(
    boyfriend_data: BoyfriendCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new AI boyfriend persona.
    
    - **name**: Display name for your boyfriend
    - **birth_data**: Astrological birth data for personality generation
    """
    # Generate astrological profile
    birth_dict = boyfriend_data.birth_data.model_dump()
    astro_profile = await ai_client.generate_astro_profile(birth_dict)
    
    # Build system prompt with astro personality
    system_prompt = ai_client._build_system_prompt(
        boyfriend_name=boyfriend_data.name,
        astro_profile=astro_profile
    )
    
    # Create boyfriend
    new_boyfriend = Boyfriend(
        user_id=current_user_id,
        name=boyfriend_data.name,
        birth_data=birth_dict,
        system_prompt=system_prompt
    )
    
    session.add(new_boyfriend)
    await session.commit()
    await session.refresh(new_boyfriend)
    
    return new_boyfriend


@app.get("/boyfriends", response_model=List[BoyfriendRead], tags=["Boyfriends"])
async def list_boyfriends(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    List all boyfriends created by the current user.
    
    Returns boyfriends sorted by creation date (newest first).
    """
    statement = (
        select(Boyfriend)
        .where(Boyfriend.user_id == current_user_id)
        .order_by(Boyfriend.created_at.desc())
    )
    result = await session.execute(statement)
    boyfriends = result.scalars().all()
    
    return boyfriends


@app.get("/boyfriends/{boyfriend_id}", response_model=BoyfriendRead, tags=["Boyfriends"])
async def get_boyfriend(
    boyfriend_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific boyfriend by ID."""
    statement = select(Boyfriend).where(
        Boyfriend.id == boyfriend_id,
        Boyfriend.user_id == current_user_id
    )
    result = await session.execute(statement)
    boyfriend = result.scalar_one_or_none()
    
    if not boyfriend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boyfriend not found or access denied"
        )
    
    return boyfriend


@app.delete("/boyfriends/{boyfriend_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Boyfriends"])
async def delete_boyfriend(
    boyfriend_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Delete a boyfriend and all associated chat sessions."""
    statement = select(Boyfriend).where(
        Boyfriend.id == boyfriend_id,
        Boyfriend.user_id == current_user_id
    )
    result = await session.execute(statement)
    boyfriend = result.scalar_one_or_none()
    
    if not boyfriend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boyfriend not found or access denied"
        )
    
    # Delete associated chat sessions first
    chat_statement = select(ChatSession).where(ChatSession.boyfriend_id == boyfriend_id)
    chat_result = await session.execute(chat_statement)
    for chat in chat_result.scalars().all():
        await session.delete(chat)
    
    await session.delete(boyfriend)
    await session.commit()


# ============================================
# CHAT ENDPOINTS (Protected)
# ============================================
@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_with_boyfriend(
    chat_request: ChatRequest,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Send a message to your AI boyfriend and receive a response.
    
    - **boyfriend_id**: ID of the boyfriend to chat with
    - **message**: Your message
    - **session_id**: Optional - continue existing chat session
    
    Security: Verifies that the boyfriend belongs to the current user.
    """
    # Verify boyfriend ownership (SECURITY: users can't chat with others' boyfriends)
    boyfriend_statement = select(Boyfriend).where(
        Boyfriend.id == chat_request.boyfriend_id,
        Boyfriend.user_id == current_user_id
    )
    result = await session.execute(boyfriend_statement)
    boyfriend = result.scalar_one_or_none()
    
    if not boyfriend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boyfriend not found or access denied"
        )
    
    # Get or create chat session
    chat_session: Optional[ChatSession] = None
    
    if chat_request.session_id:
        session_statement = select(ChatSession).where(
            ChatSession.id == chat_request.session_id,
            ChatSession.boyfriend_id == boyfriend.id
        )
        result = await session.execute(session_statement)
        chat_session = result.scalar_one_or_none()
    
    if not chat_session:
        chat_session = ChatSession(
            boyfriend_id=boyfriend.id,
            title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
            history=[]
        )
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
    
    # Generate AI response
    ai_response = await ai_client.generate_response(
        message=chat_request.message,
        boyfriend_name=boyfriend.name,
        system_prompt=boyfriend.system_prompt,
        chat_history=chat_session.history
    )
    
    # Update chat history
    timestamp = datetime.utcnow().isoformat()
    updated_history = list(chat_session.history) if chat_session.history else []
    updated_history.append({
        "role": "user",
        "content": chat_request.message,
        "timestamp": timestamp
    })
    updated_history.append({
        "role": "assistant", 
        "content": ai_response,
        "timestamp": timestamp
    })
    
    chat_session.history = updated_history
    chat_session.updated_at = datetime.utcnow()
    
    session.add(chat_session)
    await session.commit()
    
    return ChatResponse(
        session_id=chat_session.id,
        boyfriend_id=boyfriend.id,
        user_message=chat_request.message,
        ai_response=ai_response
    )


@app.get("/chat/sessions", response_model=List[ChatSessionRead], tags=["Chat"])
async def list_chat_sessions(
    boyfriend_id: Optional[uuid.UUID] = None,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    List chat sessions for the current user.
    
    - **boyfriend_id**: Optional filter by specific boyfriend
    """
    # Get all boyfriend IDs for the current user
    boyfriend_statement = select(Boyfriend.id).where(Boyfriend.user_id == current_user_id)
    result = await session.execute(boyfriend_statement)
    user_boyfriend_ids = [row[0] for row in result.all()]
    
    if not user_boyfriend_ids:
        return []
    
    # Build chat session query
    if boyfriend_id:
        if boyfriend_id not in user_boyfriend_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Boyfriend not found or access denied"
            )
        session_statement = (
            select(ChatSession)
            .where(ChatSession.boyfriend_id == boyfriend_id)
            .order_by(ChatSession.updated_at.desc())
        )
    else:
        session_statement = (
            select(ChatSession)
            .where(ChatSession.boyfriend_id.in_(user_boyfriend_ids))
            .order_by(ChatSession.updated_at.desc())
        )
    
    result = await session.execute(session_statement)
    chat_sessions = result.scalars().all()
    
    return chat_sessions


@app.get("/chat/sessions/{session_id}", response_model=ChatSessionRead, tags=["Chat"])
async def get_chat_session(
    session_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific chat session with full history."""
    # Get chat session
    chat_statement = select(ChatSession).where(ChatSession.id == session_id)
    result = await session.execute(chat_statement)
    chat_session = result.scalar_one_or_none()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Verify ownership through boyfriend
    boyfriend_statement = select(Boyfriend).where(
        Boyfriend.id == chat_session.boyfriend_id,
        Boyfriend.user_id == current_user_id
    )
    result = await session.execute(boyfriend_statement)
    boyfriend = result.scalar_one_or_none()
    
    if not boyfriend:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chat session"
        )
    
    return chat_session


@app.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chat"])
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Delete a chat session."""
    # Get chat session
    chat_statement = select(ChatSession).where(ChatSession.id == session_id)
    result = await session.execute(chat_statement)
    chat_session = result.scalar_one_or_none()
    
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Verify ownership through boyfriend
    boyfriend_statement = select(Boyfriend).where(
        Boyfriend.id == chat_session.boyfriend_id,
        Boyfriend.user_id == current_user_id
    )
    result = await session.execute(boyfriend_statement)
    boyfriend = result.scalar_one_or_none()
    
    if not boyfriend:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chat session"
        )
    
    await session.delete(chat_session)
    await session.commit()


# ============================================
# RUN WITH UVICORN
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
