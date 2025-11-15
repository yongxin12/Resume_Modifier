"""
FileValidator utility class for validating uploaded resume files
Supports PDF and DOCX file validation with security checks
"""

import hashlib
import mimetypes
import os
import re
import uuid
from typing import List, Dict, Any, Optional, Union
import zipfile
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ValidationResult:
    """Result object containing validation outcome and details"""
    
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.file_type: Optional[str] = None
        self.mime_type: Optional[str] = None
        self.detected_mime_type: Optional[str] = None
        self.file_size: Optional[int] = None
        self.sanitized_filename: Optional[str] = None
        self.secure_filename: Optional[str] = None
        self.file_hash: Optional[str] = None
    
    def add_error(self, error: str):
        """Add an error and mark validation as invalid"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning (doesn't affect validity)"""
        self.warnings.append(warning)
    
    def __str__(self):
        result = f"ValidationResult(valid={self.is_valid}"
        if self.errors:
            result += f", errors={self.errors}"
        if self.warnings:
            result += f", warnings={self.warnings}"
        result += ")"
        return result


class FileValidator:
    """
    Comprehensive file validator for resume uploads
    Validates file types, sizes, content, and security
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        'allowed_extensions': ['pdf', 'docx'],
        'max_file_size_mb': 10,  # 10MB as per API specification
        'virus_scanning_enabled': False,
        'content_validation_enabled': True,
        'filename_security_checks': True
    }
    
    # MIME type mappings
    MIME_TYPES = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    # File signature patterns for content validation
    FILE_SIGNATURES = {
        'pdf': [
            b'%PDF-1.0',
            b'%PDF-1.1',
            b'%PDF-1.2',
            b'%PDF-1.3',
            b'%PDF-1.4',
            b'%PDF-1.5',
            b'%PDF-1.6',
            b'%PDF-1.7',
            b'%PDF-2.0'
        ],
        'docx': [
            b'PK\x03\x04'  # ZIP file signature (DOCX is a ZIP archive)
        ]
    }
    
    # Windows reserved filenames
    WINDOWS_RESERVED_NAMES = {
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize FileValidator with configuration
        
        Args:
            config: Optional configuration dictionary to override defaults
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        # If custom config provided, prioritize it over centralized config
        if config:
            self.config.update(config)
            # Use custom config values directly
            self.max_file_size_mb = self.config['max_file_size_mb']
            self.allowed_extensions = self.config['allowed_extensions']
        else:
            # Import and get upload limits from centralized config only if no custom config
            try:
                from app.utils.storage_config import StorageConfigManager
                upload_limits = StorageConfigManager.get_upload_limits()
                
                # Override defaults with centralized configuration
                self.max_file_size_mb = upload_limits['max_file_size'] // (1024 * 1024)  # Convert bytes to MB
                self.allowed_mime_types = upload_limits['allowed_mime_types']
                
                # Map MIME types to extensions
                mime_to_ext = {
                    'application/pdf': 'pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx'
                }
                self.allowed_extensions = [mime_to_ext.get(mime, '') for mime in self.allowed_mime_types if mime_to_ext.get(mime)]
                
            except ImportError:
                # Fallback to defaults if storage config not available
                self.max_file_size_mb = self.config['max_file_size_mb']
                self.allowed_extensions = self.config['allowed_extensions']
        
        # Set other properties from config
        self.virus_scanning_enabled = self.config['virus_scanning_enabled']
        self.content_validation_enabled = self.config['content_validation_enabled']
        self.filename_security_checks = self.config['filename_security_checks']
    
    def validate_file(self, file_storage: FileStorage, max_size_mb: Optional[int] = None, 
                     scan_viruses: bool = False) -> ValidationResult:
        """
        Validate a single uploaded file
        
        Args:
            file_storage: Werkzeug FileStorage object
            max_size_mb: Optional file size limit (overrides default)
            scan_viruses: Whether to scan for viruses
            
        Returns:
            ValidationResult object with validation outcome
        """
        result = ValidationResult()
        
        # Use provided size limit or default
        size_limit = max_size_mb if max_size_mb is not None else self.max_file_size_mb
        
        try:
            # Basic filename validation
            if not self._validate_filename(file_storage.filename, result):
                return result
            
            # File size validation
            if not self._validate_file_size(file_storage, size_limit, result):
                return result
            
            # File extension validation
            file_extension = self._get_file_extension(file_storage.filename)
            if not self._validate_file_extension(file_extension, result):
                return result
            
            # Set file type
            result.file_type = file_extension
            result.mime_type = file_storage.content_type
            
            # Content validation
            if self.content_validation_enabled:
                self._validate_file_content(file_storage, file_extension, result)
            
            # Security validation
            if self.filename_security_checks:
                self._validate_filename_security(file_storage.filename, result)
            
            # Virus scanning
            if scan_viruses or self.virus_scanning_enabled:
                if not self._scan_for_viruses(file_storage):
                    result.add_error("Virus or malware detected in file")
                    return result
            
            # Generate secure filename and hash if validation passed
            if result.is_valid:
                result.sanitized_filename = self.sanitize_filename(file_storage.filename)
                result.secure_filename = self.generate_secure_filename(file_storage.filename)
                result.file_hash = self.calculate_file_hash(file_storage)
        
        except Exception as e:
            result.add_error(f"Validation error: {str(e)}")
        
        return result
    
    def validate_multiple_files(self, files: List[FileStorage], max_size_mb: Optional[int] = None) -> List[ValidationResult]:
        """
        Validate multiple files
        
        Args:
            files: List of FileStorage objects
            max_size_mb: Optional file size limit
            
        Returns:
            List of ValidationResult objects
        """
        return [self.validate_file(file, max_size_mb) for file in files]
    
    def _validate_filename(self, filename: Optional[str], result: ValidationResult) -> bool:
        """Validate filename is present and not empty"""
        if not filename:
            result.add_error("Filename is required")
            return False
        
        if filename.strip() == "":
            result.add_error("Filename is required")
            return False
        
        return True
    
    def _validate_file_size(self, file_storage: FileStorage, max_size_mb: int, result: ValidationResult) -> bool:
        """Validate file size is within limits"""
        # Get file size
        file_storage.stream.seek(0, 2)  # Seek to end
        file_size = file_storage.stream.tell()
        file_storage.stream.seek(0)  # Reset to beginning
        
        result.file_size = file_size
        
        # Check if file is empty
        if file_size == 0:
            result.add_error("File is empty")
            return False
        
        # Check size limit
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            result.add_error(f"File size ({file_size / 1024 / 1024:.1f} MB) exceeds maximum limit ({max_size_mb} MB)")
            return False
        
        return True
    
    def _get_file_extension(self, filename: str) -> Optional[str]:
        """Extract and normalize file extension"""
        if '.' not in filename:
            return None
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension if extension else None
    
    def _validate_file_extension(self, extension: Optional[str], result: ValidationResult) -> bool:
        """Validate file extension is allowed"""
        if not extension:
            result.add_error("No file extension found")
            return False
        
        if extension not in self.allowed_extensions:
            result.add_error(f"Invalid file type '{extension}'. Allowed types: {', '.join(self.allowed_extensions)}")
            return False
        
        return True
    
    def _validate_file_content(self, file_storage: FileStorage, file_extension: str, result: ValidationResult):
        """Validate file content matches extension"""
        try:
            # Read file header for signature validation
            file_storage.stream.seek(0)
            header = file_storage.stream.read(1024)  # Read first 1KB
            file_storage.stream.seek(0)  # Reset
            
            # Detect actual MIME type
            detected_mime = self._detect_mime_type(header, file_extension)
            result.detected_mime_type = detected_mime
            
            # Check MIME type mismatch
            expected_mime = self.MIME_TYPES.get(file_extension)
            if result.mime_type and result.mime_type != expected_mime and detected_mime:
                result.add_warning(f"MIME type mismatch detected. Expected: {expected_mime}, Got: {result.mime_type}, Detected: {detected_mime}")
            
            # Validate file signature
            if file_extension in self.FILE_SIGNATURES:
                valid_signature = any(header.startswith(sig) for sig in self.FILE_SIGNATURES[file_extension])
                
                if not valid_signature:
                    if file_extension == 'pdf':
                        result.add_error("Invalid or corrupted PDF file")
                    elif file_extension == 'docx':
                        # For DOCX, also try to validate ZIP structure
                        if not self._validate_docx_structure(file_storage):
                            result.add_error("Invalid or corrupted DOCX file")
                    else:
                        result.add_error(f"Invalid or corrupted {file_extension.upper()} file")
        
        except Exception as e:
            result.add_error(f"Content validation failed: {str(e)}")
    
    def _detect_mime_type(self, content: bytes, extension: str) -> Optional[str]:
        """Detect MIME type from file content"""
        # Check file signatures
        for file_type, signatures in self.FILE_SIGNATURES.items():
            if any(content.startswith(sig) for sig in signatures):
                return self.MIME_TYPES.get(file_type)
        
        # Fallback to extension-based detection
        return self.MIME_TYPES.get(extension)
    
    def _validate_docx_structure(self, file_storage: FileStorage) -> bool:
        """Validate DOCX file structure (ZIP with required files)"""
        try:
            file_storage.stream.seek(0)
            
            # Try to open as ZIP file
            with zipfile.ZipFile(file_storage.stream, 'r') as zip_file:
                # Check for required DOCX files
                required_files = ['[Content_Types].xml', 'word/document.xml']
                file_list = zip_file.namelist()
                
                return all(req_file in file_list for req_file in required_files)
        
        except (zipfile.BadZipFile, Exception):
            return False
        
        finally:
            file_storage.stream.seek(0)
    
    def _validate_filename_security(self, filename: str, result: ValidationResult):
        """Validate filename for security issues"""
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            result.add_error("Invalid filename: contains path traversal characters")
            return
        
        # Check for script injection attempts
        dangerous_chars = ['<', '>', ';', '&', '|', '`', '$']
        if any(char in filename for char in dangerous_chars):
            result.add_error("Invalid filename: contains potentially dangerous characters")
            return
        
        # Check Windows reserved names
        name_without_ext = filename.rsplit('.', 1)[0].lower()
        if name_without_ext in self.WINDOWS_RESERVED_NAMES:
            result.add_error(f"Invalid filename: '{name_without_ext}' is a reserved system name")
            return
    
    def _scan_for_viruses(self, file_storage: FileStorage) -> bool:
        """
        Placeholder for virus scanning functionality
        In production, integrate with ClamAV or similar
        """
        # This is a mock implementation
        # In production, you would integrate with actual virus scanning tools
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing/replacing unsafe characters
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return ""
        
        # Convert to lowercase
        filename = filename.lower()
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Remove or replace unsafe characters
        filename = re.sub(r'[^\w\-_\.]', '', filename)
        
        # Remove multiple consecutive dots or underscores
        filename = re.sub(r'\.{2,}', '.', filename)
        filename = re.sub(r'_{2,}', '_', filename)
        
        # Ensure it doesn't start or end with dots or underscores
        filename = filename.strip('._')
        
        return filename
    
    def generate_secure_filename(self, original_filename: str) -> str:
        """
        Generate a secure filename using UUID
        
        Args:
            original_filename: Original filename
            
        Returns:
            Secure UUID-based filename with original extension
        """
        if not original_filename:
            return str(uuid.uuid4())
        
        # Extract extension
        extension = ""
        if '.' in original_filename:
            extension = '.' + original_filename.rsplit('.', 1)[1].lower()
        
        # Generate UUID-based filename
        secure_name = str(uuid.uuid4()) + extension
        
        return secure_name
    
    def calculate_file_hash(self, file_storage: FileStorage) -> str:
        """
        Calculate SHA-256 hash of file content for deduplication
        
        Args:
            file_storage: FileStorage object
            
        Returns:
            SHA-256 hash as hexadecimal string
        """
        sha256_hash = hashlib.sha256()
        
        # Reset stream position
        file_storage.stream.seek(0)
        
        # Read and hash file content in chunks
        while chunk := file_storage.stream.read(8192):
            sha256_hash.update(chunk)
        
        # Reset stream position
        file_storage.stream.seek(0)
        
        return sha256_hash.hexdigest()