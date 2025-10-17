#!/usr/bin/env python3
"""
Direct test of Google Docs service without API authentication
"""
import os
import sys
import json
from datetime import datetime

# Add project path
sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier')

def test_document_creation_direct():
    """Test document creation directly via GoogleDocsService"""
    print("=" * 60)
    print("DIRECT GOOGLE DOCS SERVICE TEST")
    print("=" * 60)
    
    try:
        from app.services.google_docs_service import GoogleDocsService
        from app.models.temp import Resume, ResumeTemplate
        from app.extensions import db
        from app import create_app
        
        # Create application context
        app = create_app()
        
        with app.app_context():
            print("📊 Fetching resume data from database...")
            
            # Get the actual resume data
            resume = Resume.query.filter_by(user_id=5, serial_number=1).first()
            if not resume:
                print("❌ Resume not found (user_id=5, serial_number=1)")
                return False
            
            print(f"✅ Found resume: {resume.title}")
            print(f"   Created: {resume.created_at}")
            
            # Get template data
            template = ResumeTemplate.query.filter_by(id=1).first()
            if not template:
                print("❌ Template not found (template_id=1)")
                return False
            
            print(f"✅ Found template: {template.name}")
            
            # Parse resume data
            resume_data = resume.parsed_resume
            if not resume_data:
                print("❌ Resume has no parsed_resume data")
                return False
            
            print(f"✅ Resume data available - {len(str(resume_data))} characters")
            
            # Test transformation
            service = GoogleDocsService()
            transformed_data = service._transform_resume_data(resume_data)
            
            print("\n📋 Content Analysis:")
            total_content = 0
            
            for section_name, section_data in transformed_data.items():
                if section_data:
                    if isinstance(section_data, dict):
                        content_size = len(str(section_data))
                        non_empty_fields = sum(1 for v in section_data.values() if v)
                        print(f"  - {section_name}: {non_empty_fields} fields, {content_size} chars")
                    elif isinstance(section_data, list):
                        content_size = len(str(section_data))
                        print(f"  - {section_name}: {len(section_data)} items, {content_size} chars")
                    else:
                        content_size = len(str(section_data))
                        print(f"  - {section_name}: {content_size} chars")
                    
                    total_content += content_size
                else:
                    print(f"  - {section_name}: ❌ Empty")
            
            print(f"\n📈 Total content size: {total_content} characters")
            
            # Test document creation in test mode
            print("\n🔧 Testing document creation...")
            os.environ['TESTING'] = 'true'  # Enable test mode
            
            result = service.create_document(
                document_data={
                    'title': f"Test Resume - {resume.title}",
                    'content': transformed_data,
                    'template_config': template.style_config if template else None
                }
            )
            
            if result and 'document_id' in result:
                print(f"✅ Document creation successful!")
                print(f"   Document ID: {result['document_id']}")
                print(f"   Document URL: {result.get('document_url', 'N/A')}")
                
                # Check content summary
                if 'content_summary' in result:
                    summary = result['content_summary']
                    print(f"\n📄 Generated Content Summary:")
                    for section, has_content in summary.items():
                        status = "✅" if has_content else "❌"
                        print(f"   {status} {section}")
                
                return True
            else:
                print("❌ Document creation failed - no result returned")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"Direct test started at: {datetime.now()}")
    
    success = test_document_creation_direct()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 DIRECT TEST PASSED - Google Docs service is working correctly!")
        print("✅ Content transformation and document creation are both functional")
    else:
        print("❌ DIRECT TEST FAILED - Review the output above for details")
    
    print(f"Test completed at: {datetime.now()}")