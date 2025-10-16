#!/usr/bin/env python3
"""
API Endpoint Analysis Script
Compares documented endpoints vs actual endpoints and tests functionality
"""

import requests
import json
import re

BASE_URL = "http://localhost:5001"

def get_documented_endpoints():
    """Get endpoints from OpenAPI spec"""
    try:
        response = requests.get(f"{BASE_URL}/apispec_1.json")
        spec = response.json()
        return list(spec.get('paths', {}).keys())
    except Exception as e:
        print(f"Error getting API spec: {e}")
        return []

def get_actual_endpoints():
    """Parse server.py to find all @api.route endpoints"""
    endpoints = []
    try:
        with open('app/server.py', 'r') as f:
            content = f.read()
            
        # Find all @api.route patterns
        route_pattern = r"@api\.route\(['\"]([^'\"]+)['\"].*?\)"
        matches = re.findall(route_pattern, content)
        
        for match in matches:
            # Clean up route parameters for comparison
            clean_route = re.sub(r'<[^>]+>', lambda m: '{' + m.group(0)[1:-1].split(':')[-1] + '}', match)
            endpoints.append(clean_route)
            
    except Exception as e:
        print(f"Error parsing server.py: {e}")
        
    return sorted(set(endpoints))

def test_endpoint_basic(endpoint, method="GET"):
    """Basic test of endpoint availability"""
    if '{' in endpoint:
        # Skip parameterized endpoints for basic test
        return None
        
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=5)
        
        return {
            'status': response.status_code,
            'accessible': response.status_code != 404,
            'error': None
        }
    except Exception as e:
        return {
            'status': None,
            'accessible': False,
            'error': str(e)
        }

def main():
    print("=" * 80)
    print("🔍 API ENDPOINT ANALYSIS")
    print("=" * 80)
    
    # Get endpoints from both sources
    documented = get_documented_endpoints()
    actual = get_actual_endpoints()
    
    print(f"\n📚 DOCUMENTED ENDPOINTS ({len(documented)}):")
    for endpoint in sorted(documented):
        print(f"  ✓ {endpoint}")
    
    print(f"\n⚙️  ACTUAL ENDPOINTS IN CODE ({len(actual)}):")
    for endpoint in sorted(actual):
        print(f"  ✓ {endpoint}")
    
    # Find differences
    missing_docs = set(actual) - set(documented)
    extra_docs = set(documented) - set(actual)
    
    print(f"\n❌ MISSING FROM DOCUMENTATION ({len(missing_docs)}):")
    if missing_docs:
        for endpoint in sorted(missing_docs):
            print(f"  ⚠️  {endpoint}")
    else:
        print("  ✅ None")
    
    print(f"\n⚠️  DOCUMENTED BUT NOT IN CODE ({len(extra_docs)}):")
    if extra_docs:
        for endpoint in sorted(extra_docs):
            print(f"  ❌ {endpoint}")
    else:
        print("  ✅ None")
    
    # Test accessibility of key endpoints
    print(f"\n🧪 ENDPOINT ACCESSIBILITY TEST:")
    key_endpoints = [
        ('/health', 'GET'),
        ('/api/register', 'POST'),
        ('/api/login', 'POST'),
        ('/api/templates', 'GET'),
        ('/api/resume/score', 'POST'),
        ('/api/get_profile', 'GET'),
        ('/api/save_resume', 'PUT'),
        ('/api/get_resume_list', 'GET'),
        ('/auth/google', 'GET'),
        ('/api/feedback', 'PUT')
    ]
    
    accessible_count = 0
    for endpoint, method in key_endpoints:
        result = test_endpoint_basic(endpoint, method)
        if result:
            status = "✅ ACCESSIBLE" if result['accessible'] else f"❌ NOT ACCESSIBLE ({result['status']})"
            print(f"  {endpoint:<25} {method:<4} : {status}")
            if result['accessible']:
                accessible_count += 1
        else:
            print(f"  {endpoint:<25} {method:<4} : ⚠️  PARAMETERIZED")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total documented endpoints: {len(documented)}")
    print(f"  Total actual endpoints: {len(actual)}")
    print(f"  Missing from docs: {len(missing_docs)}")
    print(f"  Extra in docs: {len(extra_docs)}")
    print(f"  Accessible endpoints: {accessible_count}/{len(key_endpoints)}")
    
    # Identify specific issues
    print(f"\n🔧 ISSUES IDENTIFIED:")
    if missing_docs:
        print(f"  1. {len(missing_docs)} endpoints lack Swagger documentation")
    if extra_docs:
        print(f"  2. {len(extra_docs)} endpoints documented but don't exist")
    if accessible_count < len(key_endpoints):
        print(f"  3. Some endpoints are not accessible (server issues?)")
    
    if not missing_docs and not extra_docs and accessible_count == len(key_endpoints):
        print("  ✅ All endpoints properly documented and accessible!")
    
    return len(missing_docs) + len(extra_docs)

if __name__ == "__main__":
    issues = main()
    exit(issues)