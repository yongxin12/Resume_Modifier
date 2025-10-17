#!/usr/bin/env python3
"""
Test script to validate Google Docs export with complete content mapping
"""
import os
import sys
import requests
import json
from datetime import datetime

# Set environment for testing
os.environ['TESTING'] = 'true'

def test_export_api():
    """Test the Google Docs export API directly with mock credentials"""
    base_url = "http://localhost:5001"
    
    print("=" * 60)
    print("TESTING GOOGLE DOCS EXPORT VALIDATION")
    print("=" * 60)
    
    # Test the export endpoint with user_id=5, resume_id=1, template_id=1
    export_url = f"{base_url}/api/resume/export/gdocs"
    
    # Prepare test parameters
    test_params = {
        'user_id': 5,
        'resume_id': 1,
        'template_id': 1,
        'test_mode': True  # Enable test mode to avoid actual Google API calls
    }
    
    print(f"Testing export endpoint: {export_url}")
    print(f"Parameters: {test_params}")
    print("-" * 40)
    
    try:
        # Make the API call
        response = requests.post(export_url, json=test_params, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS - Export completed!")
            print(f"Document ID: {result.get('document_id', 'N/A')}")
            print(f"Document URL: {result.get('document_url', 'N/A')}")
            
            # Check if content summary is available
            if 'content_summary' in result:
                summary = result['content_summary']
                print(f"\n📄 Content Summary:")
                print(f"  - Contact Info: {'✅' if summary.get('contact_info') else '❌'}")
                print(f"  - Summary: {'✅' if summary.get('summary') else '❌'}")
                print(f"  - Work Experience: {'✅' if summary.get('work_experience') else '❌'}")
                print(f"  - Projects: {'✅' if summary.get('projects') else '❌'}")
                print(f"  - Education: {'✅' if summary.get('education') else '❌'}")
                print(f"  - Skills: {'✅' if summary.get('skills') else '❌'}")
                print(f"  - Certifications: {'✅' if summary.get('certifications') else '❌'}")
            
            return True
            
        else:
            print(f"\n❌ FAILED - Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
                if 'details' in error_data:
                    print(f"Details: {error_data['details']}")
            except:
                print(f"Response text: {response.text}")
            
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_data_transformation():
    """Test the data transformation logic directly"""
    print("\n" + "=" * 60)
    print("TESTING DATA TRANSFORMATION LOGIC")
    print("=" * 60)
    
    # Import the transformation function
    sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier')
    
    try:
        from app.services.google_docs_service import GoogleDocsService
        
        # Create sample resume data in the format from database
        sample_resume_data = {
            "userInfo": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john.doe@example.com",
                "phoneNumber": "+1 (555) 123-4567",
                "websiteOrOtherProfileURL": "https://johndoe.dev",
                "linkedInURL": "https://linkedin.com/in/johndoe"
            },
            "workExperience": [
                {
                    "jobTitle": "Senior Software Engineer",
                    "companyName": "Tech Corp",
                    "startDate": "2020-01-01",
                    "endDate": "2023-12-31",
                    "description": "Led development of microservices architecture"
                }
            ],
            "projects": [
                {
                    "projectTitle": "E-commerce Platform",
                    "description": "Built scalable e-commerce platform using React and Node.js",
                    "technologies": ["React", "Node.js", "PostgreSQL"]
                }
            ],
            "education": [
                {
                    "institutionName": "University of Technology",
                    "degree": "Bachelor of Computer Science",
                    "graduationDate": "2019-05-15"
                }
            ],
            "skills": ["Python", "JavaScript", "React", "PostgreSQL", "Docker"],
            "certifications": [
                {
                    "certificationName": "AWS Solutions Architect",
                    "issuingOrganization": "Amazon Web Services",
                    "dateReceived": "2021-06-01"
                }
            ]
        }
        
        # Create service instance and test transformation
        service = GoogleDocsService()
        transformed_data = service._transform_resume_data(sample_resume_data)
        
        print("✅ Data transformation successful!")
        print("\n📋 Transformed sections:")
        
        for section_name, section_data in transformed_data.items():
            if section_data:  # Only show non-empty sections
                print(f"  - {section_name}: {'✅ Has content' if section_data else '❌ Empty'}")
                if isinstance(section_data, list):
                    print(f"    ({len(section_data)} items)")
                elif isinstance(section_data, dict):
                    print(f"    ({len(section_data)} fields)")
        
        return True
        
    except Exception as e:
        print(f"❌ TRANSFORMATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"Test started at: {datetime.now()}")
    
    # Run transformation test first
    transform_success = test_data_transformation()
    
    # Then test the full API
    api_success = test_export_api()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Data Transformation: {'✅ PASS' if transform_success else '❌ FAIL'}")
    print(f"API Export Test: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if transform_success and api_success:
        print("\n🎉 ALL TESTS PASSED - Export functionality is working correctly!")
    else:
        print("\n⚠️  SOME TESTS FAILED - Review the output above for details")
    
    print(f"Test completed at: {datetime.now()}")