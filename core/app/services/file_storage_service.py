"""
File Storage Service for handling file operations
Supports both local file system and Amazon S3 storage

Author: Resume Modifier Backend Team
Date: October 2024
"""

import os
import shutil
import uuid
import mimetypes
from datetime import datetime
from typing import Dict, Any, Optional, Union
from io import BytesIO
from werkzeug.datastructures import FileStorage
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class StorageError(Exception):
    """Custom exception for storage-related errors"""
    pass


@dataclass
class StorageResult:
    """Result object for storage operations"""
    success: bool
    storage_type: Optional[str] = None
    file_path: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None
    file_size: Optional[int] = None
    url: Optional[str] = None
    content: Optional[bytes] = None
    content_type: Optional[str] = None
    filename: Optional[str] = None
    error_message: Optional[str] = None
    
    @property
    def local_path(self):
        """Backward compatibility property - returns file_path for local storage"""
        if self.storage_type == 'local':
            return self.file_path
        return None


class FileStorageService:
    """
    Service for handling file storage operations.
    Supports both local file system and Amazon S3 storage.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the file storage service with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - storage_type: 'local' or 's3'
                - For local storage:
                    - local_storage_path: Base path for file storage
                    - base_url: Base URL for generating file URLs
                - For S3 storage:
                    - s3_bucket: S3 bucket name
                    - s3_region: AWS region
                    - aws_access_key_id: AWS access key
                    - aws_secret_access_key: AWS secret key
        
        Raises:
            StorageError: If configuration is invalid or missing required fields
        """
        self.config = config
        self.storage_type = config.get('storage_type')
        
        if self.storage_type not in ['local', 's3']:
            raise StorageError(f"Invalid storage type: {self.storage_type}")
        
        if self.storage_type == 'local':
            self._validate_local_config()
            self.local_storage_path = config['local_storage_path']
            self.base_url = config.get('base_url', 'http://localhost:5001')
        
        elif self.storage_type == 's3':
            self._validate_s3_config()
            self.s3_bucket = config['s3_bucket']
            self.s3_region = config['s3_region']
            self._init_s3_client()

    def _validate_local_config(self):
        """Validate local storage configuration"""
        if 'local_storage_path' not in self.config:
            raise StorageError("local_storage_path is required for local storage")

    def _validate_s3_config(self):
        """Validate S3 storage configuration"""
        required_fields = ['s3_bucket', 's3_region', 'aws_access_key_id', 'aws_secret_access_key']
        for field in required_fields:
            if field not in self.config:
                raise StorageError(f"{field} is required for S3 storage")

    def _init_s3_client(self):
        """Initialize S3 client with credentials"""
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.config['s3_region'],
                aws_access_key_id=self.config['aws_access_key_id'],
                aws_secret_access_key=self.config['aws_secret_access_key']
            )
        except NoCredentialsError as e:
            raise StorageError(f"AWS credentials not found: {str(e)}")
        except Exception as e:
            raise StorageError(f"Failed to initialize S3 client: {str(e)}")

    def upload_file(self, file_storage: FileStorage, user_id: int, filename: str) -> StorageResult:
        """
        Upload a file to the configured storage backend.
        
        Args:
            file_storage (FileStorage): Werkzeug FileStorage object
            user_id (int): ID of the user uploading the file
            filename (str): Sanitized filename for storage
        
        Returns:
            StorageResult: Result object containing upload details or error
        """
        try:
            # Reset file pointer to beginning
            file_storage.seek(0)
            file_content = file_storage.read()
            file_size = len(file_content)
            
            if self.storage_type == 'local':
                return self._upload_local(file_content, user_id, filename, file_size)
            elif self.storage_type == 's3':
                return self._upload_s3(file_content, user_id, filename, file_size)
                
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"Upload failed: {str(e)}"
            )

    def _upload_local(self, file_content: bytes, user_id: int, filename: str, file_size: int) -> StorageResult:
        """Upload file to local storage"""
        try:
            # Generate storage path
            file_path = self._generate_storage_path(user_id, filename)
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except OSError as e:
                    return StorageResult(
                        success=False,
                        error_message=f"Failed to create storage directory: {str(e)}"
                    )
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Generate URL
            url = self._get_file_url(file_path)
            
            return StorageResult(
                success=True,
                storage_type='local',
                file_path=file_path,
                file_size=file_size,
                url=url
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"Local upload failed: {str(e)}"
            )

    def _upload_s3(self, file_content: bytes, user_id: int, filename: str, file_size: int) -> StorageResult:
        """Upload file to S3 storage"""
        try:
            # Generate S3 key
            s3_key = self._generate_storage_path(user_id, filename)
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                BytesIO(file_content),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ContentType': mimetypes.guess_type(filename)[0] or 'application/octet-stream'
                }
            )
            
            # Generate URL
            url = self._get_file_url(s3_key)
            
            return StorageResult(
                success=True,
                storage_type='s3',
                s3_bucket=self.s3_bucket,
                s3_key=s3_key,
                file_size=file_size,
                url=url
            )
            
        except ClientError as e:
            return StorageResult(
                success=False,
                error_message=f"S3 upload failed: {str(e)}"
            )
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"S3 upload failed: {str(e)}"
            )

    def download_file(self, file_path: str) -> StorageResult:
        """
        Download a file from the configured storage backend.
        
        Args:
            file_path (str): Path to the file (local path or S3 key)
        
        Returns:
            StorageResult: Result object containing file content or error
        """
        try:
            if self.storage_type == 'local':
                return self._download_local(file_path)
            elif self.storage_type == 's3':
                return self._download_s3(file_path)
                
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"Download failed: {str(e)}"
            )

    def _download_local(self, file_path: str) -> StorageResult:
        """Download file from local storage"""
        try:
            if not os.path.exists(file_path):
                return StorageResult(
                    success=False,
                    error_message="File not found"
                )
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Determine content type
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # Extract filename
            filename = os.path.basename(file_path)
            
            return StorageResult(
                success=True,
                content=content,
                content_type=content_type,
                filename=filename
            )
            
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"Local download failed: {str(e)}"
            )

    def _download_s3(self, s3_key: str) -> StorageResult:
        """Download file from S3 storage"""
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            content = response['Body'].read()
            content_type = response.get('ContentType', 'application/octet-stream')
            filename = os.path.basename(s3_key)
            
            return StorageResult(
                success=True,
                content=content,
                content_type=content_type,
                filename=filename
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                return StorageResult(
                    success=False,
                    error_message="File not found"
                )
            else:
                return StorageResult(
                    success=False,
                    error_message=f"S3 download failed: {str(e)}"
                )
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"S3 download failed: {str(e)}"
            )

    def delete_file(self, file_path: str) -> StorageResult:
        """
        Delete a file from the configured storage backend.
        
        Args:
            file_path (str): Path to the file (local path or S3 key)
        
        Returns:
            StorageResult: Result object indicating success or error
        """
        try:
            if self.storage_type == 'local':
                return self._delete_local(file_path)
            elif self.storage_type == 's3':
                return self._delete_s3(file_path)
                
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"Delete failed: {str(e)}"
            )

    def _delete_local(self, file_path: str) -> StorageResult:
        """Delete file from local storage"""
        try:
            if not os.path.exists(file_path):
                return StorageResult(
                    success=False,
                    error_message="File not found"
                )
            
            os.remove(file_path)
            
            return StorageResult(success=True)
            
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"Local delete failed: {str(e)}"
            )

    def _delete_s3(self, s3_key: str) -> StorageResult:
        """Delete file from S3 storage"""
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
            
            return StorageResult(success=True)
            
        except ClientError as e:
            return StorageResult(
                success=False,
                error_message=f"S3 delete failed: {str(e)}"
            )
        except Exception as e:
            return StorageResult(
                success=False,
                error_message=f"S3 delete failed: {str(e)}"
            )

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in the storage backend.
        
        Args:
            file_path (str): Path to the file (local path or S3 key)
        
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            if self.storage_type == 'local':
                return os.path.exists(file_path)
            elif self.storage_type == 's3':
                try:
                    self.s3_client.head_object(Bucket=self.s3_bucket, Key=file_path)
                    return True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchKey':
                        return False
                    raise
        except Exception:
            return False

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file in the storage backend.
        
        Args:
            file_path (str): Path to the file (local path or S3 key)
        
        Returns:
            Dict[str, Any]: File information including size, modified time, etc.
        """
        try:
            if self.storage_type == 'local':
                return self._get_local_file_info(file_path)
            elif self.storage_type == 's3':
                return self._get_s3_file_info(file_path)
        except Exception as e:
            return {
                'exists': False,
                'error': str(e)
            }

    def _get_local_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information for local storage"""
        if not os.path.exists(file_path):
            return {'exists': False}
        
        stat = os.stat(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        
        return {
            'exists': True,
            'size': stat.st_size,
            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'content_type': content_type
        }

    def _get_s3_file_info(self, s3_key: str) -> Dict[str, Any]:
        """Get file information for S3 storage"""
        try:
            response = self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
            
            return {
                'exists': True,
                'size': response['ContentLength'],
                'modified_time': response['LastModified'],
                'content_type': response.get('ContentType', 'application/octet-stream')
            }
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return {'exists': False}
            raise

    def _generate_storage_path(self, user_id: int, filename: str) -> str:
        """
        Generate storage path for a file.
        
        Args:
            user_id (int): ID of the user
            filename (str): Filename
        
        Returns:
            str: Storage path (local path or S3 key)
        """
        if self.storage_type == 'local':
            return os.path.join(
                self.local_storage_path,
                'users',
                str(user_id),
                filename
            )
        elif self.storage_type == 's3':
            return f"users/{user_id}/{filename}"

    def _get_file_url(self, file_path: str) -> str:
        """
        Generate URL for accessing a file.
        
        Args:
            file_path (str): Path to the file (local path or S3 key)
        
        Returns:
            str: URL for accessing the file
        """
        if self.storage_type == 'local':
            # Generate relative path from storage root
            rel_path = os.path.relpath(file_path, self.local_storage_path)
            # Convert to URL-safe format
            url_path = rel_path.replace('\\', '/')
            # Extract file ID from path for URL generation
            # Format: users/{user_id}/{filename}
            path_parts = url_path.split('/')
            if len(path_parts) >= 3 and path_parts[0] == 'users':
                user_id = path_parts[1]
                filename = path_parts[2]
                # Generate unique file ID (could be based on path hash or database ID)
                file_id = str(abs(hash(file_path)) % (10 ** 8))  # Simple hash-based ID
                return f"{self.base_url}/api/files/{file_id}/download"
            else:
                return f"{self.base_url}/api/files/download"
                
        elif self.storage_type == 's3':
            # Generate presigned URL for S3
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.s3_bucket, 'Key': file_path},
                    ExpiresIn=3600  # 1 hour
                )
                return url
            except Exception as e:
                return f"Error generating S3 URL: {str(e)}"