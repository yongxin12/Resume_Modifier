"""
Simplified test for File Upload API endpoint
"""

import pytest
from io import BytesIO
from unittest.mock import patch
from app.utils.file_validator import ValidationResult
from app.services.file_storage_service import StorageResult  
from app.services.file_processing_service import ProcessingResult


def test_upload_endpoint_exists(client):
    """Test that the upload endpoint exists"""
    # Should return 401 without auth, not 404
    response = client.post('/api/files/upload')
    assert response.status_code == 401


def test_upload_requires_authentication(client):
    """Test that upload requires authentication"""
    response = client.post('/api/files/upload')
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data  # JWT decorator returns error field, not success


@patch('app.utils.file_validator.FileValidator.validate_file')
@patch('app.services.file_storage_service.FileStorageService.upload_file')
@patch('app.services.file_processing_service.FileProcessingService.process_file')
def test_upload_pdf_success(mock_process, mock_storage, mock_validate, client, authenticated_headers):
    """Test successful PDF upload"""
    # Mock validator success
    validation_result = ValidationResult()
    validation_result.is_valid = True
    validation_result.sanitized_filename = "secure_test.pdf"
    validation_result.file_type = "pdf"
    mock_validate.return_value = validation_result
    
    # Mock storage success
    storage_result = StorageResult(
        success=True,
        storage_type='local',
        file_path='/storage/test.pdf',
        file_size=1000,
        url='http://localhost:5001/api/files/123/download'
    )
    mock_storage.return_value = storage_result
    
    # Mock processing success
    processing_result = ProcessingResult(
        success=True,
        text="Sample text",
        file_type="pdf",
        metadata={'word_count': 2}
    )
    mock_process.return_value = processing_result
    
    # Test the upload
    pdf_content = b"%PDF-1.4\ntest content"
    response = client.post(
        '/api/files/upload',
        data={'file': (BytesIO(pdf_content), 'test.pdf')},
        headers=authenticated_headers,
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert 'file' in data
    assert data['file']['original_filename'] == 'test.pdf'
    # Check that stored_filename uses the user_id_timestamp_filename pattern
    stored_filename = data['file']['stored_filename']
    import re
    assert re.match(r'user_\d+_\d+_secure_test\.pdf', stored_filename), f"Expected user_{{id}}_{{timestamp}}_secure_test.pdf pattern, got: {stored_filename}"
    assert data['file']['extracted_text'] == 'Sample text'