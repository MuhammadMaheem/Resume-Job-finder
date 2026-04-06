from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Job, Resume, JobStatus
from services.groq_ai import GroqAI
from services.job_search import JobSearch
from config import get_settings
from datetime import datetime

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

groq_ai = GroqAI()
job_search = JobSearch()

scheduler = BackgroundScheduler()


async def scan_jobs_for_user(user_id: int, resume_id: int, location: str = "Remote"):
    """Scan for new jobs for a specific user."""
    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or not resume.analysis:
            return

        queries = groq_ai.search_jobs_query(resume.analysis, location)
        raw_jobs = await job_search.search_multiple_queries(queries, location)

        for raw_job in raw_jobs[:10]:
            match_data = groq_ai.match_job_to_resume(raw_job.get("description", ""), resume.analysis)
            if match_data and match_data.get("match_score", 0) >= 70:
                existing = db.query(Job).filter(
                    Job.user_id == user_id,
                    Job.title == raw_job.get("title"),
                    Job.company == raw_job.get("company"),
                ).first()

                if not existing:
                    new_job = Job(
                        user_id=user_id,
                        resume_id=resume_id,
                        title=raw_job.get("title", ""),
                        company=raw_job.get("company", ""),
                        location=raw_job.get("location", ""),
                        description=raw_job.get("description", ""),
                        match_score=match_data.get("match_score", 0),
                        match_reasons=match_data.get("match_reasons", []),
                        missing_skills=match_data.get("missing_skills", []),
                        application_url=raw_job.get("application_url", ""),
                        source=raw_job.get("source", ""),
                        status=JobStatus.NEW,
                    )
                    db.add(new_job)
                    print(f"Found new job: {raw_job.get('title')} at {raw_job.get('company')}")

        db.commit()
    except Exception as e:
        print(f"Error in scheduled scan: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background job scheduler."""
    scheduler.start()
    print("Background job scheduler started")


def stop_scheduler():
    """Stop the background job scheduler."""
    scheduler.shutdown()
