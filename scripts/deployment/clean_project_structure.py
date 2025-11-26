#!/usr/bin/env python3
"""
Clean up project structure and fix Docker import issues
"""
import os
import shutil
from pathlib import Path

def clean_project_structure():
    """Clean up duplicate files and fix project structure"""
    
    print("🧹 Cleaning up project structure...")
    
    base_dir = Path("/home/rex/project/resume-editor/project/Resume_Modifier")
    
    # Remove duplicate app directory (keep only core/app)
    duplicate_app_dir = base_dir / "app"
    
    if duplicate_app_dir.exists():
        print(f"🗑️  Removing duplicate app directory: {duplicate_app_dir}")
        shutil.rmtree(duplicate_app_dir)
    
    # Ensure all required files are in core/app/services
    core_services_dir = base_dir / "core" / "app" / "services"
    
    required_files = [
        "google_admin_auth_fixed.py",
        "flask_session_config.py",
        "google_drive_admin_service.py"
    ]
    
    for file_name in required_files:
        file_path = core_services_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name} exists in core/app/services")
        else:
            print(f"❌ Missing {file_name} in core/app/services")
    
    # Clean up any __pycache__ directories
    for pycache_dir in base_dir.rglob("__pycache__"):
        print(f"🗑️  Cleaning {pycache_dir}")
        shutil.rmtree(pycache_dir, ignore_errors=True)
    
    print("✅ Project structure cleanup completed!")

def verify_docker_structure():
    """Verify Docker container structure is correct"""
    
    print("\n🔍 Verifying Docker structure...")
    
    base_dir = Path("/home/rex/project/resume-editor/project/Resume_Modifier")
    
    # Check core directory structure
    core_dir = base_dir / "core"
    if not core_dir.exists():
        print("❌ Missing core directory")
        return False
    
    # Check core/app directory
    core_app_dir = core_dir / "app"
    if not core_app_dir.exists():
        print("❌ Missing core/app directory")
        return False
    
    # Check core/app/services directory
    services_dir = core_app_dir / "services"
    if not services_dir.exists():
        print("❌ Missing core/app/services directory")
        return False
    
    # Check required service files
    required_services = [
        "google_admin_auth_fixed.py",
        "flask_session_config.py", 
        "google_drive_admin_service.py"
    ]
    
    for service_file in required_services:
        if not (services_dir / service_file).exists():
            print(f"❌ Missing {service_file}")
            return False
        else:
            print(f"✅ Found {service_file}")
    
    print("✅ Docker structure verification passed!")
    return True

def main():
    """Main cleanup function"""
    
    print("=" * 60)
    print("🔧 PROJECT STRUCTURE CLEANUP & DOCKER FIX")
    print("=" * 60)
    
    # Clean up duplicates
    clean_project_structure()
    
    # Verify structure
    if verify_docker_structure():
        print("\n🎉 Project structure is clean and ready for Docker!")
        print("\n📝 Next steps:")
        print("1. Restart Docker containers")
        print("2. Check that imports work correctly")
        print("3. Test Google Drive integration")
    else:
        print("\n❌ Project structure issues remain!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())