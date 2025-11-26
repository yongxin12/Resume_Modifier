#!/usr/bin/env python3
"""
Fix file management integration test
"""

def fix_file_management_test():
    file_path = 'testing/unit/test_file_management_integration.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the except block at the end of the method
    except_block_start = content.find("            except Exception as e:")
    if except_block_start != -1:
        # Find the end of the method (next def or end of class)
        next_def = content.find("\n    def test_file_processing_workflow_docx", except_block_start)
        if next_def != -1:
            # Add proper indentation to close the new patch contexts
            before_except = content[:except_block_start]
            after_except = content[except_block_start:]
            
            # The except block should be at the same level as the new patches
            new_except_block = after_except.replace(
                "            except Exception as e:",
                "                    except Exception as e:"
            )
            new_except_block = new_except_block.replace(
                "                pytest.fail(f\"Integration test failed: {str(e)}\")",
                "                        pytest.fail(f\"Integration test failed: {str(e)}\")"
            )
            
            content = before_except + new_except_block
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed file management integration test indentation")

if __name__ == '__main__':
    fix_file_management_test()