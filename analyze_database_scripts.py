#!/usr/bin/env python3
"""
Database Script Cleanup and Organization Tool
Identifies outdated scripts and organizes database management tools
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Set

class ScriptAnalyzer:
    """Analyzes database scripts for duplicates and outdated versions"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.scripts = {}
        self.recommendations = []
    
    def scan_scripts(self) -> Dict[str, List[str]]:
        """Scan for all database-related scripts"""
        patterns = [
            '*migrate*.py',
            '*database*.py', 
            '*fix*.py',
            '*columns*.py',
            'railway*.py'
        ]
        
        found_scripts = {}
        
        for pattern in patterns:
            for script_path in self.project_root.rglob(pattern):
                if '__pycache__' in str(script_path):
                    continue
                    
                category = self._categorize_script(script_path)
                if category not in found_scripts:
                    found_scripts[category] = []
                found_scripts[category].append(str(script_path))
        
        return found_scripts
    
    def _categorize_script(self, script_path: Path) -> str:
        """Categorize script by functionality"""
        name = script_path.name.lower()
        
        if 'migrate' in name:
            return 'migration'
        elif 'fix' in name or 'repair' in name:
            return 'fixes'
        elif 'database' in name:
            return 'database'
        elif 'railway' in name:
            return 'railway'
        elif 'column' in name:
            return 'schema'
        else:
            return 'other'
    
    def analyze_duplicates(self, scripts: Dict[str, List[str]]) -> Dict[str, Set[str]]:
        """Find duplicate or similar scripts by content hash"""
        duplicates = {}
        file_hashes = {}
        
        for category, script_list in scripts.items():
            for script_path in script_list:
                try:
                    with open(script_path, 'r') as f:
                        content = f.read()
                    
                    # Create content hash
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    if content_hash in file_hashes:
                        # Found duplicate
                        if content_hash not in duplicates:
                            duplicates[content_hash] = set()
                        duplicates[content_hash].add(script_path)
                        duplicates[content_hash].add(file_hashes[content_hash])
                    else:
                        file_hashes[content_hash] = script_path
                        
                except Exception as e:
                    print(f"⚠️  Could not read {script_path}: {e}")
        
        return duplicates
    
    def analyze_script_purpose(self, script_path: str) -> Dict[str, any]:
        """Analyze what a script does"""
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            analysis = {
                'path': script_path,
                'size': len(content),
                'functions': [],
                'imports': [],
                'purpose': 'unknown',
                'railway_compatible': False,
                'standalone': False
            }
            
            lines = content.split('\n')
            
            # Analyze imports
            for line in lines:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    analysis['imports'].append(line.strip())
            
            # Check for Railway compatibility
            if 'DATABASE_PUBLIC_URL' in content or 'railway' in content.lower():
                analysis['railway_compatible'] = True
            
            # Check if standalone
            if 'if __name__ == "__main__"' in content:
                analysis['standalone'] = True
            
            # Determine purpose
            if 'create table' in content.lower():
                analysis['purpose'] = 'table_creation'
            elif 'alter table' in content.lower():
                analysis['purpose'] = 'schema_modification'
            elif 'migration' in content.lower():
                analysis['purpose'] = 'migration'
            elif 'fix' in content.lower():
                analysis['purpose'] = 'repair'
            
            return analysis
            
        except Exception as e:
            return {'path': script_path, 'error': str(e)}
    
    def generate_recommendations(self, scripts: Dict[str, List[str]], 
                               duplicates: Dict[str, Set[str]]) -> List[str]:
        """Generate cleanup recommendations"""
        recommendations = []
        
        # Check for duplicates
        if duplicates:
            recommendations.append("🔄 DUPLICATE SCRIPTS FOUND:")
            for hash_val, script_set in duplicates.items():
                recommendations.append(f"   Identical content:")
                for script in script_set:
                    recommendations.append(f"     - {script}")
                recommendations.append("   → Recommendation: Keep the most recent/appropriately named version")
                recommendations.append("")
        
        # Analyze each category
        for category, script_list in scripts.items():
            if len(script_list) > 1:
                recommendations.append(f"📁 MULTIPLE {category.upper()} SCRIPTS:")
                for script in script_list:
                    analysis = self.analyze_script_purpose(script)
                    recommendations.append(f"   - {script}")
                    recommendations.append(f"     Purpose: {analysis.get('purpose', 'unknown')}")
                    recommendations.append(f"     Railway compatible: {analysis.get('railway_compatible', False)}")
                    recommendations.append(f"     Standalone executable: {analysis.get('standalone', False)}")
                recommendations.append("")
        
        # Current recommendation for the unified approach
        recommendations.extend([
            "✅ RECOMMENDED APPROACH:",
            "",
            "1. USE: database_manager.py (newly created unified script)",
            "   - Handles all database operations",
            "   - Railway compatible",
            "   - Command line interface",
            "   - Safe column additions",
            "",
            "2. KEEP: scripts/railway_migrate.py",
            "   - Used by Railway deployment (railway.toml)",
            "   - Essential for production deployments",
            "",
            "3. ARCHIVE OR REMOVE:",
            "   - fix_railway_database.py (replaced by database_manager.py)",
            "   - add_missing_columns.py (replaced by database_manager.py)",
            "   - fix_columns_safe.py (replaced by database_manager.py)",
            "",
            "4. MIGRATION USAGE:",
            "   - Use Flask-Migrate/Alembic for formal schema changes",
            "   - Use database_manager.py for quick fixes and updates",
            ""
        ])
        
        return recommendations

def main():
    """Main analysis function"""
    print("🔍 Database Script Analysis and Cleanup")
    print("=" * 60)
    
    project_root = os.getcwd()
    analyzer = ScriptAnalyzer(project_root)
    
    # Scan for scripts
    print("\n📂 Scanning for database scripts...")
    scripts = analyzer.scan_scripts()
    
    if not scripts:
        print("❌ No database scripts found!")
        return
    
    # Display found scripts
    print(f"✅ Found {sum(len(scripts[cat]) for cat in scripts)} scripts in {len(scripts)} categories")
    
    for category, script_list in scripts.items():
        print(f"\n📋 {category.upper()} ({len(script_list)} scripts):")
        for script in script_list:
            rel_path = os.path.relpath(script, project_root)
            print(f"   - {rel_path}")
    
    # Analyze duplicates
    print("\n🔍 Analyzing for duplicates...")
    duplicates = analyzer.analyze_duplicates(scripts)
    
    if duplicates:
        print(f"⚠️  Found {len(duplicates)} sets of duplicate scripts")
    else:
        print("✅ No exact duplicate scripts found")
    
    # Generate recommendations
    print("\n📝 Generating recommendations...")
    recommendations = analyzer.generate_recommendations(scripts, duplicates)
    
    print("\n" + "=" * 60)
    print("CLEANUP RECOMMENDATIONS")
    print("=" * 60)
    
    for rec in recommendations:
        print(rec)
    
    # Create cleanup script
    cleanup_script_path = os.path.join(project_root, 'cleanup_database_scripts.sh')
    
    cleanup_content = """#!/bin/bash
# Database Script Cleanup
# Generated by script analyzer

echo "🧹 Cleaning up database scripts..."

# Create archive directory
mkdir -p archive/old_database_scripts

# Move outdated scripts to archive
echo "📦 Archiving outdated scripts..."
mv fix_railway_database.py archive/old_database_scripts/ 2>/dev/null || echo "fix_railway_database.py not found"
mv add_missing_columns.py archive/old_database_scripts/ 2>/dev/null || echo "add_missing_columns.py not found"
mv fix_columns_safe.py archive/old_database_scripts/ 2>/dev/null || echo "fix_columns_safe.py not found"

# Create README for active scripts
cat > DATABASE_SCRIPTS_README.md << 'EOF'
# Database Management Scripts

## Active Scripts

### 🚀 Primary Tool: `database_manager.py`
**Purpose:** Unified database management for all environments
**Usage:**
```bash
# Show database info
python3 database_manager.py info

# Validate schema
python3 database_manager.py validate

# Update missing columns
python3 database_manager.py columns

# Full database update
python3 database_manager.py update

# Dry run (show what would be done)
python3 database_manager.py update --dry-run
```

### 🏗️ Deployment Script: `scripts/railway_migrate.py`
**Purpose:** Database initialization for Railway deployments
**Usage:** Automatically called by Railway (configured in railway.toml)

## Archived Scripts
- `archive/old_database_scripts/` - Contains previous database fix scripts
- These are kept for reference but should not be used

## Migration Management
- Use Flask-Migrate for formal schema changes: `flask db migrate`
- Use database_manager.py for quick fixes and updates
- Always test changes in development first

## Railway Deployment
1. Changes to database_manager.py are automatically deployed
2. Railway calls scripts/railway_migrate.py on startup
3. Use `railway run python3 database_manager.py info` to check production database
EOF

echo "✅ Cleanup completed!"
echo "📖 Created DATABASE_SCRIPTS_README.md with usage instructions"
echo "📦 Archived old scripts in archive/old_database_scripts/"
"""
    
    with open(cleanup_script_path, 'w') as f:
        f.write(cleanup_content)
    
    os.chmod(cleanup_script_path, 0o755)
    
    print(f"\n📜 Created cleanup script: {cleanup_script_path}")
    print("🏃 Run './cleanup_database_scripts.sh' to perform cleanup")

if __name__ == "__main__":
    main()