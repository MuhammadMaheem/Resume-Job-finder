#!/usr/bin/env python3
"""API Testing Script"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test health endpoint"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            print("✅ Health check: PASSED")
            print(f"   Response: {r.json()}")
            return True
        else:
            print(f"❌ Health check: FAILED (Status {r.status_code})")
            return False
    except Exception as e:
        print(f"❌ Health check: ERROR - {e}")
        return False

def test_create_user():
    """Test user creation"""
    try:
        payload = {"name": "Test User", "email": "test@example.com"}
        r = requests.post(f"{BASE_URL}/users", json=payload, timeout=5)
        if r.status_code == 200:
            data = r.json()
            user_id = data.get("id")
            print(f"✅ Create user: PASSED (User ID: {user_id})")
            return user_id
        else:
            print(f"❌ Create user: FAILED (Status {r.status_code})")
            print(f"   Response: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Create user: ERROR - {e}")
        return None

def test_get_user(user_id):
    """Test get user"""
    try:
        r = requests.get(f"{BASE_URL}/users/{user_id}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ Get user: PASSED")
            print(f"   User: {data['name']} ({data['email']})")
            return True
        else:
            print(f"❌ Get user: FAILED (Status {r.status_code})")
            return False
    except Exception as e:
        print(f"❌ Get user: ERROR - {e}")
        return False

def test_list_resumes(user_id):
    """Test list resumes"""
    try:
        r = requests.get(f"{BASE_URL}/users/{user_id}/resumes", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ List resumes: PASSED ({len(data)} resumes)")
            return True
        else:
            print(f"❌ List resumes: FAILED (Status {r.status_code})")
            return False
    except Exception as e:
        print(f"❌ List resumes: ERROR - {e}")
        return False

def test_list_jobs(user_id):
    """Test list jobs"""
    try:
        r = requests.get(f"{BASE_URL}/users/{user_id}/jobs", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✅ List jobs: PASSED ({len(data)} jobs)")
            return True
        else:
            print(f"❌ List jobs: FAILED (Status {r.status_code})")
            return False
    except Exception as e:
        print(f"❌ List jobs: ERROR - {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running API Tests...\n")
    
    # Test health
    if not test_health():
        print("\n❌ Backend is not responding. Cannot continue tests.")
        exit(1)
    
    print()
    
    # Test user creation
    user_id = test_create_user()
    if not user_id:
        print("\n❌ Cannot create user. Stopping tests.")
        exit(1)
    
    print()
    
    # Test get user
    test_get_user(user_id)
    
    print()
    
    # Test list resumes
    test_list_resumes(user_id)
    
    print()
    
    # Test list jobs
    test_list_jobs(user_id)
    
    print("\n✅ All basic tests completed!")
