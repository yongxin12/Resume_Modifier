#!/usr/bin/env python3
"""
Test the fixed StorageResult with local_path property
"""

import sys
import os

# Add the path to import the fixed StorageResult
sys.path.insert(0, '/home/rex/project/resume-editor/project/Resume_Modifier/core')

try:
    from app.services.file_storage_service import StorageResult
    
    # Test local storage
    result_local = StorageResult(
        success=True,
        storage_type='local',
        file_path='/test/path/file.pdf',
        file_size=1000
    )
    
    print("Testing LOCAL storage:")
    print(f"  file_path: {result_local.file_path}")
    print(f"  local_path: {result_local.local_path}")
    print(f"  local_path == file_path: {result_local.local_path == result_local.file_path}")
    
    # Test S3 storage
    result_s3 = StorageResult(
        success=True,
        storage_type='s3',
        s3_key='users/1/file.pdf',
        file_size=1000
    )
    
    print("\nTesting S3 storage:")
    print(f"  file_path: {result_s3.file_path}")
    print(f"  s3_key: {result_s3.s3_key}")
    print(f"  local_path: {result_s3.local_path}")
    
    print("\n✅ SUCCESS: local_path property works correctly!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()