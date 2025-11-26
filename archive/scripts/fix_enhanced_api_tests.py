#!/usr/bin/env python3
"""
Fix script for enhanced API endpoint tests
Fixes request context and SQLAlchemy session issues
"""

def fix_enhanced_api_tests():
    """Fix all the context and session issues in enhanced API tests"""
    
    file_path = 'testing/unit/test_enhanced_api_endpoints.py'
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # List of test methods that need app context wrapper for request patching
    request_context_tests = [
        'test_enhanced_upload_basic',
        'test_enhanced_upload_with_google_drive', 
        'test_google_drive_error_handling_in_upload',
        'test_duplicate_detection_error_handling_in_upload'
    ]
    
    # Fix each test that has request context issues
    for test_name in request_context_tests:
        # Find the test method signature
        method_pattern = f"def {test_name}(self, "
        method_start = content.find(method_pattern)
        if method_start == -1:
            continue
            
        # Find the end of the method signature
        method_sig_end = content.find('):', method_start) + 2
        method_sig = content[method_start:method_sig_end]
        
        # Add app parameter if not present
        if ', app,' not in method_sig and ', app' not in method_sig:
            new_sig = method_sig.replace('(self, ', '(self, app, ')
            content = content.replace(method_sig, new_sig)
        
        # Find the test body start (after the docstring)
        body_start = content.find('"""', method_sig_end)
        if body_start != -1:
            body_start = content.find('"""', body_start + 3) + 3
            # Skip whitespace to find actual code start
            while content[body_start] in ' \n\t':
                body_start += 1
        else:
            body_start = method_sig_end + 1
            while content[body_start] in ' \n\t':
                body_start += 1
        
        # Find the next method or end of class
        next_method = content.find('\n    def ', body_start)
        if next_method == -1:
            # This is the last method, find end of class
            next_method = len(content)
        
        # Get the method body
        method_body = content[body_start:next_method]
        
        # Check if it already has app.app_context()
        if 'with app.app_context():' in method_body:
            continue
            
        # Find the patch line for app.server.request
        patch_line_start = method_body.find("with patch('app.server.request')")
        if patch_line_start == -1:
            continue
            
        # Get the indentation of the patch line
        line_start = method_body.rfind('\n', 0, patch_line_start) + 1
        indent = ''
        for char in method_body[line_start:patch_line_start]:
            if char in ' \t':
                indent += char
            else:
                break
        
        # Insert app context wrapper
        app_context_line = f"{indent}with app.app_context():\n{indent}    "
        
        # Replace the patch line with app context + patch line
        old_patch_line = method_body[line_start:method_body.find('\n', patch_line_start)]
        new_patch_line = app_context_line + old_patch_line.strip()
        
        # Update the method body
        new_method_body = method_body.replace(old_patch_line, new_patch_line)
        
        # Now we need to indent everything after the patch line by 4 more spaces
        lines = new_method_body.split('\n')
        patch_line_index = -1
        for i, line in enumerate(lines):
            if "with app.app_context():" in line:
                patch_line_index = i
                break
        
        if patch_line_index != -1:
            # Indent all subsequent lines until we reach the same level as the app_context
            base_indent_level = len(lines[patch_line_index]) - len(lines[patch_line_index].lstrip())
            
            for i in range(patch_line_index + 1, len(lines)):
                line = lines[i]
                if not line.strip():  # Empty line
                    continue
                
                current_indent = len(line) - len(line.lstrip())
                
                # If we've returned to the base level or less, stop indenting  
                if current_indent <= base_indent_level and line.strip():
                    break
                    
                # Add 4 spaces of indentation
                lines[i] = '    ' + line
            
            new_method_body = '\n'.join(lines)
        
        # Replace in the original content
        content = content[:body_start] + new_method_body + content[next_method:]
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed enhanced API tests context and session issues")

if __name__ == '__main__':
    fix_enhanced_api_tests()