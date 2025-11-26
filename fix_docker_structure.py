"""
Docker Structure Fix Script
Updates the Docker container to work with both app and core/app structures
"""

import os
import shutil
import sys

def fix_docker_structure():
    """Ensure OAuth session fixes are available in both structures."""
    
    print("🔧 Fixing Docker container structure for OAuth session support...")
    
    # Source directories
    app_services = '/home/rex/project/resume-editor/project/Resume_Modifier/app/services'
    core_app_services = '/home/rex/project/resume-editor/project/Resume_Modifier/core/app/services'
    
    # Files to copy
    oauth_files = [
        'google_admin_auth_fixed.py',
        'flask_session_config.py'
    ]
    
    # Ensure core/app/services directory exists
    os.makedirs(core_app_services, exist_ok=True)
    
    # Copy OAuth fixes to core/app/services
    for file_name in oauth_files:
        src_file = os.path.join(app_services, file_name)
        dst_file = os.path.join(core_app_services, file_name)
        
        if os.path.exists(src_file):
            shutil.copy2(src_file, dst_file)
            print(f"✅ Copied {file_name} to core/app/services/")
        else:
            print(f"❌ Source file not found: {src_file}")
    
    # Copy other required files
    other_files = [
        ('app/extensions.py', 'core/app/extensions.py'),
        ('app/services/email_service.py', 'core/app/services/email_service.py')
    ]
    
    base_dir = '/home/rex/project/resume-editor/project/Resume_Modifier'
    
    for src_rel, dst_rel in other_files:
        src_file = os.path.join(base_dir, src_rel)
        dst_file = os.path.join(base_dir, dst_rel)
        
        if os.path.exists(src_file):
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            print(f"✅ Copied {src_rel} to {dst_rel}")
        else:
            print(f"❌ Source file not found: {src_file}")
    
    print("🎉 Docker structure fix completed!")
    print("📝 Summary:")
    print("   • OAuth session fixes copied to core/app/services/")
    print("   • Extensions and email service configured")
    print("   • Ready for Docker container restart")

if __name__ == "__main__":
    fix_docker_structure()