"""
Astro-Soulmate: Authentication Service
JWT Token generation and password hashing
"""
from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config import settings
from models import TokenData

# OAuth2 scheme for token extraction from headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ============================================
# PASSWORD UTILITIES
# ============================================
def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if passwords match, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ============================================
# JWT TOKEN UTILITIES
# ============================================
def create_access_token(
    user_id: uuid.UUID,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User's UUID
        email: User's email address
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            return None
            
        return TokenData(user_id=user_id, email=email)
        
    except JWTError:
        return None


# ============================================
# AUTHENTICATION DEPENDENCY
# ============================================
async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    """
    FastAPI dependency to extract and validate current user from JWT token.
    
    Args:
        token: JWT token from Authorization header (injected by OAuth2PasswordBearer)
        
    Returns:
        User's UUID
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = decode_access_token(token)
    
    if token_data is None or token_data.user_id is None:
        raise credentials_exception
    
    try:
        user_id = uuid.UUID(token_data.user_id)
    except ValueError:
        raise credentials_exception
    
    return user_id


# ============================================
# OPTIONAL AUTH (for public routes that can benefit from auth)
# ============================================
async def get_optional_user_id(
    token: Optional[str] = Depends(
        OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
    )
) -> Optional[uuid.UUID]:
    """
    FastAPI dependency for optional authentication.
    Returns user_id if valid token provided, None otherwise.
    """
    if token is None:
        return None
    
    token_data = decode_access_token(token)
    
    if token_data is None or token_data.user_id is None:
        return None
    
    try:
        return uuid.UUID(token_data.user_id)
    except ValueError:
        return None
