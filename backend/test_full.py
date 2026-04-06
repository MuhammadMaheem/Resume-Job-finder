#!/usr/bin/env python3
"""Complete end-to-end test of Resume Job Matcher AI."""
import subprocess, sys, time, json, os, signal

BACKEND_DIR = "/home/arthas/Documents/GitHub/Resume-Chatbot/backend"
BASE = "http://127.0.0.1:8000"
RESUME_PATH = "/home/arthas/Documents/GitHub/Resume-Chatbot/muhammad_maheem_resume.pdf"

def run():
    import requests
    
    # Start backend
    print("⏳ Starting backend...")
    proc = subprocess.Popen(
        [f"{BACKEND_DIR}/venv/bin/python", "main.py"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    
    for i in range(10):
        time.sleep(1)
        try:
            r = requests.get(f"{BASE}/api/health", timeout=2)
            if r.status_code == 200:
                print(f"✅ Backend ready: {r.json()}")
                break
        except:
            if i == 9:
                print("❌ Backend failed to start")
                proc.kill()
                sys.exit(1)
    
    # Test 1: Create User
    print("\n=== 1. CREATE USER ===")
    r = requests.post(f"{BASE}/api/users", json={"name": "Muhammad Maheem"})
    print(f"Status: {r.status_code}")
    user = r.json()
    print(f"Response: {json.dumps(user, indent=2)}")
    user_id = user.get("id")
    if not user_id:
        print(f"❌ FAILED — no user ID. Response: {json.dumps(user, indent=2)}")
        proc.kill(); sys.exit(1)
    print(f"✅ User ID: {user_id}")
    
    # Test 2: Upload Resume
    print(f"\n=== 2. UPLOAD RESUME ===")
    with open(RESUME_PATH, "rb") as f:
        r = requests.post(f"{BASE}/api/resumes/{user_id}/upload",
            files={"file": ("resume.pdf", f, "application/pdf")})
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"❌ FAILED: {r.text[:500]}")
        proc.kill(); sys.exit(1)
    data = r.json()
    resume_id = data["id"]
    a = data.get("analysis", {})
    print(f"✅ Uploaded: {data['filename']}")
    print(f"   Resume ID: {resume_id}")
    print(f"   Skills: {len(a.get('skills', []))}")
    print(f"   Seniority: {a.get('seniority_level', '?')}")
    print(f"   Years: {a.get('years_of_experience', '?')}")
    print(f"   Summary: {a.get('summary', '')[:100]}...")
    
    # Test 3: Add Manual Profile
    print(f"\n=== 3. ADD MANUAL PROFILE ===")
    manual = {
        "additional_skills": ["LangChain", "RAG", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scrapy", "Selenium"],
        "projects": [{"name": "AI Resume Job Matcher", "description": "AI platform matching resumes to jobs using LLMs", "technologies": "Python,FastAPI,React,Groq", "url": ""}],
        "education_details": "BSc AI, Superior University, CGPA 3.58/4.0",
        "experience_details": "Frontend Developer at AABS: Next.js 15/React 19 SaaS dashboard",
        "certifications": ["AI/ML courses"],
        "languages": ["English", "Urdu"],
        "preferred_job_titles": ["Python Developer", "AI Engineer", "ML Engineer"],
        "preferred_locations": ["Remote", "Dubai", "UAE"],
        "preferred_job_type": "Remote",
        "career_objective": "Python/AI developer role",
        "github_url": "https://github.com/MuhammadMaheem",
        "linkedin_url": "", "portfolio_url": "", "other_notes": "Passionate about AI"
    }
    r = requests.put(f"{BASE}/api/resumes/{resume_id}/profile", json=manual)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"❌ FAILED: {r.text[:500]}")
        proc.kill(); sys.exit(1)
    pdata = r.json()
    mp = pdata.get("manual_profile")
    print(f"✅ Manual Profile: {'SAVED' if mp else 'MISSING'}")
    print(f"   Skills after merge: {len(pdata.get('analysis', {}).get('skills', []))}")
    
    # Test 4: Scan for Jobs
    print(f"\n=== 4. SCAN FOR JOBS (Real SerpAPI) ===")
    r = requests.post(f"{BASE}/api/jobs/scan",
        json={"resume_id": resume_id, "location": "Remote", "max_results": 10},
        timeout=180)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"❌ FAILED: {r.text[:500]}")
        proc.kill(); sys.exit(1)
    jobs = r.json()
    print(f"✅ Jobs found: {len(jobs)}")
    for i, j in enumerate(jobs[:3]):
        print(f"\n  Job {i+1}: {j['title']} at {j['company']}")
        print(f"  Match: {j['match_score']}% | {j['location']}")
        print(f"  Apply: {j['application_url'][:100]}")
        if j.get('match_reasons'):
            print(f"  Why: {j['match_reasons'][0][:100]}...")
    if len(jobs) > 3:
        print(f"\n  ... and {len(jobs)-3} more")
    
    # Test 5: Resume Improvements
    print(f"\n=== 5. RESUME IMPROVEMENTS ===")
    r = requests.post(f"{BASE}/api/resumes/{resume_id}/improvements",
        params={"target_titles": json.dumps(["Python Developer", "AI Engineer"])})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        imp = r.json()
        if imp.get('suggestions'):
            print(f"✅ {len(imp['suggestions'])} improvement tips")
            for s in imp['suggestions'][:3]:
                print(f"   • {s[:100]}")
        if imp.get('trending_skills'):
            print(f"   Trending: {', '.join(imp['trending_skills'][:5])}")
    
    # Test 6: PDF Export
    print(f"\n=== 6. PDF EXPORT ===")
    r = requests.get(f"{BASE}/api/resumes/{resume_id}/export-pdf")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"✅ PDF generated ({len(r.content)} bytes)")
    else:
        print(f"❌ FAILED: {r.text[:200]}")
    
    # Test 7: Cover Letter
    if jobs:
        print(f"\n=== 7. COVER LETTER ===")
        r = requests.post(f"{BASE}/api/cover-letters/generate",
            json={"job_id": jobs[0]["id"]})
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            cl = r.json()
            print(f"✅ Cover letter generated ({len(cl['content'])} chars)")
            print(f"   Preview: {cl['content'][:100]}...")
        else:
            print(f"❌ FAILED: {r.text[:200]}")
    
    # Test 8: Interview Questions
    if jobs:
        print(f"\n=== 8. INTERVIEW QUESTIONS ===")
        r = requests.post(f"{BASE}/api/interview-questions/generate",
            json={"job_id": jobs[0]["id"]})
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            questions = r.json()
            print(f"✅ {len(questions)} questions generated")
            for q in questions[:2]:
                print(f"   [{q['category']}] {q['question'][:80]}...")
        else:
            print(f"❌ FAILED: {r.text[:200]}")
    
    # Test 9: Job Status Update
    if jobs:
        print(f"\n=== 9. JOB STATUS UPDATE ===")
        r = requests.patch(f"{BASE}/api/jobs/{jobs[0]['id']}/status",
            json={"status": "saved"})
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print(f"✅ Status updated to '{r.json()['status']}'")
    
    # Test 10: Bulk Status
    print(f"\n=== 10. BULK STATUS UPDATE ===")
    r = requests.post(f"{BASE}/api/jobs/{jobs[0]['id']}/select-bulk")
    print(f"Select bulk status: {r.status_code}")
    r2 = requests.post(f"{BASE}/api/jobs/bulk-status",
        json={"status": "applied", "job_ids": [jobs[0]["id"]]})
    print(f"Bulk update: {r2.status_code}")
    if r2.status_code == 200:
        print(f"✅ {r2.json()['message']}")
    
    # Test 11: Analytics
    print(f"\n=== 11. ANALYTICS ===")
    r = requests.get(f"{BASE}/api/users/{user_id}/analytics")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        a = r.json()
        print(f"✅ Total applications: {a['total_applications']}")
        print(f"   Avg match: {a['avg_match_score']}%")
        print(f"   Status: {a['status_breakdown']}")
    
    # Test 12: Resume Comparison (need 2 resumes, skip if only 1)
    print(f"\n=== 12. RESUME COMPARISON ===")
    r = requests.get(f"{BASE}/api/users/{user_id}/resumes/compare")
    print(f"Status: {r.status_code}")
    data = r.json()
    if data.get("comparison"):
        print(f"✅ {data['comparison'].get('message', 'OK')}")
    
    # Cleanup
    proc.terminate()
    
    print(f"\n{'='*50}")
    print(f"🎉 ALL 12 TESTS COMPLETED!")
    print(f"   User: {user_id}")
    print(f"   Resume: {resume_id}")
    print(f"   Jobs: {len(jobs)}")

if __name__ == "__main__":
    run()
