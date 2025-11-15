"""
Storage Configuration Management for File Services
Centralizes all storage configuration and settings management

Author: Resume Modifier Backend Team  
Date: October 2024
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class StorageConfiguration:
    """
    Data class for storage configuration settings
    """
    storage_type: str
    local_storage_path: str
    base_url: str
    s3_bucket: str
    s3_region: str
    aws_access_key_id: str
    aws_secret_access_key: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for service initialization"""
        return {
            'storage_type': self.storage_type,
            'local_storage_path': self.local_storage_path,
            'base_url': self.base_url,
            's3_bucket': self.s3_bucket,
            's3_region': self.s3_region,
            'aws_access_key_id': self.aws_access_key_id,
            'aws_secret_access_key': self.aws_secret_access_key
        }


class StorageConfigManager:
    """
    Centralized storage configuration manager
    Handles environment variable loading and configuration validation
    """
    
    @staticmethod
    def get_storage_config() -> StorageConfiguration:
        """
        Get storage configuration from environment variables
        
        Returns:
            StorageConfiguration: Configuration object with all storage settings
            
        Raises:
            ValueError: If required configuration is missing or invalid
        """
        # Get storage type with validation
        storage_type = os.getenv('FILE_STORAGE_TYPE', 'local').lower()
        if storage_type not in ['local', 's3']:
            raise ValueError(f"Invalid storage type: {storage_type}. Must be 'local' or 's3'")
        
        # Local storage configuration
        local_storage_path = os.getenv('LOCAL_STORAGE_PATH', '/tmp/resume_files')
        base_url = os.getenv('BASE_URL', 'http://localhost:5001')
        
        # S3 storage configuration
        s3_bucket = os.getenv('AWS_S3_BUCKET', '')
        s3_region = os.getenv('AWS_S3_REGION', 'us-east-1')
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID', '')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        
        # Validate configuration based on storage type
        if storage_type == 'local':
            if not local_storage_path:
                raise ValueError("LOCAL_STORAGE_PATH is required for local storage")
                
        elif storage_type == 's3':
            required_s3_vars = {
                'AWS_S3_BUCKET': s3_bucket,
                'AWS_ACCESS_KEY_ID': aws_access_key_id,
                'AWS_SECRET_ACCESS_KEY': aws_secret_access_key
            }
            
            missing_vars = [var_name for var_name, var_value in required_s3_vars.items() if not var_value]
            if missing_vars:
                raise ValueError(f"Missing required S3 configuration: {', '.join(missing_vars)}")
        
        return StorageConfiguration(
            storage_type=storage_type,
            local_storage_path=local_storage_path,
            base_url=base_url,
            s3_bucket=s3_bucket,
            s3_region=s3_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
    
    @staticmethod
    def get_storage_config_dict() -> Dict[str, Any]:
        """
        Get storage configuration as dictionary for direct service use
        
        Returns:
            Dict[str, Any]: Configuration dictionary ready for FileStorageService
        """
        # Check for cloud storage environment variable
        storage_type = os.getenv('FILE_STORAGE_TYPE', 'local').lower()
        if storage_type == 'cloud' or os.getenv('STORAGE_TYPE') == 'cloud':
            storage_type = 'cloud'
        
        config = StorageConfigManager.get_storage_config()
        config_dict = config.to_dict()
        
        # Override storage type if cloud is specifically requested
        if storage_type == 'cloud':
            config_dict['storage_type'] = 'cloud'
            # Add cloud-specific configuration fields expected by tests
            config_dict['cloud_storage_bucket'] = os.getenv('CLOUD_STORAGE_BUCKET', config_dict.get('s3_bucket', ''))
            config_dict['cloud_storage_provider'] = os.getenv('CLOUD_STORAGE_PROVIDER', 'aws')
        
        return config_dict
    
    @staticmethod
    def validate_storage_config() -> bool:
        """
        Validate current storage configuration
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            StorageConfigManager.get_storage_config()
            return True
        except (ValueError, KeyError) as e:
            print(f"Storage configuration validation failed: {str(e)}")
            return False
    
    @staticmethod
    def get_upload_limits() -> Dict[str, Any]:
        """
        Get file upload configuration limits
        
        Returns:
            Dict[str, Any]: Upload limits and restrictions
        """
        return {
            'max_file_size': int(os.getenv('MAX_FILE_SIZE', '10485760')),  # 10MB default
            'allowed_mime_types': os.getenv(
                'ALLOWED_MIME_TYPES', 
                'application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ).split(','),
            'max_files_per_user': int(os.getenv('MAX_FILES_PER_USER', '100')),
            'upload_timeout': int(os.getenv('UPLOAD_TIMEOUT_SECONDS', '300'))  # 5 minutes default
        }
    
    @staticmethod
    def get_processing_config() -> Dict[str, Any]:
        """
        Get file processing configuration
        
        Returns:
            Dict[str, Any]: Processing configuration settings
        """
        return {
            'max_text_length': int(os.getenv('MAX_EXTRACTED_TEXT_LENGTH', '100000')),  # 100KB text
            'processing_timeout': int(os.getenv('PROCESSING_TIMEOUT_SECONDS', '60')),  # 1 minute
            'enable_ocr': os.getenv('ENABLE_OCR', 'false').lower() == 'true',
            'enable_language_detection': os.getenv('ENABLE_LANGUAGE_DETECTION', 'true').lower() == 'true'
        }


# Global instance for easy access
storage_config_manager = StorageConfigManager()