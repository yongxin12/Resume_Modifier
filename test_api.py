"""
Test script for Resume Editor API endpoints
Tests health check, resume scoring, and other key endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_health_check():
    """Test the /health endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_resume_score():
    """Test the /api/resume/score endpoint"""
    print("\n=== Testing Resume Score Endpoint ===")
    
    sample_resume = {
        "personalInfo": {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "location": "San Francisco, CA"
        },
        "workExperience": [
            {
                "companyName": "Tech Corp",
                "jobTitle": "Software Engineer",
                "location": "San Francisco, CA",
                "startDate": "2020-01",
                "endDate": "2023-12",
                "description": "Developed web applications using Python and React"
            }
        ],
        "education": [
            {
                "institutionName": "University of California",
                "degree": "Bachelor of Science",
                "major": "Computer Science",
                "startDate": "2016-09",
                "endDate": "2020-05"
            }
        ],
        "skills": ["Python", "JavaScript", "React", "Flask", "PostgreSQL"]
    }
    
    job_description = """
    We are looking for a Senior Software Engineer with experience in Python, 
    React, and cloud technologies. The ideal candidate should have strong 
    communication skills and experience building scalable web applications.
    """
    
    payload = {
        "resume": sample_resume,
        "job_description": job_description
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/resume/score",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_register_and_login():
    """Test registration and login endpoints"""
    print("\n=== Testing Registration and Login ===")
    
    # Test registration
    import time
    register_data = {
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "SecurePass123!"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/register",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Registration Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Test login with same credentials
        login_response = requests.post(
            f"{BASE_URL}/api/login",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nLogin Status: {login_response.status_code}")
        print(f"Response: {json.dumps(login_response.json(), indent=2)}")
        
        return login_response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("========================================")
    print("Resume Editor API Test Suite")
    print("========================================")
    
    results = {
        "Health Check": test_health_check(),
        "Resume Scoring": test_resume_score(),
        "Auth (Register/Login)": test_register_and_login()
    }
    
    print("\n========================================")
    print("Test Results Summary")
    print("========================================")
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
