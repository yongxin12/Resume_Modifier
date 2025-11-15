"""
Comprehensive test suite for FileValidator utility class
Following Test-Driven Development approach
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from io import BytesIO
from werkzeug.datastructures import FileStorage
from app.utils.file_validator import FileValidator, ValidationError


class TestFileValidator:
    """Test suite for FileValidator utility class"""

    def test_validate_file_valid_pdf(self):
        """Test validation of a valid PDF file"""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        file_storage = FileStorage(
            stream=BytesIO(pdf_content),
            filename="test_resume.pdf",
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is True
        assert result.file_type == 'pdf'
        assert result.mime_type == 'application/pdf'
        assert result.file_size == len(pdf_content)
        assert result.errors == []

    def test_validate_file_valid_docx(self):
        """Test validation of a valid DOCX file"""
        # Create a minimal valid DOCX file (ZIP with proper structure)
        docx_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00" + b"\x00" * 50  # Minimal ZIP header
        file_storage = FileStorage(
            stream=BytesIO(docx_content),
            filename="test_resume.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is True
        assert result.file_type == 'docx'
        assert result.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        assert result.file_size == len(docx_content)
        assert result.errors == []

    def test_validate_file_invalid_extension(self):
        """Test validation fails for invalid file extensions"""
        file_storage = FileStorage(
            stream=BytesIO(b"some content"),
            filename="test_resume.txt",
            content_type="text/plain"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is False
        assert 'Invalid file type' in str(result.errors)
        assert result.file_type is None

    def test_validate_file_no_extension(self):
        """Test validation fails for files without extensions"""
        file_storage = FileStorage(
            stream=BytesIO(b"some content"),
            filename="test_resume",
            content_type="application/octet-stream"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is False
        assert 'No file extension found' in str(result.errors)

    def test_validate_file_empty_filename(self):
        """Test validation fails for empty filename"""
        file_storage = FileStorage(
            stream=BytesIO(b"some content"),
            filename="",
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is False
        assert 'Filename is required' in str(result.errors)

    def test_validate_file_none_filename(self):
        """Test validation fails for None filename"""
        file_storage = FileStorage(
            stream=BytesIO(b"some content"),
            filename=None,
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is False
        assert 'Filename is required' in str(result.errors)

    def test_validate_file_size_exceeds_limit(self):
        """Test validation fails when file size exceeds limit"""
        large_content = b"x" * (2 * 1024 * 1024)  # 2MB content
        file_storage = FileStorage(
            stream=BytesIO(large_content),
            filename="large_resume.pdf",
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=1)  # 1MB limit
        
        assert result.is_valid is False
        assert 'exceeds maximum limit' in str(result.errors)
        assert result.file_size == len(large_content)

    def test_validate_file_zero_size(self):
        """Test validation fails for empty files"""
        file_storage = FileStorage(
            stream=BytesIO(b""),
            filename="empty_resume.pdf",
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is False
        assert 'File is empty' in str(result.errors)
        assert result.file_size == 0

    def test_validate_mime_type_mismatch(self):
        """Test validation handles MIME type mismatch with file extension"""
        # PDF content but wrong MIME type
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        file_storage = FileStorage(
            stream=BytesIO(pdf_content),
            filename="test_resume.pdf",
            content_type="text/plain"  # Wrong MIME type
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        # Should detect actual content type and warn about mismatch
        assert result.is_valid is True  # Still valid because content is correct
        assert result.file_type == 'pdf'
        assert 'MIME type mismatch detected' in str(result.warnings)

    def test_validate_malicious_filename(self):
        """Test validation handles potentially malicious filenames"""
        malicious_filenames = [
            "../../../etc/passwd.pdf",
            "..\\..\\windows\\system32\\config.pdf",
            "resume;rm -rf /.pdf",
            "resume<script>alert('xss')</script>.pdf",
            "con.pdf",  # Windows reserved name
            "prn.docx",  # Windows reserved name
        ]
        
        validator = FileValidator()
        
        for filename in malicious_filenames:
            file_storage = FileStorage(
                stream=BytesIO(b"%PDF-1.4\ntest"),
                filename=filename,
                content_type="application/pdf"
            )
            
            result = validator.validate_file(file_storage, max_size_mb=10)
            
            # Should detect security issues
            assert result.is_valid is False
            assert any('security' in str(error).lower() or 'invalid filename' in str(error).lower() 
                     for error in result.errors)

    def test_validate_file_content_type_detection(self):
        """Test automatic content type detection from file content"""
        # Test PDF detection
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj"
        file_storage = FileStorage(
            stream=BytesIO(pdf_content),
            filename="test.pdf",
            content_type="application/octet-stream"  # Generic type
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is True
        assert result.detected_mime_type == 'application/pdf'
        assert result.file_type == 'pdf'

    def test_validate_corrupted_pdf(self):
        """Test validation of corrupted PDF file"""
        corrupted_content = b"This is not a valid PDF file content"
        file_storage = FileStorage(
            stream=BytesIO(corrupted_content),
            filename="corrupted.pdf",
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is False
        assert 'Invalid or corrupted PDF file' in str(result.errors)

    def test_validate_corrupted_docx(self):
        """Test validation of corrupted DOCX file"""
        corrupted_content = b"This is not a valid DOCX file content"
        file_storage = FileStorage(
            stream=BytesIO(corrupted_content),
            filename="corrupted.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        validator = FileValidator()
        result = validator.validate_file(file_storage, max_size_mb=10)
        
        assert result.is_valid is False
        assert 'Invalid or corrupted DOCX file' in str(result.errors)

    def test_sanitize_filename(self):
        """Test filename sanitization functionality"""
        validator = FileValidator()
        
        test_cases = [
            ("normal_file.pdf", "normal_file.pdf"),
            ("file with spaces.pdf", "file_with_spaces.pdf"),
            ("file@#$%^&*().pdf", "file.pdf"),
            ("UPPERCASE.PDF", "uppercase.pdf"),
            ("file..pdf", "file.pdf"),
            ("résumé_français.pdf", "résumé_français.pdf"),  # Unicode support
            ("file___multiple___underscores.pdf", "file_multiple_underscores.pdf"),
        ]
        
        for input_filename, expected_output in test_cases:
            sanitized = validator.sanitize_filename(input_filename)
            assert sanitized == expected_output

    def test_generate_secure_filename(self):
        """Test secure filename generation"""
        validator = FileValidator()
        
        original_filename = "my resume.pdf"
        secure_filename = validator.generate_secure_filename(original_filename)
        
        # Should be a UUID-based filename with original extension
        assert secure_filename.endswith('.pdf')
        assert len(secure_filename) > 10  # UUID + extension
        assert ' ' not in secure_filename
        assert secure_filename != original_filename

    def test_calculate_file_hash(self):
        """Test file hash calculation for deduplication"""
        content = b"Test file content for hashing"
        file_storage = FileStorage(
            stream=BytesIO(content),
            filename="test.pdf",
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        file_hash = validator.calculate_file_hash(file_storage)
        
        # Should return a SHA-256 hash
        assert len(file_hash) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in file_hash)
        
        # Same content should produce same hash
        file_storage2 = FileStorage(
            stream=BytesIO(content),
            filename="different_name.pdf",
            content_type="application/pdf"
        )
        file_hash2 = validator.calculate_file_hash(file_storage2)
        assert file_hash == file_hash2

    def test_validate_file_with_virus_scan_mock(self):
        """Test virus scanning integration (mocked)"""
        file_storage = FileStorage(
            stream=BytesIO(b"%PDF-1.4\ntest content"),
            filename="test.pdf",
            content_type="application/pdf"
        )
        
        validator = FileValidator()
        
        # Mock virus scanner to return clean
        with patch.object(validator, '_scan_for_viruses', return_value=True):
            result = validator.validate_file(file_storage, max_size_mb=10, scan_viruses=True)
            assert result.is_valid is True
        
        # Mock virus scanner to detect threat
        with patch.object(validator, '_scan_for_viruses', return_value=False):
            result = validator.validate_file(file_storage, max_size_mb=10, scan_viruses=True)
            assert result.is_valid is False
            assert 'Virus or malware detected' in str(result.errors)

    def test_validation_result_class(self):
        """Test ValidationResult class functionality"""
        from app.utils.file_validator import ValidationResult
        
        result = ValidationResult()
        
        # Test initial state
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        
        # Test adding errors
        result.add_error("Test error")
        assert result.is_valid is False
        assert "Test error" in result.errors
        
        # Test adding warnings
        result.add_warning("Test warning")
        assert "Test warning" in result.warnings
        
        # Test string representation
        result_str = str(result)
        assert "Test error" in result_str
        assert "Test warning" in result_str

    def test_custom_validation_error_exception(self):
        """Test custom ValidationError exception"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test validation error")
        
        assert str(exc_info.value) == "Test validation error"

    def test_validate_multiple_files(self):
        """Test validation of multiple files at once"""
        files = []
        
        # Valid PDF
        pdf_content = b"%PDF-1.4\ntest"
        files.append(FileStorage(
            stream=BytesIO(pdf_content),
            filename="resume1.pdf",
            content_type="application/pdf"
        ))
        
        # Valid DOCX
        docx_content = b"PK\x03\x04" + b"\x00" * 50
        files.append(FileStorage(
            stream=BytesIO(docx_content),
            filename="resume2.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ))
        
        # Invalid file
        files.append(FileStorage(
            stream=BytesIO(b"invalid"),
            filename="resume3.txt",
            content_type="text/plain"
        ))
        
        validator = FileValidator()
        results = validator.validate_multiple_files(files, max_size_mb=10)
        
        assert len(results) == 3
        assert results[0].is_valid is True  # PDF
        assert results[1].is_valid is True  # DOCX
        assert results[2].is_valid is False  # TXT

    def test_configuration_defaults(self):
        """Test FileValidator configuration and defaults"""
        validator = FileValidator()
        
        # Test default configuration
        assert 'pdf' in validator.allowed_extensions
        assert 'docx' in validator.allowed_extensions
        assert validator.max_file_size_mb == 10  # Default 10MB from storage config
        assert validator.virus_scanning_enabled is False  # Default disabled
        
    def test_custom_configuration(self):
        """Test FileValidator with custom configuration"""
        config = {
            'max_file_size_mb': 25,
            'allowed_extensions': ['pdf'],  # Only PDF
            'virus_scanning_enabled': True
        }
        
        validator = FileValidator(config)
        
        assert validator.max_file_size_mb == 25
        assert validator.allowed_extensions == ['pdf']
        assert validator.virus_scanning_enabled is True
        
        # Test DOCX should now be rejected
        docx_file = FileStorage(
            stream=BytesIO(b"PK\x03\x04" + b"\x00" * 50),
            filename="test.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        result = validator.validate_file(docx_file, max_size_mb=25)
        assert result.is_valid is False
        assert 'Invalid file type' in str(result.errors)