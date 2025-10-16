#!/usr/bin/env python3
"""
Complete Docker Application Test Suite
Tests all major functionality of the Resume Modifier application running in Docker.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5001"

def test_endpoint(endpoint, method="GET", data=None, headers=None, description=""):
    """Test a single endpoint and return the result"""
    url = f"{BASE_URL}{endpoint}"
    print(f"🔍 Testing {method} {endpoint} - {description}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code < 400:
            print("   ✅ SUCCESS")
            try:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
                return True, result
            except:
                print(f"   Response: {response.text[:100]}...")
                return True, response.text
        else:
            print(f"   ❌ FAILED: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, None

def main():
    print("=" * 80)
    print("🚀 DOCKER APPLICATION COMPLETE FUNCTIONALITY TEST")
    print("=" * 80)
    
    # Wait for services to be ready
    print("⏳ Waiting 5 seconds for services to be fully ready...")
    time.sleep(5)
    
    test_results = []
    
    # Test 1: Health Check
    success, result = test_endpoint("/health", description="System health check")
    test_results.append(("Health Check", success))
    
    # Test 2: API Documentation
    success, result = test_endpoint("/apidocs/", description="API documentation")
    test_results.append(("API Documentation", success))
    
    # Test 3: User Registration
    user_data = {
        "email": "dockertest@example.com",
        "password": "SecurePass123!"
    }
    success, result = test_endpoint("/api/register", "POST", user_data, description="User registration")
    test_results.append(("User Registration", success))
    
    # Test 4: User Login
    success, login_result = test_endpoint("/api/login", "POST", user_data, description="User login")
    test_results.append(("User Login", success))
    
    # Extract token for authenticated requests
    token = None
    if success and login_result:
        token = login_result.get("token")
        print(f"   🔑 Token extracted: {token[:20]}...")
    
    # Test 5: Resume Scoring (AI functionality)
    resume_data = {
        "resume": {
            "personalInfo": {
                "firstName": "Docker",
                "lastName": "Test",
                "email": "dockertest@example.com"
            },
            "workExperience": [
                {
                    "title": "Full Stack Developer",
                    "company": "Tech Startup",
                    "duration": "2021-2024",
                    "description": "Developed web applications using Python Flask and PostgreSQL"
                }
            ],
            "education": [
                {
                    "degree": "Computer Science",
                    "school": "University",
                    "year": "2021"
                }
            ],
            "skills": ["Python", "Flask", "PostgreSQL", "Docker", "REST APIs"]
        },
        "job_description": "We are looking for a skilled Python developer with experience in Flask, PostgreSQL, and Docker to join our team."
    }
    success, result = test_endpoint("/api/resume/score", "POST", resume_data, description="AI resume scoring")
    test_results.append(("AI Resume Scoring", success))
    
    # Test 6: Get Profile (if token available)
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        success, result = test_endpoint("/api/get_profile", "GET", headers=headers, description="Get user profile")
        test_results.append(("Get User Profile", success))
    else:
        test_results.append(("Get User Profile", False))
    
    # Test 7: Template endpoints
    success, result = test_endpoint("/api/templates", description="Get resume templates")
    test_results.append(("Get Templates", success))
    
    # Test 8: Seed templates
    success, result = test_endpoint("/api/templates/seed", "POST", description="Seed default templates")
    test_results.append(("Seed Templates", success))
    
    # Test 9: Basic PDF upload endpoint (without file, just structure test)
    try:
        response = requests.post(f"{BASE_URL}/api/pdfupload")
        if response.status_code in [400, 415]:  # Expected errors for missing file
            test_results.append(("PDF Upload Structure", True))
            print("🔍 Testing POST /api/pdfupload - PDF upload structure")
            print("   Status: 400/415 (Expected - no file provided)")
            print("   ✅ SUCCESS - Endpoint structure working")
        else:
            test_results.append(("PDF Upload Structure", False))
    except:
        test_results.append(("PDF Upload Structure", False))
    
    # Test Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<25} : {status}")
        if success:
            passed += 1
    
    print("-" * 80)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Docker application is fully functional!")
        print("✅ Database connectivity: Working")
        print("✅ User authentication: Working") 
        print("✅ AI resume scoring: Working")
        print("✅ API documentation: Working")
        print("✅ Template system: Working")
        print("\n📍 Access your application at:")
        print(f"   API Base: {BASE_URL}")
        print(f"   API Docs: {BASE_URL}/apidocs")
        print(f"   Health Check: {BASE_URL}/health")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())