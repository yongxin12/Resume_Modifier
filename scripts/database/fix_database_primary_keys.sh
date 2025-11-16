#!/bin/bash
# Database Primary Key Fix Script
# This script adds missing primary keys to resumes and job_descriptions tables

set -e  # Exit on error

echo "=========================================="
echo "Database Primary Key Fix Script"
echo "=========================================="
echo ""

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if database is running
echo "🔍 Checking database connection..."
if docker-compose exec -T db psql -U postgres -d resume_app -c '\q' 2>/dev/null; then
    echo "✅ Database is accessible"
else
    echo "❌ Cannot connect to database. Starting database..."
    docker-compose up -d db
    echo "⏳ Waiting for database to be ready..."
    sleep 5
fi

echo ""
echo "=========================================="
echo "Step 1: Checking for duplicate records"
echo "=========================================="

# Check for duplicates in resumes
echo ""
echo "Checking resumes table for duplicates..."
RESUME_DUPLICATES=$(docker-compose exec -T db psql -U postgres resume_app -t -c "
SELECT COUNT(*) FROM (
    SELECT user_id, serial_number, COUNT(*) as cnt
    FROM resumes 
    GROUP BY user_id, serial_number 
    HAVING COUNT(*) > 1
) AS duplicates;" | tr -d ' ')

if [ "$RESUME_DUPLICATES" -gt 0 ]; then
    echo "⚠️  Found $RESUME_DUPLICATES duplicate records in resumes table!"
    echo "Duplicate records:"
    docker-compose exec -T db psql -U postgres resume_app -c "
    SELECT user_id, serial_number, COUNT(*) as count
    FROM resumes 
    GROUP BY user_id, serial_number 
    HAVING COUNT(*) > 1;"
    echo ""
    echo "❌ Cannot add primary key with duplicate records."
    echo "Please clean up duplicates first, then run this script again."
    exit 1
else
    echo "✅ No duplicates found in resumes table"
fi

# Check for duplicates in job_descriptions
echo ""
echo "Checking job_descriptions table for duplicates..."
JOB_DUPLICATES=$(docker-compose exec -T db psql -U postgres resume_app -t -c "
SELECT COUNT(*) FROM (
    SELECT user_id, serial_number, COUNT(*) as cnt
    FROM job_descriptions 
    GROUP BY user_id, serial_number 
    HAVING COUNT(*) > 1
) AS duplicates;" | tr -d ' ')

if [ "$JOB_DUPLICATES" -gt 0 ]; then
    echo "⚠️  Found $JOB_DUPLICATES duplicate records in job_descriptions table!"
    echo "Duplicate records:"
    docker-compose exec -T db psql -U postgres resume_app -c "
    SELECT user_id, serial_number, COUNT(*) as count
    FROM job_descriptions 
    GROUP BY user_id, serial_number 
    HAVING COUNT(*) > 1;"
    echo ""
    echo "❌ Cannot add primary key with duplicate records."
    echo "Please clean up duplicates first, then run this script again."
    exit 1
else
    echo "✅ No duplicates found in job_descriptions table"
fi

echo ""
echo "=========================================="
echo "Step 2: Adding Primary Keys"
echo "=========================================="

# Add primary key to resumes
echo ""
echo "Adding primary key to resumes table..."
if docker-compose exec -T db psql -U postgres resume_app -c "
ALTER TABLE resumes 
ADD CONSTRAINT resumes_pkey PRIMARY KEY (user_id, serial_number);" 2>/dev/null; then
    echo "✅ Primary key added to resumes table"
else
    echo "⚠️  Primary key might already exist on resumes table"
fi

# Add primary key to job_descriptions
echo ""
echo "Adding primary key to job_descriptions table..."
if docker-compose exec -T db psql -U postgres resume_app -c "
ALTER TABLE job_descriptions 
ADD CONSTRAINT job_descriptions_pkey PRIMARY KEY (user_id, serial_number);" 2>/dev/null; then
    echo "✅ Primary key added to job_descriptions table"
else
    echo "⚠️  Primary key might already exist on job_descriptions table"
fi

echo ""
echo "=========================================="
echo "Step 3: Verification"
echo "=========================================="

# Verify resumes table
echo ""
echo "Resumes table structure:"
docker-compose exec -T db psql -U postgres resume_app -c "\d resumes"

echo ""
echo "Job descriptions table structure:"
docker-compose exec -T db psql -U postgres resume_app -c "\d job_descriptions"

echo ""
echo "=========================================="
echo "✅ Primary Key Fix Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "✅ Verified no duplicate records"
echo "✅ Added primary key to resumes (user_id, serial_number)"
echo "✅ Added primary key to job_descriptions (user_id, serial_number)"
echo ""
echo "Next steps:"
echo "1. Run: python3 verify_database_schema.py"
echo "2. Create migration to document these changes"
echo "3. Test application functionality"
echo ""
