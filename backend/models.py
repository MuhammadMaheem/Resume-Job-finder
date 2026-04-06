from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum


class JobStatus(enum.Enum):
    NEW = "new"
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    REJECTED = "rejected"
    OFFER = "offer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, index=True, unique=True)
    notification_email = Column(String(255), nullable=True)
    notification_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    search_history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    raw_text = Column(Text, nullable=True)
    analysis = Column(JSON, nullable=True)
    manual_profile = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="resumes")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    location = Column(String(255), default="Remote")
    queries_used = Column(JSON, nullable=True)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="search_history")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=True, index=True)
    job_type = Column(String(50), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), nullable=True)
    salary_period = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(JSON, nullable=True)
    match_score = Column(Float, nullable=True, index=True)
    match_reasons = Column(JSON, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    application_url = Column(String(1000), nullable=False)
    source = Column(String(100), nullable=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.NEW, index=True)
    ease_of_apply = Column(Float, nullable=True)
    posted_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    applied_at = Column(DateTime, nullable=True)
    selected_for_bulk = Column(Boolean, default=False, index=True)

    user = relationship("User", back_populates="jobs")
    cover_letters = relationship("CoverLetter", back_populates="job", cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="job", cascade="all, delete-orphan")
    networking_suggestions = relationship("NetworkingSuggestion", back_populates="job", cascade="all, delete-orphan")


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="cover_letters")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    question = Column(Text, nullable=False)
    suggested_answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="interview_questions")


class NetworkingSuggestion(Base):
    __tablename__ = "networking_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="networking_suggestions")
