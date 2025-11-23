#!/usr/bin/env python3
"""
Simple test to see what attributes StorageResult has
"""

from dataclasses import dataclass
from typing import Optional

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

# Test the StorageResult object to see what attributes it has
result = StorageResult(
    success=True,
    storage_type='local',
    file_path='/test/path/file.pdf',
    file_size=1000
)

print("StorageResult attributes:")
for attr in dir(result):
    if not attr.startswith('_'):
        print(f"  {attr}: {getattr(result, attr)}")

print("\nTrying to access local_path (should fail):")
try:
    print(result.local_path)
except AttributeError as e:
    print(f"Error: {e}")

print("\nTrying to access file_path (should work):")
print(f"file_path: {result.file_path}")