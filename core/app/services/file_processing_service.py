"""
File Processing Service for extracting text and metadata from uploaded files
Supports PDF and DOCX file processing with comprehensive error handling

Author: Resume Modifier Backend Team
Date: October 2024
"""

import time
import re
import psutil
import os
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from io import BytesIO

# PDF processing
try:
    from PyPDF2 import PdfReader
except ImportError:
    try:
        from pypdf import PdfReader
    except ImportError:
        PdfReader = None

# DOCX processing
try:
    from docx import Document
except ImportError:
    Document = None

# Language detection
try:
    from langdetect import detect, DetectorFactory, LangDetectException
    # Set seed for consistent results
    DetectorFactory.seed = 0
except ImportError:
    detect = None


class ProcessingError(Exception):
    """Custom exception for file processing errors"""
    pass


@dataclass
class ProcessingResult:
    """Result object for file processing operations"""
    success: bool
    text: Optional[str] = None
    file_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    
    # Type-specific properties
    page_count: Optional[int] = None
    paragraph_count: Optional[int] = None
    keywords: List[str] = field(default_factory=list)
    language: Optional[str] = None


class FileProcessingService:
    """
    Service for processing uploaded files and extracting text content and metadata.
    Supports PDF and DOCX files with comprehensive error handling and validation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the file processing service with configuration.
        
        Args:
            config (Dict[str, Any], optional): Configuration dictionary containing:
                - max_text_length: Maximum allowed text length (default: 100000)
                - enable_metadata_extraction: Enable metadata extraction (default: True)
                - timeout_seconds: Processing timeout in seconds (default: 60)
                - enable_keyword_extraction: Enable keyword extraction (default: True)
                - enable_language_detection: Enable language detection (default: True)
        """
        self.config = config or {}
        
        # Configuration settings
        self.max_text_length = self.config.get('max_text_length', 100000)
        self.enable_metadata_extraction = self.config.get('enable_metadata_extraction', True)
        self.timeout_seconds = self.config.get('timeout_seconds', 60)
        self.enable_keyword_extraction = self.config.get('enable_keyword_extraction', True)
        self.enable_language_detection = self.config.get('enable_language_detection', True)
        
        # Check for required dependencies
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required dependencies are available"""
        if PdfReader is None:
            raise ProcessingError("PDF processing requires PyPDF2 or pypdf package")
        if Document is None:
            raise ProcessingError("DOCX processing requires python-docx package")

    def process_file(self, file_obj) -> ProcessingResult:
        """
        Process a file and extract text content and metadata.
        
        Args:
            file_obj: File object with filename and content_type attributes
        
        Returns:
            ProcessingResult: Processing result with text and metadata
        """
        start_time = time.time()
        initial_memory = self._get_memory_usage()
        
        try:
            # Determine file type
            file_type = self._determine_file_type(file_obj)
            
            if file_type == "pdf":
                extract_result = self.extract_text_from_pdf(file_obj)
            elif file_type == "docx":
                extract_result = self.extract_text_from_docx(file_obj)
            else:
                return ProcessingResult(
                    success=False,
                    error_message=f"Unsupported file type: {file_obj.content_type}"
                )
            
            # Check extraction success
            if not extract_result.success:
                return extract_result
            
            # Validate text length
            if len(extract_result.text) > self.max_text_length:
                return ProcessingResult(
                    success=False,
                    error_message=f"Text content too long: {len(extract_result.text)} characters (limit: {self.max_text_length})"
                )
            
            # Clean up text
            cleaned_text = self.cleanup_text(extract_result.text)
            
            # Generate metadata
            metadata = {}
            if self.enable_metadata_extraction:
                metadata = self.generate_metadata(
                    cleaned_text, 
                    file_type,
                    page_count=getattr(extract_result, 'page_count', None),
                    paragraph_count=getattr(extract_result, 'paragraph_count', None)
                )
            
            # Extract keywords
            keywords = []
            if self.enable_keyword_extraction and cleaned_text.strip():
                keywords = self.extract_keywords(cleaned_text)
            
            # Detect language
            language = None
            if self.enable_language_detection and cleaned_text.strip():
                language = self.detect_language(cleaned_text)
            
            # Calculate processing metrics
            processing_time = time.time() - start_time
            final_memory = self._get_memory_usage()
            memory_usage = final_memory - initial_memory
            
            # Add processing metrics to metadata
            metadata.update({
                'processing_time': processing_time,
                'memory_usage_mb': memory_usage,
                'text_length': len(cleaned_text)
            })
            
            return ProcessingResult(
                success=True,
                text=cleaned_text,
                file_type=file_type,
                metadata=metadata,
                processing_time=processing_time,
                page_count=getattr(extract_result, 'page_count', None),
                paragraph_count=getattr(extract_result, 'paragraph_count', None),
                keywords=keywords,
                language=language
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=f"File processing failed: {str(e)}",
                processing_time=time.time() - start_time
            )

    def extract_text_from_pdf(self, file_obj) -> ProcessingResult:
        """
        Extract text content from a PDF file.
        
        Args:
            file_obj: PDF file object
        
        Returns:
            ProcessingResult: Extraction result with text and page count
        """
        start_time = time.time()
        
        try:
            # Reset file pointer
            file_obj.seek(0)
            
            # Read PDF content
            pdf_reader = PdfReader(file_obj)
            text_parts = []
            page_count = len(pdf_reader.pages)
            
            # Extract text from each page
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_parts.append(page_text)
                except Exception as e:
                    # Log page-specific error but continue
                    print(f"Warning: Failed to extract text from page {page_num + 1}: {str(e)}")
                    continue
            
            # Combine all text
            full_text = '\n\n'.join(text_parts)
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                text=full_text,
                page_count=page_count,
                processing_time=processing_time
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=f"PDF text extraction failed: {str(e)}",
                processing_time=time.time() - start_time
            )

    def extract_text_from_docx(self, file_obj) -> ProcessingResult:
        """
        Extract text content from a DOCX file.
        
        Args:
            file_obj: DOCX file object
        
        Returns:
            ProcessingResult: Extraction result with text and paragraph count
        """
        start_time = time.time()
        
        try:
            # Reset file pointer
            file_obj.seek(0)
            
            # Read DOCX content
            doc = Document(file_obj)
            text_parts = []
            paragraph_count = 0
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:  # Only add non-empty paragraphs
                    text_parts.append(text)
                    paragraph_count += 1
            
            # Combine all text
            full_text = '\n\n'.join(text_parts)
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                text=full_text,
                paragraph_count=paragraph_count,
                processing_time=processing_time
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                error_message=f"DOCX text extraction failed: {str(e)}",
                processing_time=time.time() - start_time
            )

    def process_multiple_files(self, files: List) -> List[ProcessingResult]:
        """
        Process multiple files in batch.
        
        Args:
            files: List of file objects to process
        
        Returns:
            List[ProcessingResult]: List of processing results
        """
        results = []
        
        for file_obj in files:
            try:
                result = self.process_file(file_obj)
                results.append(result)
            except Exception as e:
                results.append(ProcessingResult(
                    success=False,
                    error_message=f"Batch processing failed for {getattr(file_obj, 'filename', 'unknown')}: {str(e)}"
                ))
        
        return results

    def generate_metadata(self, text: str, file_type: str, **kwargs) -> Dict[str, Any]:
        """
        Generate metadata for extracted text.
        
        Args:
            text: Extracted text content
            file_type: Type of the source file
            **kwargs: Additional metadata fields
        
        Returns:
            Dict[str, Any]: Metadata dictionary
        """
        metadata = {
            'file_type': file_type,
            'character_count': len(text),
            'word_count': len(text.split()) if text.strip() else 0,
            'has_content': bool(text.strip()),
        }
        
        # Add any additional metadata passed in kwargs
        metadata.update(kwargs)
        
        return metadata

    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """
        Extract keywords from text content.
        
        Args:
            text: Text content to analyze
            max_keywords: Maximum number of keywords to return
        
        Returns:
            List[str]: List of extracted keywords
        """
        if not text.strip():
            return []
        
        try:
            # Simple keyword extraction using regex
            # Remove common words and extract meaningful terms
            words = re.findall(r'\b[A-Za-z]+\b', text.lower())
            
            # Common stop words to filter out
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
                'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 
                'above', 'below', 'between', 'among', 'this', 'that', 'these', 'those', 'i', 'me', 
                'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 
                'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 
                'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 
                'who', 'whom', 'whose', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 
                'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 
                'doing', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'
            }
            
            # Filter out stop words and short words
            filtered_words = [word for word in words if len(word) > 2 and word not in stop_words]
            
            # Count word frequency
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and return top keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
            
        except Exception as e:
            print(f"Warning: Keyword extraction failed: {str(e)}")
            return []

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the text content.
        
        Args:
            text: Text content to analyze
        
        Returns:
            str: Language code (e.g., 'en', 'es', 'fr') or 'unknown'
        """
        if not text.strip():
            return "unknown"
        
        if detect is None:
            print("Warning: Language detection not available (langdetect package required)")
            return "unknown"
        
        try:
            # Use first 1000 characters for detection to improve accuracy and speed
            sample_text = text[:1000].strip()
            if len(sample_text) < 3:
                return "unknown"
            
            detected_lang = detect(sample_text)
            return detected_lang
            
        except (LangDetectException, Exception) as e:
            print(f"Warning: Language detection failed: {str(e)}")
            return "unknown"

    def cleanup_text(self, text: str) -> str:
        """
        Clean up and normalize text content.
        
        Args:
            text: Raw text content
        
        Returns:
            str: Cleaned text content
        """
        if not text:
            return ""
        
        # Replace multiple whitespace with single space
        cleaned = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Normalize line breaks
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        
        return cleaned

    def validate_file_content(self, content: bytes, content_type: str) -> bool:
        """
        Validate file content against its declared type.
        
        Args:
            content: File content bytes
            content_type: Declared content type
        
        Returns:
            bool: True if content matches type, False otherwise
        """
        if not content:
            return False
        
        try:
            if content_type == "application/pdf":
                # Check for PDF signature
                return content.startswith(b'%PDF-')
            
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                # Check for ZIP signature (DOCX is a ZIP file)
                return content.startswith(b'PK\x03\x04') or content.startswith(b'PK\x05\x06') or content.startswith(b'PK\x07\x08')
            
            else:
                return False
                
        except Exception:
            return False

    def _determine_file_type(self, file_obj) -> str:
        """
        Determine file type from file object.
        
        Args:
            file_obj: File object with content_type or filename
        
        Returns:
            str: File type ('pdf', 'docx', or 'unknown')
        """
        # Check content type first
        content_type = getattr(file_obj, 'content_type', '')
        if content_type == 'application/pdf':
            return 'pdf'
        elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return 'docx'
        
        # Check filename extension as fallback
        filename = getattr(file_obj, 'filename', '')
        if filename:
            if filename.lower().endswith('.pdf'):
                return 'pdf'
            elif filename.lower().endswith('.docx'):
                return 'docx'
        
        return 'unknown'

    def _get_memory_usage(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            float: Memory usage in megabytes
        """
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except Exception:
            return 0.0