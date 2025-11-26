"""
Unit tests for ThumbnailService
Tests thumbnail generation, storage management, and error handling
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from PIL import Image
import io

# Add core to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../core'))

from app.services.thumbnail_service import ThumbnailService


class TestThumbnailService:
    """Test suite for ThumbnailService class"""
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_pdf_path(self, temp_directory):
        """Create a sample PDF file for testing"""
        # This would create a real PDF file in practice
        # For now, we'll mock the PDF processing
        pdf_path = os.path.join(temp_directory, "sample.pdf")
        
        # Create a dummy file (in real implementation, this would be a valid PDF)
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4 dummy pdf content')
        
        return pdf_path
    
    @pytest.fixture
    def invalid_pdf_path(self, temp_directory):
        """Create an invalid PDF file for testing"""
        invalid_path = os.path.join(temp_directory, "invalid.pdf")
        with open(invalid_path, 'w') as f:
            f.write("This is not a PDF file")
        return invalid_path
    
    def test_thumbnail_size_constants(self):
        """Test that thumbnail size constants are properly defined"""
        assert ThumbnailService.THUMBNAIL_SIZE == (150, 200)
        assert ThumbnailService.THUMBNAIL_QUALITY == 85
        assert ThumbnailService.THUMBNAIL_FORMAT == 'JPEG'
    
    def test_get_thumbnail_path(self, app, temp_directory):
        """Test thumbnail path generation"""
        with app.app_context():
            with patch('app.services.thumbnail_service.current_app') as mock_app:
                mock_app.config = {'UPLOAD_FOLDER': temp_directory}
                
                path = ThumbnailService.get_thumbnail_path(42)
                expected_path = os.path.join(temp_directory, 'thumbnails', '42.jpg')
                
                assert path == expected_path
    
    def test_ensure_thumbnail_directory_creates_directory(self, app, temp_directory):
        """Test that thumbnail directory is created if it doesn't exist"""
        with app.app_context():
            with patch('app.services.thumbnail_service.current_app') as mock_app:
                mock_app.config = {'UPLOAD_FOLDER': temp_directory}
                
                thumbnail_dir = os.path.join(temp_directory, 'thumbnails')
                assert not os.path.exists(thumbnail_dir)
                
                ThumbnailService.ensure_thumbnail_directory()
                
                assert os.path.exists(thumbnail_dir)
                assert os.path.isdir(thumbnail_dir)
    
    def test_ensure_thumbnail_directory_existing_directory(self, app, temp_directory):
        """Test that existing thumbnail directory is not modified"""
        with app.app_context():
            with patch('app.services.thumbnail_service.current_app') as mock_app:
                mock_app.config = {'UPLOAD_FOLDER': temp_directory}
                
                thumbnail_dir = os.path.join(temp_directory, 'thumbnails')
                os.makedirs(thumbnail_dir)
                
                # Should not raise an exception
                ThumbnailService.ensure_thumbnail_directory()
                
                assert os.path.exists(thumbnail_dir)
    
    @patch('app.services.thumbnail_service.pdf2image.convert_from_path')
    def test_generate_thumbnail_success(self, mock_convert, temp_directory, sample_pdf_path):
        """Test successful thumbnail generation"""
        # Mock PDF conversion
        mock_image = MagicMock()
        mock_image.size = (210, 297)  # A4 size
        mock_convert.return_value = [mock_image]
        
        # Mock image resize and save
        mock_resized = MagicMock()
        mock_image.resize.return_value = mock_resized
        
        output_path = os.path.join(temp_directory, 'test_thumbnail.jpg')
        
        result = ThumbnailService.generate_thumbnail(sample_pdf_path, output_path)
        
        assert result is True
        mock_convert.assert_called_once_with(
            sample_pdf_path,
            first_page=1,
            last_page=1,
            dpi=150,
            fmt='JPEG'
        )
        mock_image.resize.assert_called_once_with((150, 200), Image.Resampling.LANCZOS)
        mock_resized.save.assert_called_once_with(
            output_path,
            'JPEG',
            quality=85,
            optimize=True
        )
    
    @patch('app.services.thumbnail_service.pdf2image.convert_from_path')
    def test_generate_thumbnail_pdf_conversion_error(self, mock_convert, temp_directory, sample_pdf_path):
        """Test thumbnail generation with PDF conversion error"""
        mock_convert.side_effect = Exception("PDF conversion failed")
        
        output_path = os.path.join(temp_directory, 'test_thumbnail.jpg')
        
        result = ThumbnailService.generate_thumbnail(sample_pdf_path, output_path)
        
        assert result is False
    
    def test_generate_thumbnail_nonexistent_file(self, temp_directory):
        """Test thumbnail generation with nonexistent PDF file"""
        nonexistent_path = os.path.join(temp_directory, 'nonexistent.pdf')
        output_path = os.path.join(temp_directory, 'test_thumbnail.jpg')
        
        result = ThumbnailService.generate_thumbnail(nonexistent_path, output_path)
        
        assert result is False
    
    @patch('app.services.thumbnail_service.pdf2image.convert_from_path')
    def test_generate_thumbnail_empty_pdf(self, mock_convert, temp_directory, sample_pdf_path):
        """Test thumbnail generation with PDF that has no pages"""
        mock_convert.return_value = []  # No pages
        
        output_path = os.path.join(temp_directory, 'test_thumbnail.jpg')
        
        result = ThumbnailService.generate_thumbnail(sample_pdf_path, output_path)
        
        assert result is False
    
    @patch('app.services.thumbnail_service.pdf2image.convert_from_path')
    def test_generate_thumbnail_image_save_error(self, mock_convert, temp_directory, sample_pdf_path):
        """Test thumbnail generation with image save error"""
        mock_image = MagicMock()
        mock_image.size = (210, 297)
        mock_convert.return_value = [mock_image]
        
        # Mock resize to work but save to fail
        mock_resized = MagicMock()
        mock_image.resize.return_value = mock_resized
        mock_resized.save.side_effect = Exception("Save failed")
        
        output_path = os.path.join(temp_directory, 'test_thumbnail.jpg')
        
        result = ThumbnailService.generate_thumbnail(sample_pdf_path, output_path)
        
        assert result is False
    
    def test_get_default_thumbnail_path(self, app):
        """Test getting default thumbnail path"""
        with app.app_context():
            with patch('app.services.thumbnail_service.current_app') as mock_app:
                mock_app.config = {'UPLOAD_FOLDER': '/uploads'}
                
                default_path = ThumbnailService.get_default_thumbnail()
                
                assert 'default_thumbnail.jpg' in default_path
    
    def test_cleanup_thumbnail_removes_file(self, app, temp_directory):
        """Test that cleanup removes thumbnail file"""
        with app.app_context():
            with patch('app.services.thumbnail_service.current_app') as mock_app:
                mock_app.config = {'UPLOAD_FOLDER': temp_directory}
                
                # Create a dummy thumbnail file
                thumbnail_dir = os.path.join(temp_directory, 'thumbnails')
                os.makedirs(thumbnail_dir, exist_ok=True)
                thumbnail_path = os.path.join(thumbnail_dir, '42.jpg')
                
                with open(thumbnail_path, 'w') as f:
                    f.write('dummy thumbnail')
                
                assert os.path.exists(thumbnail_path)
                
                result = ThumbnailService.cleanup_thumbnail(42)
                
                assert result is True
                assert not os.path.exists(thumbnail_path)
    
    def test_cleanup_thumbnail_nonexistent_file(self, app, temp_directory):
        """Test cleanup with nonexistent thumbnail file"""
        with app.app_context():
            with patch('app.services.thumbnail_service.current_app') as mock_app:
                mock_app.config = {'UPLOAD_FOLDER': temp_directory}
                
                result = ThumbnailService.cleanup_thumbnail(999)
                
                # Should not fail even if file doesn't exist
                assert result is True
    
    @patch('app.services.thumbnail_service.pdf2image.convert_from_path')
    def test_generate_thumbnail_creates_output_directory(self, mock_convert, temp_directory, sample_pdf_path):
        """Test that thumbnail generation creates output directory if needed"""
        mock_image = MagicMock()
        mock_image.size = (210, 297)
        mock_convert.return_value = [mock_image]
        
        mock_resized = MagicMock()
        mock_image.resize.return_value = mock_resized
        
        # Output path in non-existent directory
        output_dir = os.path.join(temp_directory, 'new_thumbnails')
        output_path = os.path.join(output_dir, 'test.jpg')
        
        assert not os.path.exists(output_dir)
        
        result = ThumbnailService.generate_thumbnail(sample_pdf_path, output_path)
        
        assert result is True
        assert os.path.exists(output_dir)
    
    def test_thread_safety_multiple_directory_creation(self, app, temp_directory):
        """Test thread safety when multiple processes create thumbnail directory"""
        import threading
        import time
        
        with app.app_context():
            with patch('app.services.thumbnail_service.current_app') as mock_app:
                mock_app.config = {'UPLOAD_FOLDER': temp_directory}
                
                results = []
                
                def create_directory():
                    try:
                        ThumbnailService.ensure_thumbnail_directory()
                        results.append(True)
                    except Exception as e:
                        results.append(False)
                
                # Create multiple threads trying to create directory simultaneously
                threads = []
                for i in range(5):
                    thread = threading.Thread(target=create_directory)
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads to complete
                for thread in threads:
                    thread.join()
                
                # All should succeed
                assert all(results)
                assert len(results) == 5
                
                # Directory should exist
                thumbnail_dir = os.path.join(temp_directory, 'thumbnails')
                assert os.path.exists(thumbnail_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])