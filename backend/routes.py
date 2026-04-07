from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional as Opt
import os
import json
import shutil
import logging
import tempfile
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger('jobmatcher')

from database import get_db
from models import (
    User, Resume, Job, CoverLetter, JobStatus, SearchHistory,
    InterviewQuestion, NetworkingSuggestion
)
from schemas import *
from services.resume_parser import ResumeParser
from services.groq_ai import GroqAI
from services.job_search import JobSearch

router = APIRouter()

# Initialize services
resume_parser = ResumeParser()
groq_ai = GroqAI()
job_search = JobSearch()

# Serverless filesystems (e.g. Vercel) are read-only under the deployment bundle.
# Use the system temp directory for any temporary file operations.
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "resume_chatbot_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ========== USER ENDPOINTS ==========

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email, notification_email=user.notification_email, notification_enabled=user.notification_enabled)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}/notifications", response_model=UserResponse)
def update_notifications(user_id: int, settings: NotificationSettings, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if settings.notification_email is not None:
        user.notification_email = settings.notification_email
    if settings.notification_enabled is not None:
        user.notification_enabled = settings.notification_enabled
    db.commit()
    db.refresh(user)
    return user


# ========== RESUME ENDPOINTS ==========

@router.post("/resumes/{user_id}/upload", response_model=ResumeResponse)
async def upload_resume(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Read file content to validate size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")

    # Sanitize filename
    import uuid
    safe_filename = f"{user_id}_{uuid.uuid4().hex}.pdf"
    # Parse PDF directly from bytes to avoid write failures on read-only filesystems.
    raw_text = resume_parser.extract_text_from_bytes(content)
    if not raw_text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF. The file may be image-based or corrupted.")

    analysis = groq_ai.analyze_resume(raw_text)
    if not analysis:
        raise HTTPException(status_code=500, detail="Failed to analyze resume with AI. Please try again.")

    # Keep a logical reference path for compatibility with existing DB schema.
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    db_resume = Resume(user_id=user_id, filename=file.filename, file_path=file_path, raw_text=raw_text, analysis=analysis)
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume


@router.put("/resumes/{resume_id}/profile", response_model=ResumeResponse)
def update_resume_profile(resume_id: int, manual_profile: ManualProfile, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    manual_data = manual_profile.model_dump()
    resume.manual_profile = manual_data

    raw = resume.raw_text or ""
    extra_parts = []
    if manual_data.get("career_objective"):
        extra_parts.append(f"Career Objective: {manual_data['career_objective']}")
    if manual_data.get("additional_skills"):
        extra_parts.append(f"Additional Skills: {', '.join(manual_data['additional_skills'])}")
    if manual_data.get("projects"):
        proj_lines = [f"- {p['name']}: {p.get('description','')} (Tech: {p.get('technologies','')})" for p in manual_data["projects"] if isinstance(p, dict) and p.get("name")]
        if proj_lines:
            extra_parts.append("Projects:\n" + "\n".join(proj_lines))
    if manual_data.get("education_details"):
        extra_parts.append(f"Education: {manual_data['education_details']}")
    if manual_data.get("experience_details"):
        extra_parts.append(f"Additional Experience: {manual_data['experience_details']}")
    if manual_data.get("certifications"):
        extra_parts.append(f"Certifications: {', '.join(manual_data['certifications'])}")
    if manual_data.get("languages"):
        extra_parts.append(f"Languages: {', '.join(manual_data['languages'])}")
    if manual_data.get("other_notes"):
        extra_parts.append(f"Notes: {manual_data['other_notes']}")

    if extra_parts:
        combined = raw + "\n\n--- ADDITIONAL USER INFORMATION ---\n" + "\n".join(extra_parts)
        analysis = groq_ai.analyze_resume(combined)
        if analysis:
            resume.analysis = analysis

    db.commit()
    db.refresh(resume)
    return resume


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.get("/users/{user_id}/resumes", response_model=List[ResumeResponse])
def get_user_resumes(user_id: int, db: Session = Depends(get_db)):
    return db.query(Resume).filter(Resume.user_id == user_id).all()


@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    # Delete file (ignore errors)
    try:
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
    except OSError as e:
        logger.warning(f"Failed to delete resume file {resume.file_path}: {e}")
    db.delete(resume)
    db.commit()
    return {"message": "Resume deleted"}


# ========== FEATURE 7: RESUME COMPARISON ==========

@router.get("/users/{user_id}/resumes/compare", response_model=ResumeComparisonResponse)
def compare_resumes(user_id: int, db: Session = Depends(get_db)):
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    if len(resumes) < 2:
        return ResumeComparisonResponse(resumes=resumes, comparison={"message": "Upload at least 2 resumes to compare"})

    comparison = {
        "message": "Comparison across your resumes",
        "resumes_count": len(resumes),
        "common_skills": [],
        "unique_skills_per_resume": [],
    }

    all_skills = [set(r.analysis.get("skills", []) if r.analysis else []) for r in resumes]
    comparison["common_skills"] = list(set.intersection(*all_skills)) if all_skills else []
    comparison["unique_skills_per_resume"] = [
        {"resume_id": r.id, "filename": r.filename, "unique_skills": list(all_skills[i] - set.intersection(*all_skills))}
        for i, r in enumerate(resumes)
    ]

    return ResumeComparisonResponse(resumes=resumes, comparison=comparison)


# ========== JOB ENDPOINTS ==========

@router.post("/jobs/scan", response_model=List[JobResponse])
async def scan_for_jobs(request: JobScanRequest, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.analysis:
        raise HTTPException(status_code=400, detail="Resume has not been analyzed yet")

    queries = groq_ai.search_jobs_query(resume.analysis, request.location)
    raw_jobs = await job_search.search_multiple_queries(queries, request.location)

    matched_jobs = []
    for raw_job in raw_jobs[:request.max_results]:
        match_data = groq_ai.match_job_to_resume(raw_job.get("description", ""), resume.analysis)
        if match_data:
            # Calculate ease of apply based on application URL quality and source
            ease = 50.0
            url = raw_job.get("application_url", "")
            if "linkedin.com" in url or "indeed.com" in url:
                ease = 80.0
            elif url and len(url) > 10:
                ease = 65.0

            db_job = Job(
                user_id=resume.user_id, resume_id=request.resume_id,
                title=raw_job.get("title", ""), company=raw_job.get("company", ""),
                location=raw_job.get("location", ""), job_type=raw_job.get("job_type", ""),
                description=raw_job.get("description", ""),
                requirements=raw_job.get("requirements", []),
                match_score=match_data.get("match_score", 0),
                match_reasons=match_data.get("match_reasons", []),
                missing_skills=match_data.get("missing_skills", []),
                application_url=raw_job.get("application_url", ""),
                source=raw_job.get("source", ""), status=JobStatus.NEW,
                ease_of_apply=ease,
            )
            db.add(db_job)
            matched_jobs.append(db_job)

    # Save search history
    search = SearchHistory(
        user_id=resume.user_id, resume_id=request.resume_id,
        location=request.location, queries_used=queries,
        results_count=len(matched_jobs),
    )
    db.add(search)
    db.commit()
    for job in matched_jobs:
        db.refresh(job)

    return matched_jobs


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/users/{user_id}/jobs", response_model=List[JobResponse])
def get_user_jobs(user_id: int, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), min_match: Opt[int] = None, job_type: Opt[str] = None, company: Opt[str] = None, db: Session = Depends(get_db)):
    query = db.query(Job).filter(Job.user_id == user_id)
    if min_match:
        query = query.filter(Job.match_score >= min_match)
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if company:
        query = query.filter(Job.company.ilike(f"%{company[:50]}%"))  # Limit length
    return query.order_by(Job.match_score.desc()).offset(skip).limit(limit).all()


@router.get("/users/{user_id}/jobs/top", response_model=List[JobResponse])
def get_top_jobs(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Job).filter(Job.user_id == user_id, Job.match_score.isnot(None)).order_by(Job.match_score.desc()).limit(limit).all()


# FEATURE 11: AUTO-APPLY SUGGESTIONS
@router.get("/users/{user_id}/jobs/easy-apply", response_model=List[JobResponse])
def get_easy_apply_jobs(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Job).filter(Job.user_id == user_id, Job.ease_of_apply.isnot(None)).order_by(Job.ease_of_apply.desc()).limit(limit).all()


@router.patch("/jobs/{job_id}/status", response_model=JobResponse)
def update_job_status(job_id: int, status_update: JobStatusUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        job.status = JobStatus(status_update.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status_update.status}")
    if status_update.status == "applied":
        job.applied_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job


# FEATURE 4: BULK STATUS UPDATE
@router.post("/jobs/bulk-status", response_model=dict)
def bulk_update_status(update: BulkStatusUpdate, db: Session = Depends(get_db)):
    if update.job_ids:
        jobs = db.query(Job).filter(Job.id.in_(update.job_ids)).all()
    else:
        jobs = db.query(Job).filter(Job.selected_for_bulk == True).all()

    for job in jobs:
        try:
            job.status = JobStatus(update.status)
            if update.status == "applied":
                job.applied_at = datetime.utcnow()
            job.selected_for_bulk = False
        except ValueError:
            pass

    db.commit()
    return {"message": f"Updated {len(jobs)} jobs to '{update.status}'"}


@router.post("/jobs/{job_id}/select-bulk")
def toggle_bulk_select(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.selected_for_bulk = not job.selected_for_bulk
    db.commit()
    return {"selected": job.selected_for_bulk}


# FEATURE 10: INTERVIEW PREP
@router.post("/interview-questions/generate", response_model=List[InterviewQuestionResponse])
def generate_interview_questions(request: InterviewQuestionGenerate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume = db.query(Resume).filter(Resume.id == job.resume_id).first() if job.resume_id else None
    resume_text = f"\nCandidate Profile:\n{json.dumps(resume.analysis, indent=2)}" if resume and resume.analysis else ""

    questions = groq_ai.generate_interview_questions(job.description or "", job.title, job.company, resume_text)

    db_questions = []
    for q in questions:
        db_q = InterviewQuestion(
            job_id=job.id, category=q.get("category", "general"),
            question=q.get("question", ""), suggested_answer=q.get("suggested_answer", ""),
        )
        db.add(db_q)
        db_questions.append(db_q)

    db.commit()
    for dq in db_questions:
        db.refresh(dq)

    return db_questions


@router.get("/jobs/{job_id}/interview-questions", response_model=List[InterviewQuestionResponse])
def get_interview_questions(job_id: int, db: Session = Depends(get_db)):
    return db.query(InterviewQuestion).filter(InterviewQuestion.job_id == job_id).all()


# FEATURE 15: NETWORKING SUGGESTIONS
@router.post("/networking/generate", response_model=List[NetworkingSuggestionResponse])
def generate_networking(request: NetworkingGenerate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    suggestions = groq_ai.generate_networking_suggestions(job.company, job.title, job.description or "")

    db_suggestions = []
    for s in suggestions:
        db_s = NetworkingSuggestion(
            job_id=job.id, company=s.get("company", job.company),
            role=s.get("role", ""), linkedin_url=s.get("linkedin_url", ""),
            suggestion=s.get("suggestion", ""),
        )
        db.add(db_s)
        db_suggestions.append(db_s)

    db.commit()
    for ds in db_suggestions:
        db.refresh(ds)

    return db_suggestions


@router.get("/jobs/{job_id}/networking", response_model=List[NetworkingSuggestionResponse])
def get_networking(job_id: int, db: Session = Depends(get_db)):
    return db.query(NetworkingSuggestion).filter(NetworkingSuggestion.job_id == job_id).all()


# FEATURE 14: RESUME REWRITER
@router.post("/resumes/rewrite", response_model=ResumeRewriterResponse)
def rewrite_resume(request: ResumeRewriterRequest, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = groq_ai.rewrite_resume_for_job(resume.raw_text or "", job.description or "", job.title, job.company)

    return ResumeRewriterResponse(
        original_resume_id=resume.id,
        tailored_resume_text=result.get("tailored_text", ""),
        tailored_summary=result.get("summary", ""),
    )


# ========== SEARCH HISTORY (FEATURE 2) ==========

@router.get("/users/{user_id}/search-history", response_model=List[SearchHistoryResponse])
def get_search_history(user_id: int, db: Session = Depends(get_db)):
    return db.query(SearchHistory).filter(SearchHistory.user_id == user_id).order_by(SearchHistory.created_at.desc()).all()


# ========== ANALYTICS (FEATURE 12) ==========

@router.get("/users/{user_id}/analytics", response_model=AnalyticsResponse)
def get_analytics(user_id: int, db: Session = Depends(get_db)):
    jobs = db.query(Job).filter(Job.user_id == user_id).all()

    # Status breakdown
    status_counts = Counter(j.status.value if j.status else "new" for j in jobs)

    # Applications over time (last 30 days, grouped by week)
    now = datetime.utcnow()
    applications_over_time = []
    for i in range(3, -1, -1):
        end_date = now - timedelta(days=i * 7)
        start_date = end_date - timedelta(days=7)
        count = sum(1 for j in jobs if j.created_at and start_date <= j.created_at <= end_date)
        applications_over_time.append({"week": f"Week {4 - i}", "start": start_date.strftime("%Y-%m-%d"), "count": count})

    # Top companies
    company_counts = Counter(j.company for j in jobs)
    top_companies = [{"company": c, "count": n} for c, n in company_counts.most_common(10)]

    # Top locations
    location_counts = Counter(j.location for j in jobs if j.location)
    top_locations = [{"location": loc, "count": n} for loc, n in location_counts.most_common(10)]

    # Salary averages
    salaries = [(j.salary_min, j.salary_max) for j in jobs if j.salary_min or j.salary_max]
    avg_min = sum(s[0] for s in salaries if s[0]) / len([s for s in salaries if s[0]]) if salaries else None
    avg_max = sum(s[1] for s in salaries if s[1]) / len([s for s in salaries if s[1]]) if salaries else None

    # Average match score
    scores = [j.match_score for j in jobs if j.match_score is not None]
    avg_match = sum(scores) / len(scores) if scores else 0

    return AnalyticsResponse(
        total_applications=len(jobs),
        status_breakdown=dict(status_counts),
        avg_match_score=round(avg_match, 1),
        applications_over_time=applications_over_time,
        top_companies=top_companies,
        top_locations=top_locations,
        avg_salary_min=avg_min,
        avg_salary_max=avg_max,
    )


# ========== COVER LETTER ENDPOINTS ==========

@router.post("/cover-letters/generate", response_model=CoverLetterResponse)
def generate_cover_letter(request: CoverLetterGenerate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume = db.query(Resume).filter(Resume.id == job.resume_id).first() if job.resume_id else None
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    content = groq_ai.generate_cover_letter(job.description or "", resume.analysis or {}, job.company, job.title)
    if not content:
        raise HTTPException(status_code=500, detail="Failed to generate cover letter")

    db_cover = CoverLetter(job_id=job.id, content=content)
    db.add(db_cover)
    db.commit()
    db.refresh(db_cover)
    return db_cover


@router.get("/jobs/{job_id}/cover-letters", response_model=List[CoverLetterResponse])
def get_cover_letters(job_id: int, db: Session = Depends(get_db)):
    return db.query(CoverLetter).filter(CoverLetter.job_id == job_id).all()


# ========== RESUME IMPROVEMENT ENDPOINTS ==========

@router.post("/resumes/{resume_id}/improvements", response_model=ResumeImprovementResponse)
def get_resume_improvements(resume_id: int, target_titles: Opt[str] = Query(default=None), db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.analysis:
        raise HTTPException(status_code=400, detail="Resume has not been analyzed yet")

    if target_titles:
        try:
            target_jobs = json.loads(target_titles)
        except json.JSONDecodeError:
            target_jobs = [t.strip() for t in target_titles.split(",")]
    else:
        target_jobs = ["Software Engineer", "Full Stack Developer"]

    improvements = groq_ai.suggest_resume_improvements(resume.analysis, target_jobs)
    if not improvements:
        raise HTTPException(status_code=500, detail="Failed to generate improvements")

    return improvements


# FEATURE 1: EXPORT RESUME ANALYSIS AS PDF
@router.get("/resumes/{resume_id}/export-pdf")
def export_resume_pdf(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.analysis:
        raise HTTPException(status_code=400, detail="Resume not analyzed yet")

    from fpdf import FPDF
    import unicodedata

    def sanitize(text):
        """Replace unsupported Unicode characters with ASCII equivalents."""
        if not text:
            return ""
        # Replace em/en dashes, smart quotes, bullets
        replacements = {
            '\u2014': '--', '\u2013': '-', '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"', '\u2022': '-', '\u2026': '...',
            '\u00b7': '-', '\u201a': ',', '\u201e': '"',
        }
        for uni, ascii in replacements.items():
            text = text.replace(uni, ascii)
        # Replace any remaining non-latin-1 chars
        text = text.encode('latin-1', errors='replace').decode('latin-1')
        return text

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 64, 175)
    pdf.cell(0, 15, "Resume Analysis Report", 0, 1, "C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} | File: {resume.filename}", 0, 1, "C")
    pdf.ln(5)

    a = resume.analysis

    def section(title):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 10, title, 0, 1)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

    def body(text):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, sanitize(text))
        pdf.ln(4)

    # Summary
    section("Professional Summary")
    body(a.get("summary", "N/A"))

    # Overview
    section("Overview")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 7, f"Skills: {len(a.get('skills', []))}  |  Seniority: {a.get('seniority_level', 'N/A')}  |  Experience: {a.get('years_of_experience', 'N/A')} years", 0, 1)
    pdf.ln(4)

    # Skills
    section(f"Skills ({len(a.get('skills', []))})")
    skills = a.get("skills", [])
    body(", ".join(skills))

    # Experience
    if a.get("experience"):
        section("Experience")
        for exp in a["experience"]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(50, 50, 50)
            title = sanitize(f"{exp.get('title', '')} at {exp.get('company', '')}")
            pdf.cell(0, 7, title, 0, 1)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, sanitize(exp.get("duration", "")), 0, 1)
            pdf.ln(2)

    # Education
    if a.get("education"):
        section("Education")
        for edu in a["education"]:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            text = sanitize(f"{edu.get('degree', '')} {edu.get('field', '')} - {edu.get('institution', '')}")
            pdf.cell(0, 7, text, 0, 1)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "Generated by JobMatcher AI - Powered by Groq", 0, 1, "C")

    import uuid
    output_path = os.path.join(UPLOAD_DIR, f"report_{resume_id}_{uuid.uuid4().hex[:8]}.pdf")
    pdf.output(output_path)

    return FileResponse(output_path, media_type="application/pdf", filename=f"resume_analysis_{resume_id}.pdf")
