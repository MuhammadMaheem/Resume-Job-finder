from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    GROQ_API_KEY: str
    SERPAPI_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./resume_chatbot.db"
    JOB_SCAN_INTERVAL_MINUTES: int = 60
    APP_NAME: str = "Resume Job Matcher AI"
    DEBUG: bool = False
    CORS_ORIGINS: str = ""  # Will be auto-set to VERCEL_URL if not provided
    MAX_RESULTS_LIMIT: int = 50

    class Config:
        env_file = ".env"

    def get_cors_origins(self) -> str:
        """Get CORS origins - use VERCEL_URL in production, localhost in dev"""
        if self.CORS_ORIGINS and self.CORS_ORIGINS != "*":
            return self.CORS_ORIGINS
        
        # Auto-detect from environment
        vercel_url = os.environ.get("VERCEL_URL")
        if vercel_url:
            return f"https://{vercel_url},https://*.vercel.app"
        
        # Default to localhost for development
        return "http://localhost:3000,http://localhost:5173"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
