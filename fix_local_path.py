"""
Fix for StorageResult local_path attribute error
This patch adds backward compatibility for any code expecting local_path
"""

# Add this to the StorageResult class in file_storage_service.py
# Property to provide backward compatibility if needed

def add_local_path_property():
    """Add local_path property to StorageResult for backward compatibility"""
    code_to_add = '''
    @property
    def local_path(self):
        """Backward compatibility property - returns file_path for local storage"""
        if self.storage_type == 'local':
            return self.file_path
        return None
    '''
    print("Code to add to StorageResult class:")
    print(code_to_add)

if __name__ == "__main__":
    add_local_path_property()