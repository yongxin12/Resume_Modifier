"""
Database Index Optimization for Enhanced File Management

This script creates optimal database indexes for the enhanced file management features
to improve query performance for duplicate detection, soft deletion, and file listing.
"""

from app.extensions import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


def create_performance_indexes():
    """
    Create database indexes to optimize file management queries
    
    This function creates indexes that are critical for performance of:
    - Duplicate file detection (hash-based queries)
    - Soft deletion filtering (deleted_at queries) 
    - User file listing (user_id + deleted_at combinations)
    - Google Drive integration queries
    """
    
    indexes_to_create = [
        # Compound index for duplicate detection queries (user_id + file_hash + deleted_at)
        {
            'name': 'idx_resumefile_duplicate_detection',
            'table': 'resume_file',
            'columns': ['user_id', 'file_hash', 'deleted_at'],
            'description': 'Optimizes duplicate file detection queries'
        },
        
        # Index for soft deletion queries (deleted_at + user_id)
        {
            'name': 'idx_resumefile_soft_deletion',
            'table': 'resume_file', 
            'columns': ['deleted_at', 'user_id'],
            'description': 'Optimizes soft deletion filtering and listing'
        },
        
        # Index for file hash lookups
        {
            'name': 'idx_resumefile_hash_lookup',
            'table': 'resume_file',
            'columns': ['file_hash'],
            'description': 'Optimizes file hash lookups for duplicate detection'
        },
        
        # Index for user file listings with upload date sorting
        {
            'name': 'idx_resumefile_user_listing',
            'table': 'resume_file',
            'columns': ['user_id', 'deleted_at', 'uploaded_at'],
            'description': 'Optimizes user file listing with date sorting'
        },
        
        # Index for Google Drive integration queries
        {
            'name': 'idx_resumefile_google_drive',
            'table': 'resume_file',
            'columns': ['google_drive_file_id', 'user_id'],
            'description': 'Optimizes Google Drive file lookups'
        },
        
        # Index for Google Doc conversion queries
        {
            'name': 'idx_resumefile_google_doc',
            'table': 'resume_file', 
            'columns': ['google_doc_id', 'user_id'],
            'description': 'Optimizes Google Doc access queries'
        },
        
        # Partial index for active files only (where deleted_at IS NULL)
        {
            'name': 'idx_resumefile_active_files',
            'table': 'resume_file',
            'columns': ['user_id', 'uploaded_at'],
            'condition': 'deleted_at IS NULL',
            'description': 'Optimizes queries for active (non-deleted) files only'
        },
        
        # Index for duplicate sequence queries
        {
            'name': 'idx_resumefile_duplicate_sequence',
            'table': 'resume_file',
            'columns': ['user_id', 'original_filename', 'duplicate_sequence'],
            'description': 'Optimizes duplicate sequence number generation'
        },
        
        # Index for admin deleted file queries
        {
            'name': 'idx_resumefile_admin_deleted',
            'table': 'resume_file',
            'columns': ['deleted_at', 'deleted_by'],
            'description': 'Optimizes admin queries for deleted files'
        },
        
        # Index for file restoration queries
        {
            'name': 'idx_resumefile_restoration',
            'table': 'resume_file',
            'columns': ['id', 'deleted_at', 'user_id'], 
            'description': 'Optimizes file restoration operations'
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for index_info in indexes_to_create:
        try:
            if _index_exists(index_info['name']):
                logger.info(f"Index {index_info['name']} already exists, skipping")
                skipped_count += 1
                continue
            
            _create_index(index_info)
            created_count += 1
            logger.info(f"Created index: {index_info['name']} - {index_info['description']}")
            
        except Exception as e:
            logger.error(f"Failed to create index {index_info['name']}: {e}")
    
    logger.info(f"Index creation completed: {created_count} created, {skipped_count} skipped")
    return created_count, skipped_count


def _index_exists(index_name: str) -> bool:
    """Check if an index already exists"""
    try:
        # PostgreSQL query to check index existence
        result = db.session.execute(text("""
            SELECT 1 FROM pg_indexes 
            WHERE indexname = :index_name
        """), {'index_name': index_name})
        
        return result.fetchone() is not None
        
    except Exception:
        # Fallback for other databases (SQLite, MySQL)
        try:
            # Try to get index info - if it fails, index doesn't exist
            db.session.execute(text(f"SELECT 1 FROM sqlite_master WHERE type='index' AND name='{index_name}'"))
            return True
        except Exception:
            return False


def _create_index(index_info: dict):
    """Create a database index"""
    columns_str = ', '.join(index_info['columns'])
    index_name = index_info['name']
    table_name = index_info['table']
    
    # Build the CREATE INDEX statement
    sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"
    
    # Add partial index condition if specified
    if 'condition' in index_info:
        sql += f" WHERE {index_info['condition']}"
    
    db.session.execute(text(sql))
    db.session.commit()


def drop_performance_indexes():
    """Drop all performance indexes (for cleanup/testing)"""
    
    indexes_to_drop = [
        'idx_resumefile_duplicate_detection',
        'idx_resumefile_soft_deletion', 
        'idx_resumefile_hash_lookup',
        'idx_resumefile_user_listing',
        'idx_resumefile_google_drive',
        'idx_resumefile_google_doc',
        'idx_resumefile_active_files',
        'idx_resumefile_duplicate_sequence',
        'idx_resumefile_admin_deleted',
        'idx_resumefile_restoration'
    ]
    
    dropped_count = 0
    
    for index_name in indexes_to_drop:
        try:
            if _index_exists(index_name):
                db.session.execute(text(f"DROP INDEX {index_name}"))
                db.session.commit()
                dropped_count += 1
                logger.info(f"Dropped index: {index_name}")
            else:
                logger.info(f"Index {index_name} does not exist, skipping")
                
        except Exception as e:
            logger.error(f"Failed to drop index {index_name}: {e}")
    
    logger.info(f"Index cleanup completed: {dropped_count} indexes dropped")
    return dropped_count


def analyze_query_performance():
    """
    Analyze query performance for common file management operations
    
    This function runs EXPLAIN ANALYZE on key queries to measure performance
    improvements from the indexes.
    """
    
    test_queries = [
        {
            'name': 'Duplicate Detection Query',
            'sql': """
                SELECT * FROM resume_file 
                WHERE user_id = 1 
                AND file_hash = 'test_hash_123' 
                AND deleted_at IS NULL
            """,
            'description': 'Query used for detecting duplicate files'
        },
        
        {
            'name': 'User File Listing Query',
            'sql': """
                SELECT * FROM resume_file 
                WHERE user_id = 1 
                AND deleted_at IS NULL 
                ORDER BY uploaded_at DESC 
                LIMIT 10
            """,
            'description': 'Query used for listing user files'
        },
        
        {
            'name': 'Deleted Files Admin Query',
            'sql': """
                SELECT * FROM resume_file 
                WHERE deleted_at IS NOT NULL 
                ORDER BY deleted_at DESC 
                LIMIT 50
            """,
            'description': 'Query used by admins to list deleted files'
        },
        
        {
            'name': 'Google Drive File Lookup',
            'sql': """
                SELECT * FROM resume_file 
                WHERE google_drive_file_id = 'test_drive_id_123'
                AND user_id = 1
            """,
            'description': 'Query used for Google Drive file lookups'
        }
    ]
    
    performance_results = []
    
    for query_info in test_queries:
        try:
            # Run EXPLAIN ANALYZE (PostgreSQL syntax)
            explain_sql = f"EXPLAIN ANALYZE {query_info['sql']}"
            result = db.session.execute(text(explain_sql))
            
            execution_plan = [row[0] for row in result.fetchall()]
            
            performance_results.append({
                'query_name': query_info['name'],
                'description': query_info['description'],
                'execution_plan': execution_plan,
                'analyzed': True
            })
            
        except Exception as e:
            # Fallback for databases that don't support EXPLAIN ANALYZE
            performance_results.append({
                'query_name': query_info['name'],
                'description': query_info['description'],
                'error': str(e),
                'analyzed': False
            })
    
    return performance_results


def optimize_database_settings():
    """
    Apply database-level optimizations for file management operations
    
    This function applies configuration changes that can improve performance
    for the file management workload.
    """
    
    optimizations = []
    
    try:
        # For PostgreSQL databases
        postgres_optimizations = [
            # Increase work_mem for hash operations (duplicate detection)
            "SET work_mem = '32MB'",
            
            # Increase shared_buffers for better caching
            "SET shared_buffers = '256MB'",
            
            # Optimize for file operations
            "SET random_page_cost = 1.1",
            
            # Enable parallel query execution
            "SET max_parallel_workers_per_gather = 2"
        ]
        
        for optimization in postgres_optimizations:
            try:
                db.session.execute(text(optimization))
                optimizations.append(f"Applied: {optimization}")
            except Exception as e:
                optimizations.append(f"Failed: {optimization} - {e}")
                
    except Exception as e:
        optimizations.append(f"Database optimization not available: {e}")
    
    return optimizations


def generate_performance_report():
    """Generate a comprehensive performance optimization report"""
    
    report = {
        'timestamp': db.func.now(),
        'database_type': db.engine.name,
        'indexes': [],
        'query_performance': [],
        'recommendations': []
    }
    
    # Check which indexes exist
    index_names = [
        'idx_resumefile_duplicate_detection',
        'idx_resumefile_soft_deletion',
        'idx_resumefile_hash_lookup',
        'idx_resumefile_user_listing',
        'idx_resumefile_google_drive'
    ]
    
    for index_name in index_names:
        report['indexes'].append({
            'name': index_name,
            'exists': _index_exists(index_name)
        })
    
    # Analyze query performance
    report['query_performance'] = analyze_query_performance()
    
    # Generate recommendations
    recommendations = []
    
    missing_indexes = [idx for idx in report['indexes'] if not idx['exists']]
    if missing_indexes:
        recommendations.append(f"Create missing indexes: {[idx['name'] for idx in missing_indexes]}")
    
    if db.engine.name == 'postgresql':
        recommendations.append("Consider using PostgreSQL-specific optimizations like partial indexes")
    
    recommendations.append("Monitor query performance regularly and adjust indexes as needed")
    recommendations.append("Consider database connection pooling for high-concurrency scenarios")
    
    report['recommendations'] = recommendations
    
    return report


if __name__ == '__main__':
    """
    Command-line interface for database optimization
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python database_optimization.py [create|drop|analyze|report]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'create':
        created, skipped = create_performance_indexes()
        print(f"Index creation completed: {created} created, {skipped} skipped")
        
    elif command == 'drop':
        dropped = drop_performance_indexes()
        print(f"Index cleanup completed: {dropped} indexes dropped")
        
    elif command == 'analyze':
        results = analyze_query_performance()
        print("Query Performance Analysis:")
        for result in results:
            print(f"\n{result['query_name']}: {result['description']}")
            if result['analyzed']:
                print("Execution plan:")
                for line in result['execution_plan']:
                    print(f"  {line}")
            else:
                print(f"Analysis failed: {result.get('error', 'Unknown error')}")
                
    elif command == 'report':
        report = generate_performance_report()
        print("Performance Optimization Report:")
        print(f"Database: {report['database_type']}")
        print(f"\nIndexes:")
        for idx in report['indexes']:
            status = "EXISTS" if idx['exists'] else "MISSING"
            print(f"  {idx['name']}: {status}")
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
            
    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, drop, analyze, report")
        sys.exit(1)