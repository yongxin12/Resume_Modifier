"""
Google Drive Admin Service

This service handles file operations using administrator's Google Drive via OAuth credentials,
meeting functional requirements API-05f and API-05g for admin-controlled storage.

The service provides:
- File uploads to admin's personal Google Drive
- Organized folder structure by user
- Document conversion (PDF to Google Docs)
- File sharing with edit permissions
- User folder management
"""

import os
import io
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from flask import current_app
from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed
from app.models.temp import User
import logging

logger = logging.getLogger(__name__)

class GoogleDriveAdminService:
    """
    Google Drive service using admin OAuth credentials for centralized file storage.
    
    This service implements API-05f (admin-controlled Google Drive storage) and 
    API-05g (file sharing with user edit permissions) from the functional specifications.
    """
    
    def __init__(self):
        """Initialize the Google Drive Admin Service."""
        self.auth_service = GoogleAdminAuthServiceFixed()
        self.drive_service = None
        self.docs_service = None
        
        # Configuration from app settings
        self.main_folder_name = current_app.config.get('GOOGLE_ADMIN_DRIVE_FOLDER_NAME', 'Resume_Modifier_Files')
        self.enable_sharing = current_app.config.get('GOOGLE_DRIVE_ENABLE_SHARING', True)
        self.default_permissions = current_app.config.get('GOOGLE_DRIVE_DEFAULT_PERMISSIONS', 'writer')
    
    def _get_drive_service(self, admin_user_id: int = None):
        """
        Get authenticated Google Drive service using admin credentials.
        
        Args:
            admin_user_id: Specific admin user ID (optional, will find admin if not provided)
            
        Returns:
            googleapiclient.discovery.Resource: Authenticated Drive service
            
        Raises:
            ValueError: If admin authentication is not available
        """
        if self.drive_service:
            return self.drive_service
        
        # Find authenticated admin user if not provided
        if admin_user_id is None:
            admin_users = User.query.filter_by(is_admin=True).all()
            if not admin_users:
                raise ValueError("No admin user found")
            
            # Find first authenticated admin user
            for admin_user in admin_users:
                auth_status = self.auth_service.get_auth_status(admin_user.id) 
                if auth_status.get('authenticated'):
                    admin_user_id = admin_user.id
                    break
            
            if admin_user_id is None:
                raise ValueError("No authenticated admin user found. Please authenticate at /auth/google/admin")
        
        credentials = self.auth_service.get_admin_credentials(admin_user_id)
        if not credentials:
            raise ValueError("Admin Google authentication required. Please authenticate at /auth/google/admin")
        
        self.drive_service = build('drive', 'v3', credentials=credentials)
        return self.drive_service
    
    def _get_docs_service(self, admin_user_id: int = None):
        """
        Get authenticated Google Docs service using admin credentials.
        
        Args:
            admin_user_id: Specific admin user ID (optional, will find admin if not provided)
            
        Returns:
            googleapiclient.discovery.Resource: Authenticated Docs service
            
        Raises:
            ValueError: If admin authentication is not available
        """
        if self.docs_service:
            return self.docs_service
        
        # Find authenticated admin user if not provided
        if admin_user_id is None:
            admin_users = User.query.filter_by(is_admin=True).all()
            if not admin_users:
                raise ValueError("No admin user found")
            
            # Find first authenticated admin user
            for admin_user in admin_users:
                auth_status = self.auth_service.get_auth_status(admin_user.id) 
                if auth_status.get('authenticated'):
                    admin_user_id = admin_user.id
                    break
            
            if admin_user_id is None:
                raise ValueError("No authenticated admin user found. Please authenticate at /auth/google/admin")
        
        credentials = self.auth_service.get_admin_credentials(admin_user_id)
        if not credentials:
            raise ValueError("Admin Google authentication required. Please authenticate at /auth/google/admin")
        
        self.docs_service = build('docs', 'v1', credentials=credentials)
        return self.docs_service
    
    def upload_file_to_admin_drive(
        self,
        file_content: bytes,
        filename: str,
        mime_type: str,
        user_id: int,
        user_email: str = None,
        convert_to_doc: bool = True,
        share_with_user: bool = True
    ) -> Dict[str, Any]:
        """
        Upload file to admin's Google Drive with organized folder structure.
        
        This method implements API-05f (admin Google Drive storage) and API-05g 
        (sharing with user edit permissions).
        
        Args:
            file_content: Binary content of the file
            filename: Original filename
            mime_type: MIME type of the file
            user_id: ID of the user uploading the file
            user_email: Email of the user for sharing (optional)
            convert_to_doc: Whether to convert PDF/DOCX to Google Doc
            share_with_user: Whether to share files with the user
            
        Returns:
            dict: Upload result with file information and links
        """
        try:
            drive_service = self._get_drive_service()
            
            # Get user information for folder organization
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Use provided email or fall back to user's email
            share_email = user_email or user.email
            
            # Create user folder if needed
            user_folder_id = self._ensure_user_folder(user_id, user.username or f"User_{user_id}")
            
            # Upload original file
            file_metadata = {
                'name': filename,
                'parents': [user_folder_id],
                'description': f'Uploaded by {user.username or user.email} on {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype=mime_type,
                resumable=True
            )
            
            uploaded_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, webViewLink, webContentLink, createdTime'
            ).execute()
            
            result = {
                'success': True,
                'file_id': uploaded_file.get('id'),
                'name': uploaded_file.get('name'),
                'mime_type': uploaded_file.get('mimeType'),
                'size': uploaded_file.get('size'),
                'drive_link': uploaded_file.get('webViewLink'),
                'download_link': uploaded_file.get('webContentLink'),
                'created_time': uploaded_file.get('createdTime'),
                'folder_id': user_folder_id
            }
            
            # Convert to Google Doc if requested and file is supported
            if convert_to_doc and self._is_convertible_to_doc(mime_type):
                doc_result = self._convert_to_google_doc(
                    uploaded_file['id'], 
                    filename, 
                    user_folder_id
                )
                result.update(doc_result)
            
            # Share with user if requested and email available
            if share_with_user and share_email:
                sharing_result = self._share_files_with_user(
                    [uploaded_file['id']], 
                    share_email,
                    doc_file_id=result.get('doc_id')
                )
                result.update(sharing_result)
            
            logger.info(f"Successfully uploaded {filename} to admin's Google Drive for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to upload to admin's Google Drive: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def _ensure_user_folder(self, user_id: int, username: str) -> str:
        """
        Ensure user-specific folder exists in admin's drive.
        
        Creates organized folder structure: Resume_Modifier_Files/Users/Username_UserID/
        
        Args:
            user_id: ID of the user
            username: Username for folder naming
            
        Returns:
            str: Folder ID of the user's folder
        """
        drive_service = self._get_drive_service()
        
        # Get or create main Resume Modifier folder
        main_folder_id = self._get_or_create_folder(self.main_folder_name)
        
        # Get or create Users subfolder
        users_folder_id = self._get_or_create_folder("Users", main_folder_id)
        
        # Get or create user-specific folder
        user_folder_name = f"{username}_{user_id}"
        user_folder_id = self._get_or_create_folder(user_folder_name, users_folder_id)
        
        return user_folder_id
    
    def _get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Get existing folder or create new one.
        
        Args:
            folder_name: Name of the folder
            parent_id: Parent folder ID (optional)
            
        Returns:
            str: Folder ID
        """
        drive_service = self._get_drive_service()
        
        # Search for existing folder
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        try:
            results = drive_service.files().list(
                q=query, 
                fields='files(id, name)',
                pageSize=10
            ).execute()
            folders = results.get('files', [])
            
            if folders:
                logger.info(f"Found existing folder '{folder_name}': {folders[0]['id']}")
                return folders[0]['id']
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'description': f'Resume Modifier folder created on {datetime.utcnow().strftime("%Y-%m-%d")}'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = drive_service.files().create(
                body=folder_metadata,
                fields='id, name'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created folder '{folder_name}' in admin's Google Drive: {folder_id}")
            return folder_id
            
        except Exception as e:
            logger.error(f"Failed to get or create folder '{folder_name}': {str(e)}")
            raise ValueError(f"Failed to create folder structure: {str(e)}")
    
    def _is_convertible_to_doc(self, mime_type: str) -> bool:
        """
        Check if file type can be converted to Google Doc.
        
        Args:
            mime_type: MIME type of the file
            
        Returns:
            bool: True if file can be converted to Google Doc
        """
        convertible_types = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
            'application/msword',  # DOC
            'text/plain',
            'text/rtf',
            'application/rtf'
        ]
        return mime_type in convertible_types
    
    def _convert_to_google_doc(self, file_id: str, original_name: str, parent_folder_id: str) -> Dict[str, Any]:
        """
        Convert uploaded file to Google Doc format.
        
        Args:
            file_id: ID of the uploaded file
            original_name: Original filename
            parent_folder_id: Parent folder ID
            
        Returns:
            dict: Google Doc information
        """
        drive_service = self._get_drive_service()
        
        try:
            # Create Google Doc name
            base_name = os.path.splitext(original_name)[0]
            doc_name = f"{base_name} (Google Doc)"
            
            # Import the file as Google Doc
            copy_metadata = {
                'name': doc_name,
                'parents': [parent_folder_id],
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            # Use the import method to convert file to Google Doc
            doc = drive_service.files().copy(
                fileId=file_id,
                body=copy_metadata,
                fields='id, name, webViewLink, mimeType'
            ).execute()
            
            logger.info(f"Successfully converted {original_name} to Google Doc: {doc.get('id')}")
            
            return {
                'doc_id': doc.get('id'),
                'doc_name': doc.get('name'),
                'doc_link': doc.get('webViewLink'),
                'doc_mime_type': doc.get('mimeType')
            }
            
        except Exception as e:
            logger.warning(f"Failed to convert {original_name} to Google Doc: {str(e)}")
            return {
                'doc_conversion_error': str(e),
                'doc_conversion_attempted': True
            }
    
    def _share_files_with_user(self, file_ids: List[str], user_email: str, doc_file_id: str = None) -> Dict[str, Any]:
        """
        Share files publicly with "Anyone with the link" access (API-05g).
        
        Per functional specification API-05g: "makes publicly editable via link"
        This sets General Access to "Anyone with the link" with editor permissions,
        so users don't need to request access or have a Google account.
        
        Args:
            file_ids: List of file IDs to share
            user_email: Email address of the user (for tracking, not for permission)
            doc_file_id: Google Doc file ID if available
            
        Returns:
            dict: Sharing result information
        """
        if not self.enable_sharing:
            return {'sharing_skipped': True, 'reason': 'Sharing disabled'}
        
        drive_service = self._get_drive_service()
        shared_files = []
        sharing_errors = []
        
        # Add doc file to sharing list if provided
        all_file_ids = file_ids.copy()
        if doc_file_id and doc_file_id not in all_file_ids:
            all_file_ids.append(doc_file_id)
        
        for file_id in all_file_ids:
            try:
                # Create "Anyone with the link" permission (public access)
                # This allows anyone with the link to access without requesting permission
                permission = {
                    'type': 'anyone',  # Changed from 'user' to 'anyone'
                    'role': self.default_permissions  # 'writer' allows editing
                }
                
                # Apply permission - no email needed for 'anyone' type
                drive_service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    fields='id, type, role'
                ).execute()
                
                shared_files.append(file_id)
                logger.info(f"Set file {file_id} to 'Anyone with the link' ({self.default_permissions} access)")
                
            except HttpError as e:
                error_msg = f"Failed to share file {file_id}: {str(e)}"
                logger.warning(error_msg)
                sharing_errors.append({'file_id': file_id, 'error': error_msg})
            except Exception as e:
                error_msg = f"Unexpected error sharing file {file_id}: {str(e)}"
                logger.error(error_msg)
                sharing_errors.append({'file_id': file_id, 'error': error_msg})
        
        return {
            'shared_with': user_email,  # Keep for reference/tracking
            'access_type': 'anyone_with_link',  # New field to indicate public access
            'shared_files': shared_files,
            'sharing_errors': sharing_errors,
            'permissions': self.default_permissions,
            'sharing_successful': len(shared_files) > 0,
            'message': f'Files accessible to anyone with the link ({self.default_permissions} access)'
        }
    
    def get_user_files(self, user_id: int, limit: int = 100) -> Dict[str, Any]:
        """
        Get files from user's folder in admin's Google Drive.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of files to return
            
        Returns:
            dict: List of files and folder information
        """
        try:
            drive_service = self._get_drive_service()
            
            # Get user folder
            user = User.query.get(user_id)
            if not user:
                return {'error': f'User {user_id} not found'}
            
            user_folder_id = self._ensure_user_folder(user_id, user.username or f"User_{user_id}")
            
            # Search for files in user's folder
            query = f"'{user_folder_id}' in parents and trashed = false"
            
            results = drive_service.files().list(
                q=query,
                fields='files(id, name, mimeType, size, webViewLink, createdTime, modifiedTime)',
                pageSize=limit,
                orderBy='createdTime desc'
            ).execute()
            
            files = results.get('files', [])
            
            return {
                'success': True,
                'user_id': user_id,
                'folder_id': user_folder_id,
                'files': files,
                'file_count': len(files)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user files for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_file_from_drive(self, file_id: str) -> Dict[str, Any]:
        """
        Delete file from admin's Google Drive.
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            dict: Deletion result
        """
        try:
            drive_service = self._get_drive_service()
            
            # Move file to trash (soft delete)
            drive_service.files().update(
                fileId=file_id,
                body={'trashed': True}
            ).execute()
            
            logger.info(f"Successfully moved file {file_id} to trash in admin's Google Drive")
            return {
                'success': True,
                'file_id': file_id,
                'action': 'moved_to_trash'
            }
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id} from admin's Google Drive: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a file in admin's Google Drive.
        
        Args:
            file_id: ID of the file
            
        Returns:
            dict: File information
        """
        try:
            drive_service = self._get_drive_service()
            
            file_info = drive_service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, webViewLink, webContentLink, createdTime, modifiedTime, parents, description'
            ).execute()
            
            return {
                'success': True,
                'file': file_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_admin_auth_status(self) -> Dict[str, Any]:
        """
        Check if admin authentication is available and valid.
        
        Returns:
            dict: Authentication status information
        """
        try:
            # Find all admin users and check if any are authenticated
            admin_users = User.query.filter_by(is_admin=True).all()
            if not admin_users:
                return {
                    'authenticated': False,
                    'message': 'No admin user found',
                    'auth_url': '/auth/google/admin'
                }
            
            # Check auth status for all admin users
            for admin_user in admin_users:
                auth_status = self.auth_service.get_auth_status(admin_user.id)
                
                if auth_status.get('authenticated'):
                    return {
                        'authenticated': True,
                        'message': 'Admin Google Drive authentication is active',
                        'admin_user_id': admin_user.id
                    }
            
            # If no admin user is authenticated
            return {
                'authenticated': False,
                'message': 'Admin Google Drive authentication required',
                'auth_url': '/auth/google/admin'
            }
                
        except Exception as e:
            logger.error(f"Failed to check admin auth status: {str(e)}")
            return {
                'authenticated': False,
                'error': str(e),
                'auth_url': '/auth/google/admin'
            }