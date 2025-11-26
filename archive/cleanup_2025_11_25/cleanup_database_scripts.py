#!/usr/bin/env python3
"""
Database Scripts Cleanup Tool
Safely removes obsolete database scripts while preserving active tools and tests
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

class DatabaseScriptsCleanup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.cleanup_archive = self.project_root / "archive" / "cleanup_2024_11_25"
        self.dry_run = True  # Safety first
        
        # Files to definitely remove (obsolete)
        self.files_to_remove = [
            "add_missing_columns.py",
            "add_oauth_persistence_fields.py", 
            "analyze_database_scripts.py",
            "fix_all_timestamps.py",
            "fix_columns_safe.py",
            "fix_railway_database.py",
            "fix_railway_schema.py",
            "railway_migration.py",
            "railway_migration_simple.py",
            "railway_setup.py",
            "update_database.py"
        ]
        
        # Files to keep (active tools)
        self.files_to_keep = [
            "database_manager.py",  # Primary tool
            "scripts/railway_migrate.py",  # Railway deployment tool
            "test_database_integration.py",  # Testing tool
            "core/migrations/",  # Flask-Migrate system
            "archive/old_database_scripts/"  # Already archived
        ]
        
        # Test files (keep but organize)
        self.test_files = [
            "test_railway_deployment.py",
            "test_railway_status.py", 
            "test_railway_google_drive.py",
            "test_complete_railway.py"
        ]
    
    def create_archive_directory(self):
        """Create archive directory for cleanup"""
        try:
            self.cleanup_archive.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created archive directory: {self.cleanup_archive}")
            return True
        except Exception as e:
            print(f"❌ Failed to create archive directory: {e}")
            return False
    
    def archive_file(self, file_path: Path):
        """Move file to archive directory"""
        if not file_path.exists():
            print(f"⚪ File not found: {file_path}")
            return True
            
        try:
            if self.dry_run:
                print(f"🔍 [DRY RUN] Would archive: {file_path}")
                return True
            else:
                archive_path = self.cleanup_archive / file_path.name
                shutil.move(str(file_path), str(archive_path))
                print(f"📦 Archived: {file_path} → {archive_path}")
                return True
        except Exception as e:
            print(f"❌ Failed to archive {file_path}: {e}")
            return False
    
    def verify_active_tools(self):
        """Verify that active tools exist and are functional"""
        print("\n🔍 Verifying active database tools...")
        
        # Check database_manager.py
        db_manager = self.project_root / "database_manager.py"
        if db_manager.exists():
            print("✅ database_manager.py: Present")
        else:
            print("❌ database_manager.py: MISSING - CRITICAL!")
            return False
            
        # Check railway migrate script
        railway_migrate = self.project_root / "scripts" / "railway_migrate.py"
        if railway_migrate.exists():
            print("✅ scripts/railway_migrate.py: Present")
        else:
            print("❌ scripts/railway_migrate.py: MISSING - CRITICAL!")
            return False
            
        # Check Flask-Migrate migrations
        migrations_dir = self.project_root / "core" / "migrations"
        if migrations_dir.exists():
            print("✅ core/migrations/: Present")
        else:
            print("⚠️  core/migrations/: Missing (may need to be initialized)")
            
        return True
    
    def cleanup_obsolete_files(self):
        """Remove obsolete database files"""
        print(f"\n🧹 Cleaning up obsolete database scripts...")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'ACTUAL CLEANUP'}")
        
        success_count = 0
        total_count = len(self.files_to_remove)
        
        for filename in self.files_to_remove:
            file_path = self.project_root / filename
            if self.archive_file(file_path):
                success_count += 1
        
        print(f"\n📊 Cleanup Results: {success_count}/{total_count} files processed")
        return success_count == total_count
    
    def create_summary_report(self):
        """Create cleanup summary report"""
        report_content = f"""# Database Scripts Cleanup Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Cleanup Summary
- **Mode**: {'DRY RUN' if self.dry_run else 'ACTUAL CLEANUP'}
- **Files Processed**: {len(self.files_to_remove)}
- **Archive Location**: {self.cleanup_archive}

## Files Cleaned Up
"""
        
        for filename in self.files_to_remove:
            file_path = self.project_root / filename
            status = "Present" if file_path.exists() else "Not Found"
            report_content += f"- `{filename}` - {status}\n"
        
        report_content += f"""
## Active Tools Preserved
- `database_manager.py` - Primary database management tool
- `scripts/railway_migrate.py` - Railway deployment migration
- `core/migrations/` - Flask-Migrate system
- All test files preserved for validation

## Next Steps
1. Review cleanup results
2. Test active database tools
3. Update documentation
4. Run actual cleanup if dry run looks good

## Commands to Test Active Tools
```bash
# Test primary database manager
python3 database_manager.py info

# Test Railway connection (if logged in)
railway run python3 database_manager.py info
```
"""
        
        report_path = self.project_root / "CLEANUP_REPORT.md"
        
        try:
            if not self.dry_run:
                with open(report_path, 'w') as f:
                    f.write(report_content)
                print(f"📄 Created cleanup report: {report_path}")
            else:
                print(f"🔍 [DRY RUN] Would create report: {report_path}")
        except Exception as e:
            print(f"❌ Failed to create report: {e}")
    
    def run_cleanup(self, dry_run=True):
        """Execute the complete cleanup process"""
        self.dry_run = dry_run
        
        print("🧹 Database Scripts Cleanup Tool")
        print("=" * 50)
        print(f"Mode: {'DRY RUN (Safe Preview)' if dry_run else 'ACTUAL CLEANUP'}")
        print("")
        
        # Step 1: Verify active tools
        if not self.verify_active_tools():
            print("❌ Active tools verification failed. Aborting cleanup.")
            return False
        
        # Step 2: Create archive directory
        if not self.create_archive_directory():
            return False
        
        # Step 3: Clean up obsolete files
        if not self.cleanup_obsolete_files():
            print("❌ Cleanup failed. Some files could not be processed.")
            return False
        
        # Step 4: Create summary report
        self.create_summary_report()
        
        # Success message
        if dry_run:
            print("\n🎉 Dry run completed successfully!")
            print("🔧 To perform actual cleanup, run:")
            print("   python3 cleanup_database_scripts.py --execute")
        else:
            print("\n🎉 Database scripts cleanup completed!")
            print("📋 Review CLEANUP_REPORT.md for details")
        
        return True

def main():
    """Main function with command line interface"""
    cleanup_tool = DatabaseScriptsCleanup()
    
    # Check for execute flag
    execute_cleanup = "--execute" in sys.argv or "--real" in sys.argv
    
    if execute_cleanup:
        print("⚠️  ACTUAL CLEANUP MODE")
        print("This will permanently move obsolete files to archive.")
        response = input("Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
        
        success = cleanup_tool.run_cleanup(dry_run=False)
    else:
        print("🔍 DRY RUN MODE (Safe Preview)")
        print("No files will be moved. Add --execute to perform actual cleanup.")
        print("")
        success = cleanup_tool.run_cleanup(dry_run=True)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()