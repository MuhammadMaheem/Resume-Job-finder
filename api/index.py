"""
Vercel Serverless API Handler for Resume Job Matcher AI.
All /api/* requests route here.
"""
import json
import os
import sys
import tempfile
import uuid
import io
import base64
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Setup path
sys.path.insert(0, os.path.dirname(__file__))

def handler(req, res):
    """Vercel serverless handler — defined at top level for Vercel detection."""
    # Lazy imports (avoid DB connection during build)
    from services.resume_parser import ResumeParser
    from services.groq_ai import GroqAI
    from services.job_search import JobSearch
    from database import get_db, init_db
    from models import User, Resume, Job, CoverLetter, JobStatus, InterviewQuestion, NetworkingSuggestion
    from sqlalchemy import text
    from collections import Counter

    # Init services & DB
    resume_parser = ResumeParser()
    groq_ai = GroqAI()
    job_search = JobSearch()
    init_db()

def read_body(req):
    """Read request body from Vercel request object."""
    body = req.get('body', '')
    if isinstance(body, dict):
        return body
    if isinstance(body, str) and body:
        try:
            return json.loads(body)
        except:
            return {}
    # Read from raw body if available
    raw = req.get('_rawBody', '')
    if raw and isinstance(raw, str):
        try:
            return json.loads(raw)
        except:
            return {}
    return {}

def json_response(data, status=200):
    """Return Vercel-compatible JSON response."""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps(data, default=str)
    }

def serialize_job(job):
    return {
        "id": job.id, "title": job.title, "company": job.company,
        "location": job.location, "job_type": job.job_type,
        "salary_min": job.salary_min, "salary_max": job.salary_max,
        "description": job.description[:500] if job.description else None,
        "requirements": job.requirements, "match_score": job.match_score,
        "match_reasons": job.match_reasons, "missing_skills": job.missing_skills,
        "application_url": job.application_url, "source": job.source,
        "status": job.status.value if job.status else "new",
        "ease_of_apply": job.ease_of_apply,
        "created_at": str(job.created_at),
        "selected_for_bulk": job.selected_for_bulk
    }

def handler(req, res):
    """Vercel serverless handler."""
    # Handle CORS preflight
    if req.get('method') == 'OPTIONS':
        return res.status(200).json({})

    method = req.get('method', 'GET')
    path = req.get('path', req.get('url', '/'))
    query = req.get('query', {})

    # Strip /api prefix for routing
    if path.startswith('/api/'):
        route = path[5:]  # Remove '/api/'
    else:
        route = path

    parts = [p for p in route.strip('/').split('/') if p]

    try:
        # === USERS ===
        if method == 'POST' and parts == ['users']:
            return create_user(req, res)
        elif method == 'GET' and len(parts) == 1 and parts[0].startswith('users/'):
            user_id = parts[0].split('/')[-1]
            return get_user(user_id, res)
        elif method == 'PATCH' and len(parts) == 2 and parts[0].startswith('users/') and parts[-1] == 'notifications':
            user_id = parts[0].split('/')[-1]
            return update_notifications(user_id, req, res)

        # === RESUMES ===
        elif method == 'POST' and len(parts) >= 3 and parts[0].startswith('resumes/') and parts[-1] == 'upload':
            user_id = parts[0].split('/')[-1]
            return upload_resume(user_id, req, res)
        elif method == 'GET' and len(parts) == 1 and parts[0].startswith('resumes/'):
            resume_id = parts[0].split('/')[-1]
            return get_resume(resume_id, res)
        elif method == 'PUT' and len(parts) >= 3 and parts[0].startswith('resumes/') and parts[-1] == 'profile':
            resume_id = parts[0].split('/')[-1]
            return update_profile(resume_id, req, res)
        elif method == 'DELETE' and len(parts) == 1 and parts[0].startswith('resumes/'):
            resume_id = parts[0].split('/')[-1]
            return delete_resume(resume_id, res)
        elif method == 'GET' and len(parts) >= 3 and parts[0].startswith('users/') and parts[-1] == 'resumes':
            user_id = parts[0].split('/')[-1]
            return get_user_resumes(user_id, res)
        elif method == 'GET' and len(parts) >= 4 and parts[-1] == 'compare':
            user_id = parts[0].split('/')[-1]
            return compare_resumes(user_id, res)
        elif method == 'POST' and len(parts) >= 3 and parts[-1] == 'improvements':
            resume_id = parts[0].split('/')[-1]
            return get_improvements(resume_id, query, res)
        elif method == 'POST' and parts == ['resumes', 'rewrite']:
            return rewrite_resume(req, res)

        # === JOBS ===
        elif method == 'POST' and parts == ['jobs', 'scan']:
            return scan_jobs(req, res)
        elif method == 'GET' and len(parts) >= 3 and parts[0].startswith('users/') and parts[-1] == 'jobs':
            user_id = parts[0].split('/')[-1]
            return get_user_jobs(user_id, query, res)
        elif method == 'GET' and len(parts) >= 4 and parts[-2] == 'jobs' and parts[-1] == 'top':
            user_id = parts[0].split('/')[-1]
            return get_top_jobs(user_id, query, res)
        elif method == 'PATCH' and len(parts) == 1 and parts[0].startswith('jobs/'):
            job_id = parts[0].split('/')[-2] if '/status' in parts[0] else parts[0].split('/')[-1]
            return update_job_status(job_id, req, res)
        elif method == 'POST' and parts == ['jobs', 'bulk-status']:
            return bulk_update_status(req, res)
        elif method == 'POST' and len(parts) >= 2 and parts[0].startswith('jobs/') and parts[-1] == 'select-bulk':
            job_id = parts[0].split('/')[-2]
            return toggle_bulk(job_id, res)
        elif method == 'GET' and len(parts) >= 3 and parts[0].startswith('jobs/') and parts[-1] == 'interview-questions':
            job_id = parts[0].split('/')[-2]
            return get_interview_questions(job_id, res)
        elif method == 'GET' and len(parts) >= 3 and parts[0].startswith('jobs/') and parts[-1] == 'cover-letters':
            job_id = parts[0].split('/')[-2]
            return get_cover_letters(job_id, res)
        elif method == 'GET' and len(parts) >= 3 and parts[0].startswith('jobs/') and parts[-1] == 'networking':
            job_id = parts[0].split('/')[-2]
            return get_networking(job_id, res)
        elif method == 'GET' and len(parts) >= 3 and parts[0].startswith('users/') and parts[-1] == 'analytics':
            user_id = parts[0].split('/')[-1]
            return get_analytics(user_id, res)
        elif method == 'GET' and len(parts) >= 3 and parts[0].startswith('users/') and parts[-1] == 'search-history':
            return json_response([])

        # === COVER LETTERS ===
        elif method == 'POST' and parts == ['cover-letters', 'generate']:
            return generate_cover_letter(req, res)

        # === INTERVIEW QUESTIONS ===
        elif method == 'POST' and parts == ['interview-questions', 'generate']:
            return generate_interview_questions(req, res)

        # === NETWORKING ===
        elif method == 'POST' and parts == ['networking', 'generate']:
            return generate_networking(req, res)

        # === HEALTH ===
        elif method == 'GET' and parts == ['health']:
            return res.status(200).json({"status": "ok", "app": "Resume Job Matcher AI"})

        # === PDF EXPORT ===
        elif method == 'GET' and len(parts) >= 3 and parts[0].startswith('resumes/') and parts[-1] == 'export-pdf':
            resume_id = parts[0].split('/')[-2]
            return export_pdf(resume_id, res)

        else:
            return res.status(404).json({"error": "Not found"})

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return res.status(500).json({"detail": str(e), "error": True})


# ========== ROUTE HANDLERS ==========

def create_user(req, res):
    body = read_body(req)
    with next(get_db()) as db:
        user = User(name=body.get('name'), email=body.get('email'))
        db.add(user)
        db.commit()
        db.refresh(user)
        return res.status(200).json({
            "id": user.id, "name": user.name, "email": user.email,
            "notification_email": user.notification_email,
            "notification_enabled": user.notification_enabled,
            "created_at": str(user.created_at)
        })

def get_user(user_id, res):
    with next(get_db()) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return res.status(404).json({"detail": "User not found"})
        return res.status(200).json({
            "id": user.id, "name": user.name, "email": user.email,
            "notification_email": user.notification_email,
            "notification_enabled": user.notification_enabled,
            "created_at": str(user.created_at)
        })

def upload_resume(user_id, req, res):
    # For Vercel, file uploads come as base64 or URL
    body = read_body(req)
    file_data = body.get('file')
    manual_profile = body.get('manual_profile')

    if not file_data:
        return res.status(400).json({"detail": "No file provided"})

    # Decode file
    if isinstance(file_data, str) and file_data.startswith('data:'):
        # Data URL
        import base64
        file_content = base64.b64decode(file_data.split(',')[1])
        filename = body.get('filename', 'resume.pdf')
    elif isinstance(file_data, dict):
        return res.status(400).json({"detail": "Send file as base64 data URL or upload via multipart"})
    else:
        return res.status(400).json({"detail": "Invalid file format"})

    if not filename.lower().endswith('.pdf'):
        return res.status(400).json({"detail": "Only PDF files accepted"})

    with next(get_db()) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return res.status(404).json({"detail": "User not found"})

        # Save temp file
        safe_name = f"{user_id}_{uuid.uuid4().hex[:12]}.pdf"
        file_path = os.path.join(tempfile.gettempdir(), safe_name)
        with open(file_path, 'wb') as f:
            f.write(file_content)

        raw_text = resume_parser.extract_text(file_path)
        if not raw_text:
            return res.status(400).json({"detail": "Could not extract text from PDF"})

        analysis = groq_ai.analyze_resume(raw_text)
        if not analysis:
            return res.status(500).json({"detail": "AI analysis failed"})

        resume = Resume(
            user_id=user_id, filename=filename, file_path=file_path,
            raw_text=raw_text, analysis=analysis, manual_profile=manual_profile
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return res.status(200).json({
            "id": resume.id, "filename": resume.filename,
            "raw_text": resume.raw_text[:500] + "..." if resume.raw_text else None,
            "analysis": resume.analysis, "manual_profile": resume.manual_profile,
            "created_at": str(resume.created_at)
        })

def get_resume(resume_id, res):
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return res.status(404).json({"detail": "Resume not found"})
        return res.status(200).json({
            "id": resume.id, "filename": resume.filename,
            "raw_text": resume.raw_text[:500] if resume.raw_text else None,
            "analysis": resume.analysis, "manual_profile": resume.manual_profile,
            "created_at": str(resume.created_at)
        })

def get_user_resumes(user_id, res):
    with next(get_db()) as db:
        resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
        return res.status(200).json([{
            "id": r.id, "filename": r.filename,
            "analysis": r.analysis, "manual_profile": r.manual_profile,
            "created_at": str(r.created_at)
        } for r in resumes])

def update_profile(resume_id, req, res):
    body = read_body(req)
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return res.status(404).json({"detail": "Resume not found"})

        resume.manual_profile = body

        # Re-analyze with combined data
        raw = resume.raw_text or ""
        extra_parts = []
        if body.get("career_objective"):
            extra_parts.append(f"Career Objective: {body['career_objective']}")
        if body.get("additional_skills"):
            extra_parts.append(f"Additional Skills: {', '.join(body['additional_skills'])}")
        if body.get("education_details"):
            extra_parts.append(f"Education: {body['education_details']}")
        if body.get("experience_details"):
            extra_parts.append(f"Experience: {body['experience_details']}")
        if body.get("certifications"):
            extra_parts.append(f"Certifications: {', '.join(body['certifications'])}")
        if body.get("languages"):
            extra_parts.append(f"Languages: {', '.join(body['languages'])}")
        if body.get("other_notes"):
            extra_parts.append(f"Notes: {body['other_notes']}")

        if extra_parts:
            combined = raw + "\n\n--- ADDITIONAL INFO ---\n" + "\n".join(extra_parts)
            analysis = groq_ai.analyze_resume(combined)
            if analysis:
                resume.analysis = analysis

        db.commit()
        db.refresh(resume)
        return res.status(200).json({
            "id": resume.id, "filename": resume.filename,
            "analysis": resume.analysis, "manual_profile": resume.manual_profile,
            "created_at": str(resume.created_at)
        })

def delete_resume(resume_id, res):
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return res.status(404).json({"detail": "Resume not found"})
        try:
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)
        except:
            pass
        db.delete(resume)
        db.commit()
        return res.status(200).json({"message": "Deleted"})

def scan_jobs(req, res):
    body = read_body(req)
    resume_id = body.get("resume_id")
    location = body.get("location", "Remote")
    max_results = min(body.get("max_results", 15), 20)

    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or not resume.analysis:
            return res.status(404).json({"detail": "Resume not found or not analyzed"})

        queries = groq_ai.search_jobs_query(resume.analysis, location)
        raw_jobs = []

        # Run sequentially (Vercel timeout limit)
        for q in queries[:3]:
            jobs = job_search.search_jobs_serpapi_sync(q.get("query", ""), location, 7)
            raw_jobs.extend(jobs)

        matched = []
        seen_urls = set()
        for raw_job in raw_jobs[:max_results]:
            url = raw_job.get("application_url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)

            match_data = groq_ai.match_job_to_resume(raw_job.get("description", ""), resume.analysis)
            if match_data:
                ease = 80.0 if any(x in url for x in ['linkedin', 'indeed']) else 50.0
                job = Job(
                    user_id=resume.user_id, resume_id=resume_id,
                    title=raw_job.get("title", ""), company=raw_job.get("company", ""),
                    location=raw_job.get("location", ""), job_type=raw_job.get("job_type", ""),
                    description=raw_job.get("description", ""),
                    match_score=match_data.get("match_score", 0),
                    match_reasons=match_data.get("match_reasons", []),
                    missing_skills=match_data.get("missing_skills", []),
                    application_url=url, source=raw_job.get("source", ""),
                    status=JobStatus.NEW, ease_of_apply=ease
                )
                db.add(job)
                matched.append(job)

        db.commit()
        for j in matched:
            db.refresh(j)

        return res.status(200).json([serialize_job(j) for j in matched])

def get_user_jobs(user_id, query, res):
    min_match = query.get("min_match", [None])[0]
    job_type = query.get("job_type", [None])[0]
    company = query.get("company", [None])[0]

    with next(get_db()) as db:
        q = db.query(Job).filter(Job.user_id == user_id)
        if min_match:
            q = q.filter(Job.match_score >= int(min_match))
        if job_type:
            q = q.filter(Job.job_type == job_type)
        if company:
            q = q.filter(Job.company.like(f"%{company[:50]}%"))

        jobs = q.order_by(Job.match_score.desc()).limit(100).all()
        return res.status(200).json([serialize_job(j) for j in jobs])

def get_top_jobs(user_id, query, res):
    limit = int(query.get("limit", [10])[0])
    with next(get_db()) as db:
        jobs = db.query(Job).filter(Job.user_id == user_id, Job.match_score.isnot(None)).order_by(Job.match_score.desc()).limit(limit).all()
        return res.status(200).json([serialize_job(j) for j in jobs])

def update_job_status(job_id, req, res):
    body = read_body(req)
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return res.status(404).json({"detail": "Job not found"})
        try:
            job.status = JobStatus(body["status"])
            if body["status"] == "applied":
                job.applied_at = datetime.utcnow()
        except (ValueError, KeyError):
            return res.status(400).json({"detail": "Invalid status"})
        db.commit()
        db.refresh(job)
        return res.status(200).json(serialize_job(job))

def bulk_update_status(req, res):
    body = read_body(req)
    with next(get_db()) as db:
        ids = body.get("job_ids", [])
        if not ids:
            jobs = db.query(Job).filter(Job.selected_for_bulk == True).all()
        else:
            jobs = db.query(Job).filter(Job.id.in_(ids)).all()

        count = 0
        for job in jobs:
            try:
                job.status = JobStatus(body["status"])
                if body["status"] == "applied":
                    job.applied_at = datetime.utcnow()
                job.selected_for_bulk = False
                count += 1
            except:
                pass
        db.commit()
        return res.status(200).json({"message": f"Updated {count} jobs"})

def toggle_bulk(job_id, res):
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return res.status(404).json({"detail": "Not found"})
        job.selected_for_bulk = not job.selected_for_bulk
        db.commit()
        return res.status(200).json({"selected": job.selected_for_bulk})

def generate_interview_questions(req, res):
    body = read_body(req)
    job_id = body.get("job_id")
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return res.status(404).json({"detail": "Job not found"})

        resume = db.query(Resume).filter(Resume.id == job.resume_id).first() if job.resume_id else None
        profile = f"\nCandidate: {json.dumps(resume.analysis)}" if resume and resume.analysis else ""

        questions = groq_ai.generate_interview_questions(job.description or "", job.title, job.company, profile)

        db_questions = []
        for q in questions:
            iq = InterviewQuestion(
                job_id=job_id, category=q.get("category", "general"),
                question=q.get("question", ""), suggested_answer=q.get("suggested_answer", "")
            )
            db.add(iq)
            db_questions.append(iq)
        db.commit()
        for iq in db_questions:
            db.refresh(iq)

        return res.status(200).json([{
            "id": iq.id, "job_id": iq.job_id, "category": iq.category,
            "question": iq.question, "suggested_answer": iq.suggested_answer,
            "created_at": str(iq.created_at)
        } for iq in db_questions])

def get_interview_questions(job_id, res):
    with next(get_db()) as db:
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.job_id == job_id).all()
        return res.status(200).json([{
            "id": q.id, "job_id": q.job_id, "category": q.category,
            "question": q.question, "suggested_answer": q.suggested_answer,
            "created_at": str(q.created_at)
        } for q in questions])

def generate_cover_letter(req, res):
    body = read_body(req)
    job_id = body.get("job_id")
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return res.status(404).json({"detail": "Job not found"})
        resume = db.query(Resume).filter(Resume.id == job.resume_id).first()
        if not resume:
            return res.status(404).json({"detail": "Resume not found"})

        content = groq_ai.generate_cover_letter(job.description or "", resume.analysis or {}, job.company, job.title)
        if not content:
            return res.status(500).json({"detail": "Failed to generate"})

        cl = CoverLetter(job_id=job_id, content=content)
        db.add(cl)
        db.commit()
        db.refresh(cl)
        return res.status(200).json({"id": cl.id, "job_id": cl.job_id, "content": cl.content, "created_at": str(cl.created_at)})

def get_cover_letters(job_id, res):
    with next(get_db()) as db:
        letters = db.query(CoverLetter).filter(CoverLetter.job_id == job_id).all()
        return res.status(200).json([{"id": c.id, "job_id": c.job_id, "content": c.content, "created_at": str(c.created_at)} for c in letters])

def get_improvements(resume_id, query, res):
    titles_param = query.get("target_titles", [None])[0]
    target_jobs = json.loads(titles_param) if titles_param else ["Python Developer", "AI Engineer"]

    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or not resume.analysis:
            return res.status(404).json({"detail": "Resume not analyzed"})

        improvements = groq_ai.suggest_resume_improvements(resume.analysis, target_jobs)
        if not improvements:
            return res.status(500).json({"detail": "Failed"})
        return res.status(200).json(improvements)

def compare_resumes(user_id, res):
    with next(get_db()) as db:
        resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
        if len(resumes) < 2:
            return res.status(200).json({
                "resumes": [{"id": r.id, "filename": r.filename, "analysis": r.analysis} for r in resumes],
                "comparison": {"message": "Upload at least 2 resumes to compare"}
            })

        all_skills = [set(r.analysis.get("skills", []) if r.analysis else []) for r in resumes]
        common = list(set.intersection(*all_skills)) if all_skills else []
        unique = [{"resume_id": r.id, "filename": r.filename, "unique_skills": list(all_skills[i] - set.intersection(*all_skills))} for i, r in enumerate(resumes)]

        return res.status(200).json({
            "resumes": [{"id": r.id, "filename": r.filename, "analysis": r.analysis} for r in resumes],
            "comparison": {"common_skills": common, "unique_per_resume": unique, "resumes_count": len(resumes)}
        })

def get_analytics(user_id, res):
    with next(get_db()) as db:
        jobs = db.query(Job).filter(Job.user_id == user_id).all()

        status_counts = Counter(j.status.value if j.status else "new" for j in jobs)
        scores = [j.match_score for j in jobs if j.match_score is not None]
        avg_match = sum(scores) / len(scores) if scores else 0

        company_counts = Counter(j.company for j in jobs)
        location_counts = Counter(j.location for j in jobs if j.location)

        return res.status(200).json({
            "total_applications": len(jobs),
            "status_breakdown": dict(status_counts),
            "avg_match_score": round(avg_match, 1),
            "applications_over_time": [{"period": "Last 30 days", "count": len(jobs)}],
            "top_companies": [{"company": c, "count": n} for c, n in company_counts.most_common(10)],
            "top_locations": [{"location": l, "count": n} for l, n in location_counts.most_common(10)],
            "avg_salary_min": None, "avg_salary_max": None
        })

def update_notifications(user_id, req, res):
    body = read_body(req)
    with next(get_db()) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return res.status(404).json({"detail": "User not found"})
        if "notification_email" in body:
            user.notification_email = body["notification_email"]
        if "notification_enabled" in body:
            user.notification_enabled = body["notification_enabled"]
        db.commit()
        db.refresh(user)
        return res.status(200).json({
            "id": user.id, "name": user.name, "email": user.email,
            "notification_email": user.notification_email,
            "notification_enabled": user.notification_enabled,
            "created_at": str(user.created_at)
        })

def rewrite_resume(req, res):
    body = read_body(req)
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == body.get("resume_id")).first()
        job = db.query(Job).filter(Job.id == body.get("job_id")).first()
        if not resume or not job:
            return res.status(404).json({"detail": "Not found"})

        result = groq_ai.rewrite_resume_for_job(resume.raw_text or "", job.description or "", job.title, job.company)
        return res.status(200).json({
            "original_resume_id": resume.id,
            "tailored_resume_text": result.get("tailored_text", ""),
            "tailored_summary": result.get("summary", "")
        })

def export_pdf(resume_id, res):
    from fpdf import FPDF

    def sanitize(text):
        if not text: return ""
        replacements = {'\u2014': '--', '\u2013': '-', '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2022': '-', '\u2026': '...'}
        for u, a in replacements.items():
            text = text.replace(u, a)
        return text.encode('latin-1', errors='replace').decode('latin-1')

    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or not resume.analysis:
            return res.status(404).json({"detail": "Not found"})

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 15, "Resume Analysis Report", 0, 1, "C")
        pdf.ln(5)

        a = resume.analysis
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, f"Skills: {len(a.get('skills', []))}\nSeniority: {a.get('seniority_level', 'N/A')}\nSummary: {sanitize(a.get('summary', '')[:300])}")

        buffer = io.BytesIO()
        pdf.output(buffer)
        buffer.seek(0)

        return res.status(200).json({
            "filename": f"resume_{resume_id}.pdf",
            "pdf_base64": base64.b64encode(buffer.read()).decode(),
            "message": "Decode pdf_base64 to download the PDF file"
        })

def generate_networking(req, res):
    body = read_body(req)
    job_id = body.get("job_id")
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return res.status(404).json({"detail": "Job not found"})

        suggestions = groq_ai.generate_networking_suggestions(job.company, job.title, job.description or "")

        db_suggestions = []
        for s in suggestions:
            ns = NetworkingSuggestion(
                job_id=job_id, company=s.get("company", job.company),
                role=s.get("role", ""), linkedin_url=s.get("linkedin_url", ""),
                suggestion=s.get("suggestion", "")
            )
            db.add(ns)
            db_suggestions.append(ns)
        db.commit()
        for ns in db_suggestions:
            db.refresh(ns)

        return res.status(200).json([{
            "id": ns.id, "job_id": ns.job_id, "company": ns.company,
            "role": ns.role, "linkedin_url": ns.linkedin_url,
            "suggestion": ns.suggestion, "created_at": str(ns.created_at)
        } for ns in db_suggestions])

def get_networking(job_id, res):
    with next(get_db()) as db:
        suggestions = db.query(NetworkingSuggestion).filter(NetworkingSuggestion.job_id == job_id).all()
        return res.status(200).json([{
            "id": ns.id, "job_id": ns.job_id, "company": ns.company,
            "role": ns.role, "linkedin_url": ns.linkedin_url,
            "suggestion": ns.suggestion, "created_at": str(ns.created_at)
        } for ns in suggestions])
