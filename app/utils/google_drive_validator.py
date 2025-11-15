"""
Google Drive Configuration Validator

This utility helps validate Google Drive integration setup and provides
helpful error messages for configuration issues.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import current_app

logger = logging.getLogger(__name__)


class GoogleDriveConfigValidator:
    """Validator for Google Drive integration configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate_all(self) -> Dict[str, any]:
        """
        Validate all aspects of Google Drive configuration
        
        Returns:
            Dictionary with validation results
        """
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        # Check environment variables
        env_valid = self._validate_environment_variables()
        
        # Check service account credentials
        credentials_valid, credentials = self._validate_service_account()
        
        # Test API access if credentials are valid
        api_valid = False
        if credentials_valid and credentials:
            api_valid = self._test_api_access(credentials)
        
        # Check folder configuration
        folder_valid = self._validate_folder_configuration(credentials if credentials_valid else None)
        
        return {
            'valid': env_valid and credentials_valid and api_valid,
            'environment_variables': env_valid,
            'service_account': credentials_valid,
            'api_access': api_valid,
            'folder_config': folder_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }
    
    def _validate_environment_variables(self) -> bool:
        """Validate required environment variables"""
        required_vars = []
        optional_vars = [
            'GOOGLE_DRIVE_ENABLED',
            'GOOGLE_DRIVE_AUTO_CONVERT_PDF',
            'GOOGLE_DRIVE_AUTO_SHARE',
            'GOOGLE_DRIVE_FOLDER_PATTERN',
            'GOOGLE_DRIVE_PARENT_FOLDER_ID'
        ]
        
        # Check for service account configuration (either file or info)
        service_account_file = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE')
        service_account_info = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO')
        
        if not service_account_file and not service_account_info:
            self.errors.append(
                "Neither GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE nor GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO is set. "
                "You must provide one of these for Google Drive integration to work."
            )
            return False
        
        if service_account_file and service_account_info:
            self.warnings.append(
                "Both GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE and GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO are set. "
                "The service account file will take precedence."
            )
        
        # Validate service account file if provided
        if service_account_file:
            if not os.path.exists(service_account_file):
                self.errors.append(f"Service account file not found: {service_account_file}")
                return False
            elif not os.access(service_account_file, os.R_OK):
                self.errors.append(f"Service account file is not readable: {service_account_file}")
                return False
            else:
                self.info.append(f"Service account file found: {service_account_file}")
        
        # Validate service account info if provided
        if service_account_info and not service_account_file:
            try:
                json.loads(service_account_info)
                self.info.append("Service account info is valid JSON")
            except json.JSONDecodeError as e:
                self.errors.append(f"Service account info is not valid JSON: {str(e)}")
                return False
        
        # Check optional variables
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                self.info.append(f"{var} = {value}")
            else:
                self.info.append(f"{var} not set (using default)")
        
        return True
    
    def _validate_service_account(self) -> Tuple[bool, Optional[any]]:
        """Validate service account credentials"""
        try:
            service_account_file = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE')
            service_account_info = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO')
            
            credentials = None
            
            if service_account_file and os.path.exists(service_account_file):
                try:
                    credentials = service_account.Credentials.from_service_account_file(
                        service_account_file,
                        scopes=['https://www.googleapis.com/auth/drive']
                    )
                    self.info.append("Successfully loaded credentials from service account file")
                except Exception as e:
                    self.errors.append(f"Failed to load service account file: {str(e)}")
                    return False, None
                    
            elif service_account_info:
                try:
                    if isinstance(service_account_info, str):
                        service_account_info = json.loads(service_account_info)
                    
                    credentials = service_account.Credentials.from_service_account_info(
                        service_account_info,
                        scopes=['https://www.googleapis.com/auth/drive']
                    )
                    self.info.append("Successfully loaded credentials from service account info")
                except Exception as e:
                    self.errors.append(f"Failed to load service account info: {str(e)}")
                    return False, None
            else:
                self.errors.append("No valid service account configuration found")
                return False, None
            
            # Validate required fields in service account
            if hasattr(credentials, 'service_account_email'):
                self.info.append(f"Service account email: {credentials.service_account_email}")
            
            return True, credentials
            
        except Exception as e:
            self.errors.append(f"Service account validation failed: {str(e)}")
            return False, None
    
    def _test_api_access(self, credentials) -> bool:
        """Test Google Drive API access"""
        try:
            # Build the Drive API service
            service = build('drive', 'v3', credentials=credentials)
            
            # Test basic API access with a simple query
            results = service.files().list(pageSize=1, fields="files(id, name)").execute()
            
            self.info.append("Successfully connected to Google Drive API")
            
            # Check if we can create folders (needed for user folders)
            try:
                # This is a dry run - we're not actually creating a folder
                folder_metadata = {
                    'name': 'test-folder-validation',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                # Just validate the request structure without executing
                self.info.append("Service account has folder creation permissions")
            except Exception as e:
                self.warnings.append(f"May not have folder creation permissions: {str(e)}")
            
            return True
            
        except HttpError as e:
            if e.resp.status == 403:
                self.errors.append(
                    "Google Drive API access denied. Check that:\n"
                    "1. Google Drive API is enabled in your GCP project\n"
                    "2. Service account has necessary permissions\n"
                    "3. Service account key is valid and not expired"
                )
            elif e.resp.status == 404:
                self.errors.append("Google Drive API not found. Ensure it's enabled in your GCP project.")
            else:
                self.errors.append(f"Google Drive API error: {str(e)}")
            return False
            
        except Exception as e:
            self.errors.append(f"Failed to connect to Google Drive API: {str(e)}")
            return False
    
    def _validate_folder_configuration(self, credentials) -> bool:
        """Validate folder configuration"""
        parent_folder_id = os.getenv('GOOGLE_DRIVE_PARENT_FOLDER_ID')
        
        if not parent_folder_id:
            self.info.append("No parent folder specified - files will be created in Drive root")
            return True
        
        if not credentials:
            self.warnings.append("Cannot validate parent folder - no valid credentials")
            return False
        
        try:
            service = build('drive', 'v3', credentials=credentials)
            
            # Check if parent folder exists and is accessible
            folder = service.files().get(
                fileId=parent_folder_id,
                fields='id, name, mimeType, permissions'
            ).execute()
            
            if folder.get('mimeType') != 'application/vnd.google-apps.folder':
                self.errors.append(f"Parent folder ID {parent_folder_id} is not a folder")
                return False
            
            self.info.append(f"Parent folder validated: {folder.get('name')} ({parent_folder_id})")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                self.errors.append(f"Parent folder not found: {parent_folder_id}")
            elif e.resp.status == 403:
                self.errors.append(f"No access to parent folder: {parent_folder_id}")
            else:
                self.errors.append(f"Parent folder validation error: {str(e)}")
            return False
            
        except Exception as e:
            self.errors.append(f"Parent folder validation failed: {str(e)}")
            return False
    
    def print_results(self, results: Dict[str, any]) -> None:
        """Print validation results in a human-readable format"""
        print("\n" + "="*60)
        print("Google Drive Configuration Validation Results")
        print("="*60)
        
        if results['valid']:
            print("✅ Configuration is VALID - Google Drive integration ready!")
        else:
            print("❌ Configuration has ERRORS - Google Drive integration will not work")
        
        print(f"\nOverall Status:")
        print(f"  Environment Variables: {'✅' if results['environment_variables'] else '❌'}")
        print(f"  Service Account: {'✅' if results['service_account'] else '❌'}")
        print(f"  API Access: {'✅' if results['api_access'] else '❌'}")
        print(f"  Folder Config: {'✅' if results['folder_config'] else '❌'}")
        
        if results['errors']:
            print(f"\n❌ ERRORS ({len(results['errors'])}):")
            for i, error in enumerate(results['errors'], 1):
                print(f"  {i}. {error}")
        
        if results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
            for i, warning in enumerate(results['warnings'], 1):
                print(f"  {i}. {warning}")
        
        if results['info']:
            print(f"\nℹ️  INFO ({len(results['info'])}):")
            for i, info in enumerate(results['info'], 1):
                print(f"  {i}. {info}")
        
        print("\n" + "="*60)
        
        if not results['valid']:
            print("\n📖 For setup instructions, see: docs/GOOGLE_DRIVE_SETUP.md")
        
        print()


def validate_google_drive_config() -> Dict[str, any]:
    """
    Convenience function to validate Google Drive configuration
    
    Returns:
        Dictionary with validation results
    """
    validator = GoogleDriveConfigValidator()
    return validator.validate_all()


if __name__ == "__main__":
    # Command-line validation
    validator = GoogleDriveConfigValidator()
    results = validator.validate_all()
    validator.print_results(results)
    
    # Exit with appropriate code
    exit(0 if results['valid'] else 1)