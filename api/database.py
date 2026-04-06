from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import os

# Use Neon PostgreSQL (free) for Vercel - falls back to SQLite for local dev
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./resume_chatbot.db")

connect_args = {}
pool_config = {}

if "postgresql" in DATABASE_URL or "postgres" in DATABASE_URL:
    # Neon connection pooling for serverless
    connect_args = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000",  # 30s statement timeout
    }
    pool_config = {
        "poolclass": QueuePool,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,  # Test connection before using
        "pool_recycle": 3600,  # Recycle connections after 1 hour
    }
else:
    # SQLite for local development
    connect_args["check_same_thread"] = False
    pool_config = {"poolclass": NullPool}  # No pooling for SQLite

engine = create_engine(DATABASE_URL, connect_args=connect_args, **pool_config)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

# DO NOT auto-create tables on import — call init_db() inside handler
