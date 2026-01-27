"""
Astro-Soulmate: FastAPI Main Application
Complete API with Auth, AI Characters, and Chat endpoints
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from config import settings
from database import get_session, init_db
from models import (
    User, UserCreate, UserRead,
    AICharacter, AICharacterCreate, AICharacterRead,
    ChatSession, ChatSessionCreate, ChatSessionRead,
    ChatRequest, ChatResponse,
    Token,
    utc_now
)
from services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id,
    set_auth_cookie,
    clear_auth_cookie
)
from services.ai_client import ai_client


# ============================================
# HELPER FUNCTIONS
# ============================================
def compute_age_from_birth_dict(birth_data: dict) -> Optional[int]:
    """
    Compute age from birth data dictionary using full birthdate.
    
    Args:
        birth_data: Dictionary containing 'year', 'month', 'day' keys
        
    Returns:
        Age in years if valid, None if invalid or future date
    """
    if not birth_data:
        return None
    
    try:
        year = int(birth_data.get("year", 0))
        month = int(birth_data.get("month", 1))
        day = int(birth_data.get("day", 1))
        
        # Validate date components
        if year <= 0 or month < 1 or month > 12 or day < 1 or day > 31:
            return None
        
        birthdate = datetime(year, month, day)
        today = utc_now()
        
        # Check if birthdate is in the future
        if birthdate > today:
            return None
        
        # Calculate age considering full birthdate
        age = today.year - birthdate.year
        
        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            age -= 1
        
        # Return None for negative ages (shouldn't happen with future date check, but safety)
        return age if age >= 0 else None
        
    except (ValueError, TypeError, KeyError):
        return None


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
    description="AI Character Relationship Simulator - Find your Astro Soulmate! 💫",
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


@app.post("/auth/login", response_model=UserRead, tags=["Auth"])
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """
    Login and receive httpOnly cookie with JWT access token.
    
    The token is automatically set as a secure httpOnly cookie.
    No need to manually handle the token on the client side.
    """
    # Find user by email (username field in OAuth2 form)
    statement = select(User).where(User.email == form_data.username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Generate JWT token and set httpOnly cookie
    access_token = create_access_token(user_id=user.id, email=user.email)
    set_auth_cookie(response, access_token)
    
    return user


@app.post("/auth/logout", tags=["Auth"])
async def logout(response: Response):
    """
    Logout and clear the authentication cookie.
    """
    clear_auth_cookie(response)
    return {"message": "Successfully logged out"}


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
# AI CHARACTER ENDPOINTS (Protected)
# ============================================
@app.post("/ai-characters", response_model=AICharacterRead, status_code=status.HTTP_201_CREATED, tags=["AI Characters"])
async def create_ai_character(
    character_data: AICharacterCreate,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new AI character persona.
    
    - **name**: Display name for your AI character
    - **birth_data**: Astrological birth data for personality generation
    """
    # Generate astrological profile
    birth_dict = character_data.birth_data.model_dump()
    astro_profile = await ai_client.generate_astro_profile(birth_dict)
    
    # Calculate age from birth_data
    age = compute_age_from_birth_dict(birth_dict)
    
    # Build system prompt with astro personality and gender
    system_prompt = ai_client._build_system_prompt(
        character_name=character_data.name,
        gender=character_data.gender or "male",
        astro_profile=astro_profile,
        age=age
    )
    
    # Create AI character
    new_character = AICharacter(
        user_id=current_user_id,
        name=character_data.name,
        gender=character_data.gender or "male",
        birth_data=birth_dict,
        system_prompt=system_prompt
    )
    
    session.add(new_character)
    await session.commit()
    await session.refresh(new_character)
    
    return new_character


@app.get("/ai-characters", response_model=List[AICharacterRead], tags=["AI Characters"])
async def list_ai_characters(
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    List all AI characters created by the current user.
    
    Returns characters sorted by creation date (newest first).
    """
    statement = (
        select(AICharacter)
        .where(AICharacter.user_id == current_user_id)
        .order_by(AICharacter.created_at.desc())
    )
    result = await session.execute(statement)
    characters = result.scalars().all()
    
    return characters


@app.get("/ai-characters/{character_id}", response_model=AICharacterRead, tags=["AI Characters"])
async def get_ai_character(
    character_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific AI character by ID."""
    statement = select(AICharacter).where(
        AICharacter.id == character_id,
        AICharacter.user_id == current_user_id
    )
    result = await session.execute(statement)
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Character not found or access denied"
        )
    
    return character


@app.delete("/ai-characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["AI Characters"])
async def delete_ai_character(
    character_id: uuid.UUID,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """Delete an AI character and all associated chat sessions."""
    statement = select(AICharacter).where(
        AICharacter.id == character_id,
        AICharacter.user_id == current_user_id
    )
    result = await session.execute(statement)
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Character not found or access denied"
        )
    
    # Delete associated chat sessions first
    chat_statement = select(ChatSession).where(ChatSession.ai_character_id == character_id)
    chat_result = await session.execute(chat_statement)
    for chat in chat_result.scalars().all():
        await session.delete(chat)
    
    await session.delete(character)
    await session.commit()


# ============================================
# CHAT ENDPOINTS (Protected)
# ============================================
@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_with_ai_character(
    chat_request: ChatRequest,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Send a message to your AI character and receive a response.
    
    - **ai_character_id**: ID of the AI character to chat with
    - **message**: Your message
    - **session_id**: Optional - continue existing chat session
    
    Security: Verifies that the AI character belongs to the current user.
    """
    # Verify AI character ownership (SECURITY: users can't chat with others' characters)
    character_statement = select(AICharacter).where(
        AICharacter.id == chat_request.ai_character_id,
        AICharacter.user_id == current_user_id
    )
    result = await session.execute(character_statement)
    character = result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Character not found or access denied"
        )
    
    # Get or create chat session
    chat_session: Optional[ChatSession] = None
    
    if chat_request.session_id:
        session_statement = select(ChatSession).where(
            ChatSession.id == chat_request.session_id,
            ChatSession.ai_character_id == character.id
        )
        result = await session.execute(session_statement)
        chat_session = result.scalar_one_or_none()
    
    if not chat_session:
        chat_session = ChatSession(
            ai_character_id=character.id,
            title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
            history=[]
        )
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
    
    # Calculate age from birth_data
    age = compute_age_from_birth_dict(character.birth_data)
    
    # Generate AI response with current relationship score (from character, not session)
    astro_profile = await ai_client.generate_astro_profile(character.birth_data)
    ai_response = await ai_client.generate_response(
        message=chat_request.message,
        character_name=character.name,
        gender=character.gender,
        chat_history=chat_session.history,
        astro_profile=astro_profile,
        age=age,
        relationship_score=character.relationship_score
    )
    
    # Re-fetch character with row lock to prevent lost updates on concurrent chats
    # This ensures that if two users chat with the same character simultaneously,
    # score changes won't overwrite each other (lost update problem)
    character_lock_statement = (
        select(AICharacter)
        .where(AICharacter.id == character.id)
        .with_for_update()
    )
    result = await session.execute(character_lock_statement)
    character = result.scalar_one()
    
    # Calculate new relationship score (clamped between 0-100)
    new_score = max(0, min(100, character.relationship_score + ai_response.score_change))
    
    # Update chat history
    timestamp = utc_now().isoformat()
    updated_history = list(chat_session.history) if chat_session.history else []
    updated_history.append({
        "role": "user",
        "content": chat_request.message,
        "timestamp": timestamp
    })
    updated_history.append({
        "role": "assistant", 
        "content": ai_response.reply_text,
        "timestamp": timestamp
    })
    
    # Update chat session history
    chat_session.history = updated_history
    chat_session.updated_at = utc_now()
    session.add(chat_session)
    
    # Update character's relationship state (applies to ALL chats with this character)
    character.relationship_score = new_score
    character.current_status = ai_response.status_label
    character.updated_at = utc_now()
    session.add(character)
    
    await session.commit()
    
    # Fetch current user to check premium status
    user_statement = select(User).where(User.id == current_user_id)
    user_result = await session.execute(user_statement)
    current_user = user_result.scalar_one()
    
    # Only include internal_thought for premium users
    # TODO: Add is_premium field to User model when implementing premium features
    is_premium = getattr(current_user, 'is_premium', False)  # Default to False if field doesn't exist yet
    
    return ChatResponse(
        session_id=chat_session.id,
        ai_character_id=character.id,
        user_message=chat_request.message,
        ai_response=ai_response.reply_text,
        relationship_score=new_score,
        current_status=ai_response.status_label,
        score_change=ai_response.score_change,
        internal_thought=ai_response.internal_thought if is_premium else None
    )


@app.get("/chat/sessions", response_model=List[ChatSessionRead], tags=["Chat"])
async def list_chat_sessions(
    ai_character_id: Optional[uuid.UUID] = None,
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    List chat sessions for the current user.
    
    - **ai_character_id**: Optional filter by specific AI character
    """
    # Get all AI character IDs for the current user
    character_statement = select(AICharacter.id).where(AICharacter.user_id == current_user_id)
    result = await session.execute(character_statement)
    user_character_ids = [row[0] for row in result.all()]
    
    if not user_character_ids:
        return []
    
    # Build chat session query
    if ai_character_id:
        if ai_character_id not in user_character_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI Character not found or access denied"
            )
        session_statement = (
            select(ChatSession)
            .where(ChatSession.ai_character_id == ai_character_id)
            .order_by(ChatSession.updated_at.desc())
        )
    else:
        session_statement = (
            select(ChatSession)
            .where(ChatSession.ai_character_id.in_(user_character_ids))
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
    
    # Verify ownership through AI character
    character_statement = select(AICharacter).where(
        AICharacter.id == chat_session.ai_character_id,
        AICharacter.user_id == current_user_id
    )
    result = await session.execute(character_statement)
    character = result.scalar_one_or_none()
    
    if not character:
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
    
    # Verify ownership through AI character
    character_statement = select(AICharacter).where(
        AICharacter.id == chat_session.ai_character_id,
        AICharacter.user_id == current_user_id
    )
    result = await session.execute(character_statement)
    character = result.scalar_one_or_none()
    
    if not character:
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
