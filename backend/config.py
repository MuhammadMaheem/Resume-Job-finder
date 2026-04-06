from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    GROQ_API_KEY: str
    SERPAPI_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./resume_chatbot.db"
    JOB_SCAN_INTERVAL_MINUTES: int = 60
    APP_NAME: str = "Resume Job Matcher AI"
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000"
    MAX_RESULTS_LIMIT: int = 50

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
