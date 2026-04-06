from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
import re


# User schemas
class UserCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    notification_email: Optional[str] = None
    notification_enabled: Optional[bool] = False

    @field_validator('email', 'notification_email')
    @classmethod
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v


class UserResponse(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[str]
    notification_email: Optional[str]
    notification_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Resume schemas
class ManualProfile(BaseModel):
    additional_skills: Optional[List[str]] = []
    projects: Optional[List[dict]] = []
    education_details: Optional[str] = ""
    experience_details: Optional[str] = ""
    certifications: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    preferred_job_titles: Optional[List[str]] = []
    preferred_locations: Optional[List[str]] = []
    preferred_job_type: Optional[str] = "Remote"
    career_objective: Optional[str] = ""
    github_url: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    portfolio_url: Optional[str] = ""
    other_notes: Optional[str] = ""


class ResumeUpload(BaseModel):
    filename: str
    analysis: Optional[dict] = None
    manual_profile: Optional[ManualProfile] = None


class ResumeResponse(BaseModel):
    id: int
    filename: str
    raw_text: Optional[str]
    analysis: Optional[dict]
    manual_profile: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


# Resume Comparison
class ResumeComparisonResponse(BaseModel):
    resumes: List[ResumeResponse]
    comparison: Optional[dict] = None


# Job schemas
class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    job_type: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: Optional[str]
    salary_period: Optional[str]
    description: Optional[str]
    requirements: Optional[list]
    match_score: Optional[float]
    match_reasons: Optional[list]
    missing_skills: Optional[list]
    application_url: str
    source: Optional[str]
    status: Optional[str] = None
    ease_of_apply: Optional[float]
    posted_date: Optional[datetime]
    created_at: datetime
    applied_at: Optional[datetime]
    selected_for_bulk: Optional[bool]

    @field_validator('status', mode='before')
    @classmethod
    def serialize_status(cls, v):
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v else None

    class Config:
        from_attributes = True


class JobStatusUpdate(BaseModel):
    status: str


class JobScanRequest(BaseModel):
    resume_id: int
    location: Optional[str] = "Remote"
    max_results: Optional[int] = 20

    @field_validator('max_results')
    @classmethod
    def validate_max_results(cls, v):
        if v is not None and (v < 1 or v > 50):
            raise ValueError('max_results must be between 1 and 50')
        return v


class BulkStatusUpdate(BaseModel):
    status: str
    job_ids: Optional[List[int]] = None  # If empty, use all selected_for_bulk=True


# Cover letter schemas
class CoverLetterResponse(BaseModel):
    id: int
    job_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class CoverLetterGenerate(BaseModel):
    job_id: int


# Interview Question schemas
class InterviewQuestionResponse(BaseModel):
    id: int
    job_id: int
    category: Optional[str]
    question: str
    suggested_answer: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewQuestionGenerate(BaseModel):
    job_id: int


# Networking schemas
class NetworkingSuggestionResponse(BaseModel):
    id: int
    job_id: int
    company: str
    role: Optional[str]
    linkedin_url: Optional[str]
    suggestion: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NetworkingGenerate(BaseModel):
    job_id: int


# Resume Improvement schemas
class ResumeImprovementResponse(BaseModel):
    missing_keywords: Optional[List[str]] = None
    skill_gaps: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    recommended_certifications: Optional[List[str]] = None
    trending_skills: Optional[List[str]] = None


# Resume Rewriter schemas
class ResumeRewriterRequest(BaseModel):
    resume_id: int
    job_id: int


class ResumeRewriterResponse(BaseModel):
    original_resume_id: int
    tailored_resume_text: str
    tailored_summary: str


# Search History schemas
class SearchHistoryResponse(BaseModel):
    id: int
    user_id: int
    resume_id: Optional[int]
    location: str
    queries_used: Optional[list]
    results_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics schemas
class AnalyticsResponse(BaseModel):
    total_applications: int
    status_breakdown: dict
    avg_match_score: float
    applications_over_time: list  # {date, count}
    top_companies: list  # {company, count}
    top_locations: list  # {location, count}
    avg_salary_min: Optional[float]
    avg_salary_max: Optional[float]


# User Notification settings
class NotificationSettings(BaseModel):
    notification_email: Optional[str] = None
    notification_enabled: Optional[bool] = True
