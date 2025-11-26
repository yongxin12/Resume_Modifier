#!/usr/bin/env python3
"""
Fix storage monitoring endpoints in server.py
Replaces _is_admin_user calls with proper admin check and adds logger initialization
"""

import re

def fix_server_file():
    """Fix the server.py file to properly handle admin checks and logging"""
    
    file_path = "/home/rex/project/resume-editor/project/Resume_Modifier/core/app/server.py"
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Replace _is_admin_user(request.user) with proper admin check
    admin_check_pattern = r'if not _is_admin_user\(request\.user\):'
    admin_replacement = '''# Get user from token and check admin status
        user = User.query.get(request.user.get('user_id'))
        if not user or not user.is_admin:'''
    
    content = re.sub(admin_check_pattern, admin_replacement, content)
    
    # Fix 2: Add logger initialization at the start of each storage monitoring function
    functions_to_fix = [
        'get_storage_monitoring_status',
        'start_storage_monitoring',
        'stop_storage_monitoring', 
        'force_storage_check',
        'get_storage_overview',
        'update_storage_monitoring_config'
    ]
    
    for func_name in functions_to_fix:
        # Find the function definition
        func_pattern = rf'(@api\.route\([^)]+\)\s*@token_required\s*def {func_name}\([^)]*\):[^"""]*"""[^"""]*""")\s*(\s*try:)'
        
        def add_logger(match):
            func_def = match.group(1)
            try_statement = match.group(2)
            
            return f'{func_def}\n    logger = logging.getLogger(__name__)\n    {try_statement}'
        
        content = re.sub(func_pattern, add_logger, content, flags=re.DOTALL)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed admin checks and logger initialization in storage monitoring endpoints")

if __name__ == "__main__":
    fix_server_file()