#!/bin/bash

# 🔍 Database Deployment Validation Script
# Tests database connectivity and validates schema

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Database Deployment Validation${NC}"
echo "=================================="

# Function to test database connection
test_database_connection() {
    local db_url="$1"
    echo -e "${YELLOW}Testing database connection...${NC}"
    
    python3 -c "
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

try:
    engine = create_engine('$db_url')
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1')).scalar()
        print('✅ Database connection successful')
        print(f'   Test query result: {result}')
except SQLAlchemyError as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Unexpected error: {e}')
    sys.exit(1)
"
}

# Function to validate schema
validate_schema() {
    local db_url="$1"
    echo -e "${YELLOW}Validating database schema...${NC}"
    
    python3 -c "
import os
import sys
sys.path.append('.')

try:
    from app import create_app
    from app.extensions import db
    from sqlalchemy import inspect

    # Set database URL
    os.environ['DATABASE_URL'] = '$db_url'
    
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['users', 'resumes', 'job_descriptions', 'resume_analyses', 'generated_documents']
        
        print('📋 Database tables found:')
        for table in tables:
            print(f'   ✅ {table}')
        
        missing_tables = set(expected_tables) - set(tables)
        if missing_tables:
            print(f'⚠️  Missing tables: {missing_tables}')
        else:
            print('✅ All expected tables found')
            
        # Check key columns
        if 'users' in tables:
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            expected_user_cols = ['id', 'email', 'password_hash']
            missing_cols = set(expected_user_cols) - set(user_columns)
            if missing_cols:
                print(f'⚠️  Missing user columns: {missing_cols}')
            else:
                print('✅ User table schema valid')
                
        if 'resumes' in tables:
            resume_columns = [col['name'] for col in inspector.get_columns('resumes')]
            expected_resume_cols = ['id', 'user_id', 'title', 'extracted_text']
            missing_cols = set(expected_resume_cols) - set(resume_columns)
            if missing_cols:
                print(f'⚠️  Missing resume columns: {missing_cols}')
            else:
                print('✅ Resume table schema valid')

except Exception as e:
    print(f'❌ Schema validation failed: {e}')
    sys.exit(1)
"
}

# Function to test Flask app initialization
test_flask_app() {
    local db_url="$1"
    echo -e "${YELLOW}Testing Flask application...${NC}"
    
    python3 -c "
import os
import sys
sys.path.append('.')

try:
    # Set database URL
    os.environ['DATABASE_URL'] = '$db_url'
    
    from app import create_app
    from app.extensions import db
    
    app = create_app()
    print('✅ Flask app created successfully')
    
    with app.app_context():
        # Test database in Flask context
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1')).scalar()
        print('✅ Database accessible from Flask context')
        
        # Test model imports
        from app.models.user import User
        from app.models.resume import Resume
        print('✅ Models imported successfully')
        
        # Test basic operations
        user_count = User.query.count()
        resume_count = Resume.query.count()
        print(f'📊 Database stats: {user_count} users, {resume_count} resumes')

except Exception as e:
    print(f'❌ Flask app test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
}

# Function to test API endpoints
test_api_endpoints() {
    local app_url="$1"
    echo -e "${YELLOW}Testing API endpoints...${NC}"
    
    # Test health endpoint
    if command -v curl &> /dev/null; then
        echo "Testing health endpoint..."
        if curl -f -s "$app_url/health" > /dev/null; then
            echo "✅ Health endpoint accessible"
            curl -s "$app_url/health" | python3 -m json.tool
        else
            echo "❌ Health endpoint failed"
        fi
        
        # Test API docs
        echo "Testing API documentation..."
        if curl -f -s "$app_url/apidocs" > /dev/null; then
            echo "✅ API documentation accessible"
        else
            echo "⚠️  API documentation not accessible (may be expected)"
        fi
    else
        echo "⚠️  curl not available, skipping endpoint tests"
    fi
}

# Main validation function
main_validation() {
    local db_url=""
    local app_url=""
    
    # Get database URL
    if [ -f ".env" ]; then
        source .env
        db_url="$DATABASE_URL"
    fi
    
    if [ -z "$db_url" ]; then
        echo "Enter database URL to test:"
        read -p "DATABASE_URL: " db_url
    fi
    
    if [ -z "$db_url" ]; then
        echo -e "${RED}Error: Database URL is required${NC}"
        exit 1
    fi
    
    echo "Testing database: $db_url"
    echo ""
    
    # Run tests
    test_database_connection "$db_url"
    echo ""
    
    validate_schema "$db_url"
    echo ""
    
    test_flask_app "$db_url"
    echo ""
    
    # Optional: Test live application
    read -p "Do you want to test live application endpoints? (y/n): " test_live
    if [[ $test_live == "y" || $test_live == "Y" ]]; then
        read -p "Enter application URL: " app_url
        if [ ! -z "$app_url" ]; then
            test_api_endpoints "$app_url"
        fi
    fi
    
    echo -e "${GREEN}🎉 Validation completed!${NC}"
}

# Check if running with arguments
if [ $# -eq 0 ]; then
    main_validation
else
    case "$1" in
        "connection")
            test_database_connection "$2"
            ;;
        "schema")
            validate_schema "$2"
            ;;
        "flask")
            test_flask_app "$2"
            ;;
        "api")
            test_api_endpoints "$2"
            ;;
        *)
            echo "Usage: $0 [connection|schema|flask|api] [url]"
            echo "Or run without arguments for interactive mode"
            ;;
    esac
fi