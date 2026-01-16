"""
Astro-Soulmate: Application Configuration
Using pydantic-settings for environment management
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    app_name: str = "Astro-Soulmate API"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:astro_pass@localhost:5432/astro_db"
    database_url_sync: str = "postgresql://postgres:astro_pass@localhost:5432/astro_db"
    
    # JWT Auth
    jwt_secret_key: str = "your-super-secret-key-change-in-production-please"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # Google AI
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
