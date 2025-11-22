"""
Thumbnail Service for PDF file thumbnail generation
Handles creation, storage, and management of PDF document thumbnails
"""

import os
import logging
from datetime import datetime
from typing import Optional, Tuple
from flask import current_app
from PIL import Image
import pdf2image
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError


class ThumbnailService:
    """Service for generating and managing PDF thumbnails"""
    
    # Configuration constants
    THUMBNAIL_SIZE = (150, 200)  # width x height in pixels
    THUMBNAIL_QUALITY = 85  # JPEG quality (0-100)
    THUMBNAIL_FORMAT = 'JPEG'
    THUMBNAIL_DPI = 150  # DPI for PDF conversion
    
    @staticmethod
    def generate_thumbnail(file_path: str, output_path: str) -> bool:
        """
        Generate thumbnail from PDF first page
        
        Args:
            file_path (str): Path to source PDF file
            output_path (str): Path where thumbnail should be saved
            
        Returns:
            bool: True if thumbnail generated successfully, False otherwise
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Validate input file exists
            if not os.path.exists(file_path):
                logger.error(f"Source PDF file not found: {file_path}")
                return False
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Created output directory: {output_dir}")
            
            # Convert first page of PDF to image
            logger.info(f"Converting PDF to image: {file_path}")
            images = pdf2image.convert_from_path(
                file_path,
                first_page=1,
                last_page=1,
                dpi=ThumbnailService.THUMBNAIL_DPI,
                fmt=ThumbnailService.THUMBNAIL_FORMAT
            )
            
            if not images:
                logger.error(f"No pages found in PDF: {file_path}")
                return False
            
            # Get first page
            first_page = images[0]
            logger.info(f"Original image size: {first_page.size}")
            
            # Resize to thumbnail size
            thumbnail = first_page.resize(
                ThumbnailService.THUMBNAIL_SIZE,
                Image.Resampling.LANCZOS
            )
            
            # Save thumbnail with optimization
            thumbnail.save(
                output_path,
                ThumbnailService.THUMBNAIL_FORMAT,
                quality=ThumbnailService.THUMBNAIL_QUALITY,
                optimize=True
            )
            
            logger.info(f"Thumbnail generated successfully: {output_path}")
            return True
            
        except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as e:
            logger.error(f"PDF processing error for {file_path}: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error generating thumbnail for {file_path}: {str(e)}")
            return False
    
    @staticmethod
    def get_thumbnail_path(file_id: int) -> str:
        """
        Get expected thumbnail file path for given file ID
        
        Args:
            file_id (int): File ID from database
            
        Returns:
            str: Full path to thumbnail file
        """
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        thumbnail_dir = os.path.join(upload_folder, 'thumbnails')
        return os.path.join(thumbnail_dir, f'{file_id}.jpg')
    
    @staticmethod
    def ensure_thumbnail_directory() -> None:
        """
        Ensure thumbnail directory exists with proper permissions
        Thread-safe directory creation
        """
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        thumbnail_dir = os.path.join(upload_folder, 'thumbnails')
        
        try:
            os.makedirs(thumbnail_dir, exist_ok=True)
            # Set appropriate permissions (readable by web server)
            os.chmod(thumbnail_dir, 0o755)
        except OSError as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create thumbnail directory {thumbnail_dir}: {str(e)}")
            raise
    
    @staticmethod
    def get_default_thumbnail() -> str:
        """
        Get path to default placeholder thumbnail
        
        Returns:
            str: Path to default thumbnail image
        """
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        static_folder = current_app.config.get('STATIC_FOLDER', 'static')
        
        # Try to find default thumbnail in static folder first
        default_static = os.path.join(static_folder, 'images', 'default_thumbnail.jpg')
        if os.path.exists(default_static):
            return default_static
        
        # Fallback to uploads folder
        default_uploads = os.path.join(upload_folder, 'default_thumbnail.jpg')
        return default_uploads
    
    @staticmethod
    def cleanup_thumbnail(file_id: int) -> bool:
        """
        Remove thumbnail file for given file ID
        
        Args:
            file_id (int): File ID to cleanup thumbnail for
            
        Returns:
            bool: True if cleanup successful or file didn't exist
        """
        logger = logging.getLogger(__name__)
        
        try:
            thumbnail_path = ThumbnailService.get_thumbnail_path(file_id)
            
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                logger.info(f"Removed thumbnail: {thumbnail_path}")
            else:
                logger.info(f"Thumbnail file not found (already removed?): {thumbnail_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up thumbnail for file {file_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_thumbnail_info(file_id: int) -> dict:
        """
        Get information about thumbnail file
        
        Args:
            file_id (int): File ID to get thumbnail info for
            
        Returns:
            dict: Thumbnail information including existence, size, etc.
        """
        thumbnail_path = ThumbnailService.get_thumbnail_path(file_id)
        
        if not os.path.exists(thumbnail_path):
            return {
                'exists': False,
                'path': thumbnail_path,
                'size': None,
                'modified': None
            }
        
        try:
            stat = os.stat(thumbnail_path)
            return {
                'exists': True,
                'path': thumbnail_path,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception:
            return {
                'exists': False,
                'path': thumbnail_path,
                'size': None,
                'modified': None
            }
    
    @staticmethod
    def validate_pdf_for_thumbnail(file_path: str) -> bool:
        """
        Validate that PDF file can be processed for thumbnail generation
        
        Args:
            file_path (str): Path to PDF file
            
        Returns:
            bool: True if PDF can be processed
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Check file exists and is readable
            if not os.path.exists(file_path):
                return False
            
            if not os.access(file_path, os.R_OK):
                return False
            
            # Try to get page count without actually converting
            # This is a lightweight check for PDF validity
            pages = pdf2image.convert_from_path(
                file_path,
                first_page=1,
                last_page=1,
                dpi=50,  # Low DPI for quick check
                fmt='JPEG'
            )
            
            return len(pages) > 0
            
        except Exception as e:
            logger.debug(f"PDF validation failed for {file_path}: {str(e)}")
            return False


# Create default thumbnail if it doesn't exist
def create_default_thumbnail():
    """Create a default placeholder thumbnail image"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple placeholder image
        img = Image.new('RGB', ThumbnailService.THUMBNAIL_SIZE, color='#f0f0f0')
        draw = ImageDraw.Draw(img)
        
        # Draw simple placeholder content
        width, height = ThumbnailService.THUMBNAIL_SIZE
        
        # Draw border
        draw.rectangle([2, 2, width-3, height-3], outline='#cccccc', width=2)
        
        # Draw document icon (simple representation)
        doc_width = width // 3
        doc_height = height // 2
        doc_x = (width - doc_width) // 2
        doc_y = (height - doc_height) // 2
        
        draw.rectangle([doc_x, doc_y, doc_x + doc_width, doc_y + doc_height], 
                      fill='white', outline='#999999', width=1)
        
        # Add text if possible
        try:
            # Try to load default font
            font = ImageFont.load_default()
            text = "PDF"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (width - text_width) // 2
            text_y = doc_y + doc_height + 10
            
            draw.text((text_x, text_y), text, fill='#666666', font=font)
        except:
            pass  # Font loading failed, skip text
        
        # Save default thumbnail
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        default_path = os.path.join(upload_folder, 'default_thumbnail.jpg')
        
        os.makedirs(os.path.dirname(default_path), exist_ok=True)
        img.save(default_path, 'JPEG', quality=85)
        
        return default_path
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create default thumbnail: {str(e)}")
        return None