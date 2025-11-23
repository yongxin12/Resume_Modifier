#!/usr/bin/env python3
"""
Test script to debug the StorageResult local_path error
"""

import sys
import os
sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier')

from core.app.services.file_storage_service import StorageResult

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