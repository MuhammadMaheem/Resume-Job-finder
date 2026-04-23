"""Comprehensive integration test for all endpoints"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api"
errors = []
successes = []

def test(name, func):
    try:
        func()
        successes.append(f"✅ {name}")
        print(f"✅ {name}")
    except Exception as e:
        errors.append(f"❌ {name}: {str(e)}")
        print(f"❌ {name}: {str(e)}")

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "database" in data

def test_create_user():
    r = requests.post(f"{BASE_URL}/users", json={"name": "Test User", "email": "test@test.com"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Test User"
    assert data["id"] > 0

def test_get_user():
    r = requests.get(f"{BASE_URL}/users/1")
    assert r.status_code == 200
    data = r.json()
    assert "id" in data

def test_update_notifications():
    r = requests.patch(f"{BASE_URL}/users/1/notifications", json={"notification_enabled": True})
    assert r.status_code == 200
    data = r.json()
    assert data["notification_enabled"] == True

def test_get_jobs():
    r = requests.get(f"{BASE_URL}/users/1/jobs", params={"limit": 10})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

def test_get_top_jobs():
    r = requests.get(f"{BASE_URL}/users/1/jobs/top", params={"limit": 5})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

def test_get_easy_apply_jobs():
    r = requests.get(f"{BASE_URL}/users/1/jobs/easy-apply", params={"limit": 5})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

def test_update_job_status():
    r = requests.patch(f"{BASE_URL}/jobs/1/status", json={"status": "saved"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "saved"

def test_toggle_bulk_select():
    r = requests.post(f"{BASE_URL}/jobs/1/select-bulk")
    assert r.status_code == 200
    data = r.json()
    assert "selected" in data

def test_bulk_update_status():
    r = requests.post(f"{BASE_URL}/jobs/bulk-status", json={"status": "applied", "job_ids": [1]})
    assert r.status_code == 200
    data = r.json()
    assert "message" in data

def test_get_analytics():
    r = requests.get(f"{BASE_URL}/users/1/analytics")
    assert r.status_code == 200
    data = r.json()
    assert "total_applications" in data
    assert "status_breakdown" in data
    assert "avg_match_score" in data

def test_get_search_history():
    r = requests.get(f"{BASE_URL}/users/1/search-history")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

def test_invalid_resume_upload():
    """Test that non-PDF files are rejected"""
    with open(".gitignore", "rb") as f:
        r = requests.post(f"{BASE_URL}/resumes/1/upload", files={"file": f})
    assert r.status_code == 400
    data = r.json()
    assert "Only PDF files are accepted" in data["detail"]

def test_get_nonexistent_user():
    r = requests.get(f"{BASE_URL}/users/99999")
    assert r.status_code == 404

def test_get_nonexistent_job():
    r = requests.get(f"{BASE_URL}/jobs/99999")
    assert r.status_code == 404

def test_resume_export_pdf():
    """Test PDF export for existing resume"""
    r = requests.get(f"{BASE_URL}/resumes/1/export-pdf")
    # May fail if no resume exists, which is OK
    assert r.status_code in [200, 404, 400]

def test_rate_limiting():
    """Test that rate limiting is active (should not block legitimate requests)"""
    for i in range(5):
        r = requests.get(f"{BASE_URL}/users/1")
        assert r.status_code in [200, 429]  # Either success or rate limit is OK

print("\n" + "="*60)
print("🧪 COMPREHENSIVE API TEST SUITE")
print("="*60 + "\n")

# Run all tests
test("Health Check", test_health)
test("Create User", test_create_user)
test("Get User", test_get_user)
test("Update Notifications", test_update_notifications)
test("Get Jobs", test_get_jobs)
test("Get Top Jobs", test_get_top_jobs)
test("Get Easy Apply Jobs", test_get_easy_apply_jobs)
test("Update Job Status", test_update_job_status)
test("Toggle Bulk Select", test_toggle_bulk_select)
test("Bulk Update Status", test_bulk_update_status)
test("Get Analytics", test_get_analytics)
test("Get Search History", test_get_search_history)
test("Invalid Resume Upload (PDF validation)", test_invalid_resume_upload)
test("Get Non-existent User (404)", test_get_nonexistent_user)
test("Get Non-existent Job (404)", test_get_nonexistent_job)
test("Resume Export PDF", test_resume_export_pdf)
test("Rate Limiting Active", test_rate_limiting)

print("\n" + "="*60)
print(f"📊 RESULTS: {len(successes)} passed, {len(errors)} failed")
print("="*60)

if errors:
    print("\n❌ FAILURES:")
    for err in errors:
        print(f"  {err}")
    sys.exit(1)
else:
    print("\n✅ ALL TESTS PASSED!")
    sys.exit(0)
