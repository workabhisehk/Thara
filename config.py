"""
Configuration management for the AI Productivity Agent.
Loads settings from environment variables with sensible defaults.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    
    # AI/LLM
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Clean up database_url if it has "DATABASE_URL=" prefix
        if hasattr(self, 'database_url') and self.database_url.startswith("DATABASE_URL="):
            self.database_url = self.database_url.split("=", 1)[1].strip().strip('"').strip("'")
    supabase_url: Optional[str] = Field(None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(None, env="SUPABASE_KEY")
    
    # Google Calendar
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(..., env="GOOGLE_REDIRECT_URI")
    
    # Application
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    timezone: str = Field("UTC", env="TIMEZONE")
    
    # Default Work Hours
    default_work_start_hour: int = Field(8, env="DEFAULT_WORK_START_HOUR")
    default_work_end_hour: int = Field(20, env="DEFAULT_WORK_END_HOUR")
    default_weekend_start_hour: int = Field(10, env="DEFAULT_WEEKEND_START_HOUR")
    default_weekend_end_hour: int = Field(18, env="DEFAULT_WEEKEND_END_HOUR")
    
    # Scheduling
    check_in_interval: int = Field(30, env="CHECK_IN_INTERVAL")
    weekly_review_hour: int = Field(10, env="WEEKLY_REVIEW_HOUR")
    
    # Server
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

