#!/usr/bin/env python3
"""
Google Drive Configuration Validation Script

Run this script to validate your Google Drive integration setup.

Usage:
    python validate_google_drive.py
    
Or from the project root:
    python -m app.utils.google_drive_validator
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from app.utils.google_drive_validator import GoogleDriveConfigValidator


def main():
    """Main validation function"""
    print("🔍 Validating Google Drive Configuration...")
    
    validator = GoogleDriveConfigValidator()
    results = validator.validate_all()
    validator.print_results(results)
    
    # Provide next steps
    if results['valid']:
        print("🎉 Your Google Drive integration is properly configured!")
        print("\nNext steps:")
        print("1. Start your application")
        print("2. Test file upload with google_drive=true parameter")
        print("3. Check application logs for Google Drive operations")
    else:
        print("🔧 Please fix the configuration errors above.")
        print("\nResources:")
        print("• Setup guide: docs/GOOGLE_DRIVE_SETUP.md")
        print("• Google Cloud Console: https://console.cloud.google.com/")
        print("• Google Drive API: https://developers.google.com/drive/api")
    
    return 0 if results['valid'] else 1


if __name__ == "__main__":
    sys.exit(main())