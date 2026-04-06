from http.server import SimpleHTTPRequestHandler
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from services.resume_parser import ResumeParser
from services.groq_ai import GroqAI
from services.job_search import JobSearch
from database import get_db
from models import User, Resume, Job, CoverLetter, JobStatus, InterviewQuestion, NetworkingSuggestion
from sqlalchemy import text

resume_parser = ResumeParser()
groq_ai = GroqAI()
job_search = JobSearch()

def read_body(request):
    """Read request body."""
    content_length = int(request.headers.get('Content-Length', 0))
    if content_length:
        return request.body.read(content_length)
    return b''

def read_multipart(request):
    """Parse multipart form data for file uploads."""
    import io
    from email.parser import Parser
    
    content_type = request.headers.get('Content-Type', '')
    if 'multipart/form-data' not in content_type:
        return None, None
    
    body = read_body(request)
    
    # Extract boundary
    boundary = content_type.split('boundary=')[1].encode()
    parts = body.split(b'--' + boundary)
    
    filename = None
    file_content = None
    manual_profile = None
    
    for part in parts:
        if b'filename=' in part:
            # Extract filename
            filename_start = part.find(b'filename="') + 10
            filename_end = part.find(b'"', filename_start)
            filename = part[filename_start:filename_end].decode('utf-8')
            
            # Find file content (after double newline)
            content_start = part.find(b'\r\n\r\n', filename_end) + 4
            # Remove trailing boundary markers
            content = part[content_start:]
            if content.endswith(b'\r\n'):
                content = content[:-2]
            if content.endswith(b'--'):
                content = content[:-2]
            file_content = content
        elif b'name="manual_profile"' in part:
            content_start = part.find(b'\r\n\r\n') + 4
            content = part[content_start:]
            if content.endswith(b'\r\n'):
                content = content[:-2]
            if content.endswith(b'--'):
                content = content[:-2]
            try:
                manual_profile = json.loads(content.decode('utf-8'))
            except:
                pass
    
    return (filename, file_content), manual_profile

def json_response(data, status=200):
    """Create JSON response."""
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": json.dumps(data)
    }

def options_response():
    """Handle CORS preflight."""
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        "body": ""
    }

def handler(request):
    """Vercel serverless handler."""
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return options_response()
    
    path = request.path
    method = request.method
    
    try:
        # Parse path
        parts = path.strip('/').split('/')
        
        # Route: POST /api/users
        if method == "POST" and parts == ['api', 'users']:
            return create_user(request)
        
        # Route: GET /api/users/{user_id}
        elif method == "GET" and len(parts) == 3 and parts[1] == 'users':
            return get_user(parts[2])
        
        # Route: POST /api/resumes/{user_id}/upload
        elif method == "POST" and len(parts) == 4 and parts[1] == 'resumes' and parts[3] == 'upload':
            return upload_resume(parts[2], request)
        
        # Route: GET /api/resumes/{resume_id}
        elif method == "GET" and len(parts) == 3 and parts[1] == 'resumes':
            return get_resume(parts[2])
        
        # Route: GET /api/users/{user_id}/resumes
        elif method == "GET" and len(parts) == 4 and parts[1] == 'users' and parts[3] == 'resumes':
            return get_user_resumes(parts[2])
        
        # Route: PUT /api/resumes/{resume_id}/profile
        elif method == "PUT" and len(parts) == 4 and parts[1] == 'resumes' and parts[3] == 'profile':
            return update_profile(parts[2], request)
        
        # Route: DELETE /api/resumes/{resume_id}
        elif method == "DELETE" and len(parts) == 3 and parts[1] == 'resumes':
            return delete_resume(parts[2])
        
        # Route: POST /api/jobs/scan
        elif method == "POST" and parts == ['api', 'jobs', 'scan']:
            return scan_jobs(request)
        
        # Route: GET /api/users/{user_id}/jobs
        elif method == "GET" and len(parts) == 4 and parts[1] == 'users' and parts[3] == 'jobs':
            query = parse_qs(urlparse(path).query)
            return get_user_jobs(parts[2], query)
        
        # Route: GET /api/users/{user_id}/jobs/top
        elif method == "GET" and len(parts) == 5 and parts[3] == 'jobs' and parts[4] == 'top':
            query = parse_qs(urlparse(path).query)
            return get_top_jobs(parts[2], query)
        
        # Route: PATCH /api/jobs/{job_id}/status
        elif method == "PATCH" and len(parts) == 4 and parts[1] == 'jobs' and parts[3] == 'status':
            return update_job_status(parts[2], request)
        
        # Route: POST /api/jobs/bulk-status
        elif method == "POST" and parts == ['api', 'jobs', 'bulk-status']:
            return bulk_update_status(request)
        
        # Route: POST /api/jobs/{job_id}/select-bulk
        elif method == "POST" and len(parts) == 5 and parts[1] == 'jobs' and parts[3] == 'select-bulk':
            return toggle_bulk(parts[2])
        
        # Route: GET /api/jobs/{job_id}/interview-questions
        elif method == "GET" and len(parts) == 5 and parts[1] == 'jobs' and parts[3] == 'interview-questions':
            return get_interview_questions(parts[2])
        
        # Route: POST /api/interview-questions/generate
        elif method == "POST" and parts == ['api', 'interview-questions', 'generate']:
            return generate_interview_questions(request)
        
        # Route: GET /api/jobs/{job_id}/networking
        elif method == "GET" and len(parts) == 5 and parts[1] == 'jobs' and parts[3] == 'networking':
            return get_networking(parts[2])
        
        # Route: POST /api/networking/generate
        elif method == "POST" and parts == ['api', 'networking', 'generate']:
            return generate_networking(request)
        
        # Route: POST /api/cover-letters/generate
        elif method == "POST" and parts == ['api', 'cover-letters', 'generate']:
            return generate_cover_letter(request)
        
        # Route: GET /api/jobs/{job_id}/cover-letters
        elif method == "GET" and len(parts) == 5 and parts[1] == 'jobs' and parts[3] == 'cover-letters':
            return get_cover_letters(parts[2])
        
        # Route: POST /api/resumes/{resume_id}/improvements
        elif method == "POST" and len(parts) == 5 and parts[1] == 'resumes' and parts[3] == 'improvements':
            query = parse_qs(urlparse(path).query)
            return get_improvements(parts[2], query)
        
        # Route: GET /api/resumes/{resume_id}/export-pdf
        elif method == "GET" and len(parts) == 5 and parts[1] == 'resumes' and parts[3] == 'export-pdf':
            return export_pdf(parts[2])
        
        # Route: GET /api/users/{user_id}/resumes/compare
        elif method == "GET" and len(parts) == 5 and parts[1] == 'users' and parts[3] == 'resumes' and parts[4] == 'compare':
            return compare_resumes(parts[2])
        
        # Route: GET /api/users/{user_id}/analytics
        elif method == "GET" and len(parts) == 4 and parts[1] == 'users' and parts[3] == 'analytics':
            return get_analytics(parts[2])
        
        # Route: PATCH /api/users/{user_id}/notifications
        elif method == "PATCH" and len(parts) == 4 and parts[1] == 'users' and parts[3] == 'notifications':
            return update_notifications(parts[2], request)
        
        # Route: POST /api/resumes/rewrite
        elif method == "POST" and parts == ['api', 'resumes', 'rewrite']:
            return rewrite_resume(request)
        
        # Route: GET /api/health
        elif method == "GET" and parts == ['api', 'health']:
            return json_response({"status": "ok", "app": "Resume Job Matcher AI"})
        
        # Route: GET /api/users/{user_id}/search-history
        elif method == "GET" and len(parts) == 5 and parts[1] == 'users' and parts[3] == 'search-history':
            return json_response([])  # Placeholder
        
        else:
            return json_response({"error": "Not found"}, 404)
    
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return json_response({"detail": str(e)}, 500)


# ========== Route Handlers ==========

def create_user(request):
    """POST /api/users"""
    try:
        body = json.loads(read_body(request).decode())
    except:
        body = {}
    
    with next(get_db()) as db:
        user = User(name=body.get('name'), email=body.get('email'))
        db.add(user)
        db.commit()
        db.refresh(user)
        return json_response({
            "id": user.id, "name": user.name, "email": user.email,
            "notification_email": user.notification_email,
            "notification_enabled": user.notification_enabled,
            "created_at": str(user.created_at)
        })

def get_user(user_id):
    """GET /api/users/{id}"""
    with next(get_db()) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return json_response({"detail": "User not found"}, 404)
        return json_response({
            "id": user.id, "name": user.name, "email": user.email,
            "notification_email": user.notification_email,
            "notification_enabled": user.notification_enabled,
            "created_at": str(user.created_at)
        })

def upload_resume(user_id, request):
    """POST /api/resumes/{user_id}/upload"""
    (filename, file_content), manual_profile = read_multipart(request)
    
    if not filename or not file_content:
        return json_response({"detail": "No file uploaded"}, 400)
    
    if not filename.lower().endswith('.pdf'):
        return json_response({"detail": "Only PDF files accepted"}, 400)
    
    with next(get_db()) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return json_response({"detail": "User not found"}, 404)
        
        # Save file temporarily
        safe_name = f"{user_id}_{uuid.uuid4().hex[:12]}.pdf"
        file_path = os.path.join(tempfile.gettempdir(), safe_name)
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Extract text
        raw_text = resume_parser.extract_text(file_path)
        if not raw_text:
            return json_response({"detail": "Could not extract text from PDF"}, 400)
        
        # Analyze
        analysis = groq_ai.analyze_resume(raw_text)
        if not analysis:
            return json_response({"detail": "AI analysis failed"}, 500)
        
        # Save
        resume = Resume(
            user_id=user_id, filename=filename, file_path=file_path,
            raw_text=raw_text, analysis=analysis, manual_profile=manual_profile
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return json_response({
            "id": resume.id, "filename": resume.filename,
            "raw_text": resume.raw_text[:500] + "...",
            "analysis": resume.analysis, "manual_profile": resume.manual_profile,
            "created_at": str(resume.created_at)
        })

def get_resume(resume_id):
    """GET /api/resumes/{id}"""
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return json_response({"detail": "Resume not found"}, 404)
        return json_response({
            "id": resume.id, "filename": resume.filename,
            "raw_text": resume.raw_text[:500] if resume.raw_text else None,
            "analysis": resume.analysis, "manual_profile": resume.manual_profile,
            "created_at": str(resume.created_at)
        })

def get_user_resumes(user_id):
    """GET /api/users/{id}/resumes"""
    with next(get_db()) as db:
        resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
        return json_response([{
            "id": r.id, "filename": r.filename,
            "raw_text": r.raw_text[:200] if r.raw_text else None,
            "analysis": r.analysis, "manual_profile": r.manual_profile,
            "created_at": str(r.created_at)
        } for r in resumes])

def update_profile(resume_id, request):
    """PUT /api/resumes/{id}/profile"""
    try:
        profile = json.loads(read_body(request).decode())
    except:
        return json_response({"detail": "Invalid JSON"}, 400)
    
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return json_response({"detail": "Resume not found"}, 404)
        
        resume.manual_profile = profile
        
        # Re-analyze with combined data
        raw = resume.raw_text or ""
        extra_parts = []
        if profile.get("career_objective"):
            extra_parts.append(f"Career Objective: {profile['career_objective']}")
        if profile.get("additional_skills"):
            extra_parts.append(f"Additional Skills: {', '.join(profile['additional_skills'])}")
        if profile.get("education_details"):
            extra_parts.append(f"Education: {profile['education_details']}")
        if profile.get("experience_details"):
            extra_parts.append(f"Experience: {profile['experience_details']}")
        if profile.get("certifications"):
            extra_parts.append(f"Certifications: {', '.join(profile['certifications'])}")
        if profile.get("languages"):
            extra_parts.append(f"Languages: {', '.join(profile['languages'])}")
        if profile.get("other_notes"):
            extra_parts.append(f"Notes: {profile['other_notes']}")
        
        if extra_parts:
            combined = raw + "\n\n--- ADDITIONAL INFO ---\n" + "\n".join(extra_parts)
            analysis = groq_ai.analyze_resume(combined)
            if analysis:
                resume.analysis = analysis
        
        db.commit()
        db.refresh(resume)
        return json_response({
            "id": resume.id, "filename": resume.filename,
            "raw_text": resume.raw_text[:500] if resume.raw_text else None,
            "analysis": resume.analysis, "manual_profile": resume.manual_profile,
            "created_at": str(resume.created_at)
        })

def delete_resume(resume_id):
    """DELETE /api/resumes/{id}"""
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return json_response({"detail": "Resume not found"}, 404)
        try:
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)
        except:
            pass
        db.delete(resume)
        db.commit()
        return json_response({"message": "Deleted"})

def scan_jobs(request):
    """POST /api/jobs/scan"""
    try:
        body = json.loads(read_body(request).decode())
    except:
        return json_response({"detail": "Invalid JSON"}, 400)
    
    resume_id = body.get("resume_id")
    location = body.get("location", "Remote")
    max_results = min(body.get("max_results", 15), 20)
    
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or not resume.analysis:
            return json_response({"detail": "Resume not found or not analyzed"}, 404)
        
        queries = groq_ai.search_jobs_query(resume.analysis, location)
        raw_jobs = []
        
        # Run sequentially to avoid async issues
        for q in queries[:3]:
            jobs = job_search.search_jobs_serpapi_sync(q.get("query", ""), location, 5)
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
                job = Job(
                    user_id=resume.user_id, resume_id=resume_id,
                    title=raw_job.get("title", ""), company=raw_job.get("company", ""),
                    location=raw_job.get("location", ""), job_type=raw_job.get("job_type", ""),
                    description=raw_job.get("description", ""),
                    match_score=match_data.get("match_score", 0),
                    match_reasons=match_data.get("match_reasons", []),
                    missing_skills=match_data.get("missing_skills", []),
                    application_url=url, source=raw_job.get("source", ""),
                    status=JobStatus.NEW, ease_of_apply=50.0
                )
                db.add(job)
                matched.append(job)
        
        db.commit()
        for j in matched:
            db.refresh(j)
        
        return json_response([serialize_job(j) for j in matched])

def get_user_jobs(user_id, query):
    """GET /api/users/{id}/jobs"""
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
        
        jobs = q.order_by(Job.match_score.desc()).all()
        return json_response([serialize_job(j) for j in jobs])

def get_top_jobs(user_id, query):
    """GET /api/users/{id}/jobs/top"""
    limit = int(query.get("limit", [10])[0])
    with next(get_db()) as db:
        jobs = db.query(Job).filter(Job.user_id == user_id, Job.match_score.isnot(None)).order_by(Job.match_score.desc()).limit(limit).all()
        return json_response([serialize_job(j) for j in jobs])

def update_job_status(job_id, request):
    """PATCH /api/jobs/{id}/status"""
    try:
        body = json.loads(read_body(request).decode())
    except:
        return json_response({"detail": "Invalid JSON"}, 400)
    
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return json_response({"detail": "Job not found"}, 404)
        try:
            job.status = JobStatus(body["status"])
            if body["status"] == "applied":
                job.applied_at = datetime.utcnow()
        except ValueError:
            return json_response({"detail": "Invalid status"}, 400)
        db.commit()
        db.refresh(job)
        return json_response(serialize_job(job))

def bulk_update_status(request):
    """POST /api/jobs/bulk-status"""
    try:
        body = json.loads(read_body(request).decode())
    except:
        return json_response({"detail": "Invalid JSON"}, 400)
    
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
        return json_response({"message": f"Updated {count} jobs"})

def toggle_bulk(job_id):
    """POST /api/jobs/{id}/select-bulk"""
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return json_response({"detail": "Not found"}, 404)
        job.selected_for_bulk = not job.selected_for_bulk
        db.commit()
        return json_response({"selected": job.selected_for_bulk})

def generate_interview_questions(request):
    """POST /api/interview-questions/generate"""
    try:
        body = json.loads(read_body(request).decode())
    except:
        return json_response({"detail": "Invalid JSON"}, 400)
    
    job_id = body.get("job_id")
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return json_response({"detail": "Job not found"}, 404)
        
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
        
        return json_response([serialize_question(iq) for iq in db_questions])

def get_interview_questions(job_id):
    """GET /api/jobs/{id}/interview-questions"""
    with next(get_db()) as db:
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.job_id == job_id).all()
        return json_response([serialize_question(q) for q in questions])

def generate_cover_letter(request):
    """POST /api/cover-letters/generate"""
    try:
        body = json.loads(read_body(request).decode())
    except:
        return json_response({"detail": "Invalid JSON"}, 400)
    
    job_id = body.get("job_id")
    with next(get_db()) as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return json_response({"detail": "Job not found"}, 404)
        resume = db.query(Resume).filter(Resume.id == job.resume_id).first()
        if not resume:
            return json_response({"detail": "Resume not found"}, 404)
        
        content = groq_ai.generate_cover_letter(job.description or "", resume.analysis or {}, job.company, job.title)
        if not content:
            return json_response({"detail": "Failed to generate"}, 500)
        
        cl = CoverLetter(job_id=job_id, content=content)
        db.add(cl)
        db.commit()
        db.refresh(cl)
        return json_response({"id": cl.id, "job_id": cl.job_id, "content": cl.content, "created_at": str(cl.created_at)})

def get_cover_letters(job_id):
    """GET /api/jobs/{id}/cover-letters"""
    with next(get_db()) as db:
        letters = db.query(CoverLetter).filter(CoverLetter.job_id == job_id).all()
        return json_response([{"id": c.id, "job_id": c.job_id, "content": c.content, "created_at": str(c.created_at)} for c in letters])

def get_improvements(resume_id, query):
    """POST /api/resumes/{id}/improvements"""
    titles_param = query.get("target_titles", [None])[0]
    target_jobs = json.loads(titles_param) if titles_param else ["Python Developer", "AI Engineer"]
    
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or not resume.analysis:
            return json_response({"detail": "Resume not analyzed"}, 404)
        
        improvements = groq_ai.suggest_resume_improvements(resume.analysis, target_jobs)
        if not improvements:
            return json_response({"detail": "Failed"}, 500)
        return json_response(improvements)

def compare_resumes(user_id):
    """GET /api/users/{id}/resumes/compare"""
    with next(get_db()) as db:
        resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
        if len(resumes) < 2:
            return json_response({"resumes": [{"id": r.id, "filename": r.filename, "analysis": r.analysis} for r in resumes], "comparison": {"message": "Upload at least 2 resumes"}})
        
        all_skills = [set(r.analysis.get("skills", []) if r.analysis else []) for r in resumes]
        comparison = {
            "common_skills": list(set.intersection(*all_skills)) if all_skills else [],
            "resumes_count": len(resumes),
        }
        return json_response({
            "resumes": [{"id": r.id, "filename": r.filename, "analysis": r.analysis} for r in resumes],
            "comparison": comparison
        })

def get_analytics(user_id):
    """GET /api/users/{id}/analytics"""
    from collections import Counter
    
    with next(get_db()) as db:
        jobs = db.query(Job).filter(Job.user_id == user_id).all()
        
        status_counts = Counter(j.status.value if j.status else "new" for j in jobs)
        scores = [j.match_score for j in jobs if j.match_score is not None]
        avg_match = sum(scores) / len(scores) if scores else 0
        
        company_counts = Counter(j.company for j in jobs)
        location_counts = Counter(j.location for j in jobs if j.location)
        
        return json_response({
            "total_applications": len(jobs),
            "status_breakdown": dict(status_counts),
            "avg_match_score": round(avg_match, 1),
            "applications_over_time": [{"week": "Last 30 days", "count": len(jobs)}],
            "top_companies": [{"company": c, "count": n} for c, n in company_counts.most_common(10)],
            "top_locations": [{"location": l, "count": n} for l, n in location_counts.most_common(10)],
            "avg_salary_min": None, "avg_salary_max": None
        })

def update_notifications(user_id, request):
    """PATCH /api/users/{id}/notifications"""
    try:
        body = json.loads(read_body(request).decode())
    except:
        return json_response({"detail": "Invalid JSON"}, 400)
    
    with next(get_db()) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return json_response({"detail": "User not found"}, 404)
        if "notification_email" in body:
            user.notification_email = body["notification_email"]
        if "notification_enabled" in body:
            user.notification_enabled = body["notification_enabled"]
        db.commit()
        db.refresh(user)
        return json_response({
            "id": user.id, "name": user.name, "email": user.email,
            "notification_email": user.notification_email,
            "notification_enabled": user.notification_enabled,
            "created_at": str(user.created_at)
        })

def rewrite_resume(request):
    """POST /api/resumes/rewrite"""
    try:
        body = json.loads(read_body(request).decode())
    except:
        return json_response({"detail": "Invalid JSON"}, 400)
    
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == body.get("resume_id")).first()
        job = db.query(Job).filter(Job.id == body.get("job_id")).first()
        if not resume or not job:
            return json_response({"detail": "Not found"}, 404)
        
        result = groq_ai.rewrite_resume_for_job(resume.raw_text or "", job.description or "", job.title, job.company)
        return json_response({
            "original_resume_id": resume.id,
            "tailored_resume_text": result.get("tailored_text", ""),
            "tailored_summary": result.get("summary", "")
        })

def export_pdf(resume_id):
    """GET /api/resumes/{id}/export-pdf - Returns JSON with PDF content as base64"""
    from fpdf import FPDF
    
    with next(get_db()) as db:
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or not resume.analysis:
            return json_response({"detail": "Not found"}, 404)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 15, "Resume Analysis Report", 0, 1, "C")
        pdf.ln(5)
        
        a = resume.analysis
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, f"Skills: {len(a.get('skills', []))}\nSeniority: {a.get('seniority_level', 'N/A')}\nSummary: {a.get('summary', '')[:300]}")
        
        import io, base64
        buffer = io.BytesIO()
        pdf.output(buffer)
        buffer.seek(0)
        
        return json_response({
            "filename": f"resume_{resume_id}.pdf",
            "pdf_base64": base64.b64encode(buffer.read()).decode(),
            "message": "Use pdf_base64 to download the PDF file"
        })

# ========== Helper Functions ==========

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
        "ease_of_apply": job.ease_of_apply, "posted_date": str(job.posted_date) if job.posted_date else None,
        "created_at": str(job.created_at), "applied_at": str(job.applied_at) if job.applied_at else None,
        "selected_for_bulk": job.selected_for_bulk
    }

def serialize_question(q):
    return {
        "id": q.id, "job_id": q.job_id, "category": q.category,
        "question": q.question, "suggested_answer": q.suggested_answer,
        "created_at": str(q.created_at)
    }
