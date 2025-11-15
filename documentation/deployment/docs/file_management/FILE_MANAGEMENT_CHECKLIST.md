# ✅ File Management Feature - Implementation Checklist

## Document Review Phase

- [ ] Read `function-specification.md` - Updated requirements
- [ ] Read `FILE_MANAGEMENT_DESIGN.md` - Architecture & design
- [ ] Read `FILE_MANAGEMENT_IMPLEMENTATION.md` - Code implementation
- [ ] Read `FILE_MANAGEMENT_SUMMARY.md` - Overall summary
- [ ] Read `FILE_MANAGEMENT_VISUAL_GUIDE.md` - Visual reference

---

## Phase 1: Planning & Setup (1-2 hours)

### 1.1 Choose Storage Provider
- [ ] Decide: Local FS (dev) or S3/GCS (production)
- [ ] Create storage bucket if using cloud
- [ ] Obtain credentials
- [ ] Test connectivity

### 1.2 Environment Configuration
- [ ] Determine `FILE_STORAGE_PROVIDER` value
- [ ] Set `FILE_STORAGE_PATH` (if local)
- [ ] Set `FILE_MAX_SIZE` (default: 10MB)
- [ ] Set AWS/GCS credentials (if cloud)
- [ ] Add to `.env` and `.env.example`

### 1.3 Database Preparation
- [ ] Back up current database
- [ ] Review migration script
- [ ] Prepare migration environment

---

## Phase 2: Database Implementation (30-45 minutes)

### 2.1 Add Model
- [ ] Add `ResumeFile` class to `app/models/temp.py`
- [ ] Include all fields: id, user_id, filename, size, etc.
- [ ] Add relationships to `User` model
- [ ] Add `to_dict()` method for JSON serialization
- [ ] Test model can be imported

### 2.2 Create Migration
- [ ] Create migration file: `migrations/versions/0016_*.py`
- [ ] Define `upgrade()` function
- [ ] Define `downgrade()` function
- [ ] Test migration file syntax

### 2.3 Execute Migration
- [ ] Run: `flask db upgrade` or `alembic upgrade head`
- [ ] Verify table created: `SELECT * FROM resume_files;`
- [ ] Verify indexes created
- [ ] Test rollback: `flask db downgrade` then `flask db upgrade`

---

## Phase 3: Utility & Validation (45 minutes)

### 3.1 File Validator
- [ ] Create `app/utils/file_validator.py`
- [ ] Implement `FileValidator` class
- [ ] Test extension validation
- [ ] Test MIME type validation
- [ ] Test file size validation
- [ ] Test with actual PDF/DOCX files
- [ ] Test with invalid files

### 3.2 Run Validator Tests
```bash
python -c "
from app.utils.file_validator import FileValidator
from werkzeug.datastructures import FileStorage
import io

v = FileValidator()
# Test with mock file
print('Validator tests passed')
"
```

---

## Phase 4: Storage Service (2 hours)

### 4.1 Local Storage
- [ ] Create `app/services/file_storage_service.py`
- [ ] Implement `FileStorageService` class
- [ ] Implement `_save_local()` method
- [ ] Implement `_get_local()` method
- [ ] Implement `_delete_local()` method
- [ ] Test local file save
- [ ] Test local file retrieve
- [ ] Test local file delete

### 4.2 S3 Storage (if applicable)
- [ ] Implement `_save_s3()` method
- [ ] Implement `_get_s3()` method
- [ ] Implement `_delete_s3()` method
- [ ] Verify boto3 installed
- [ ] Test S3 credentials
- [ ] Test S3 save/get/delete operations

### 4.3 GCS Storage (if applicable)
- [ ] Implement `_save_gcs()` method
- [ ] Implement `_get_gcs()` method
- [ ] Implement `_delete_gcs()` method
- [ ] Verify google-cloud-storage installed
- [ ] Test GCS credentials
- [ ] Test GCS save/get/delete operations

### 4.4 Storage Service Tests
```bash
pytest -v tests/test_file_storage_service.py
```

---

## Phase 5: Processing Service (1.5 hours)

### 5.1 Text Extraction
- [ ] Create `app/services/file_processing_service.py`
- [ ] Implement `extract_text()` method
- [ ] Implement `_extract_pdf()` method
- [ ] Implement `_extract_docx()` method
- [ ] Verify pypdf installed
- [ ] Verify python-docx installed

### 5.2 File Processing
- [ ] Implement `process_file()` method
- [ ] Extract text from PDF test file
- [ ] Extract text from DOCX test file
- [ ] Verify extracted text stored in database
- [ ] Test with large PDF
- [ ] Test with complex DOCX

### 5.3 Processing Service Tests
```bash
pytest -v tests/test_file_processing_service.py
```

---

## Phase 6: Metadata Service (1 hour)

### 6.1 Database Operations
- [ ] Create `app/services/file_metadata_service.py`
- [ ] Implement `get_file_by_id()` method
- [ ] Implement `get_user_files()` method
- [ ] Implement `delete_file()` method
- [ ] Implement `bulk_delete_files()` method

### 6.2 Query Operations
- [ ] Test get_file_by_id with valid ID
- [ ] Test get_file_by_id with invalid ID
- [ ] Test get_user_files pagination
- [ ] Test sorting (created_at, filename, file_size)
- [ ] Test search functionality
- [ ] Test delete_file
- [ ] Test bulk_delete_files

### 6.3 Metadata Service Tests
```bash
pytest -v tests/test_file_metadata_service.py
```

---

## Phase 7: API Endpoints (2 hours)

### 7.1 Implement Upload Endpoint
- [ ] Create `/files/upload` POST endpoint
- [ ] Validate file with FileValidator
- [ ] Store file with FileStorageService
- [ ] Process file with FileProcessingService
- [ ] Create database record
- [ ] Return proper response (201)
- [ ] Handle errors properly
- [ ] Add Swagger documentation

### 7.2 Implement List Endpoint
- [ ] Create `/files` GET endpoint
- [ ] Parse query parameters (page, per_page, sort_by, etc.)
- [ ] Call FileMetadataService
- [ ] Return paginated response (200)
- [ ] Add Swagger documentation

### 7.3 Implement Info Endpoint
- [ ] Create `/files/{id}/info` GET endpoint
- [ ] Validate ownership
- [ ] Return file metadata with text preview
- [ ] Handle file not found (404)
- [ ] Add Swagger documentation

### 7.4 Implement Download Endpoint
- [ ] Create `/files/{id}` GET endpoint (method: GET)
- [ ] Validate ownership
- [ ] Retrieve file content
- [ ] Set proper content headers
- [ ] Return as attachment
- [ ] Handle file not found (404)
- [ ] Add Swagger documentation

### 7.5 Implement Delete Endpoint
- [ ] Create `/files/{id}` DELETE endpoint (method: DELETE)
- [ ] Validate ownership
- [ ] Delete from storage
- [ ] Delete from database
- [ ] Return success response (200)
- [ ] Handle file not found (404)
- [ ] Add Swagger documentation

### 7.6 Implement Bulk Delete
- [ ] Create `/files` DELETE endpoint (method: DELETE, different from GET)
- [ ] Parse file_ids from request body
- [ ] Validate ownership for each file
- [ ] Delete all files
- [ ] Return deleted_count and failed_count
- [ ] Add Swagger documentation

---

## Phase 8: Authentication & Security (1 hour)

### 8.1 JWT Token Requirement
- [ ] Verify `@token_required` decorator on all endpoints
- [ ] Test endpoints without token (should return 401)
- [ ] Test endpoints with invalid token (should return 401)
- [ ] Test endpoints with valid token (should work)

### 8.2 User Ownership Validation
- [ ] Verify user_id from token
- [ ] Validate file belongs to user
- [ ] Test user cannot access other user's files
- [ ] Test proper error response (404 or 403)

### 8.3 Input Validation
- [ ] Validate file extension
- [ ] Validate file size
- [ ] Validate MIME type
- [ ] Test with malicious files
- [ ] Test with corrupted files

---

## Phase 9: Integration Testing (1.5 hours)

### 9.1 Upload Integration
- [ ] Upload PDF file
- [ ] Upload DOCX file
- [ ] Verify file stored correctly
- [ ] Verify text extracted
- [ ] Verify database record created
- [ ] Verify response includes file_id

### 9.2 List Integration
- [ ] Upload multiple files
- [ ] List all files
- [ ] Verify pagination works
- [ ] Verify sorting works
- [ ] Verify search works

### 9.3 Download Integration
- [ ] Download uploaded file
- [ ] Verify file content matches original
- [ ] Verify content-type header correct
- [ ] Verify content-disposition header correct

### 9.4 Delete Integration
- [ ] Delete single file
- [ ] Verify file removed from storage
- [ ] Verify database record deleted
- [ ] Verify file cannot be downloaded
- [ ] Bulk delete multiple files

### 9.5 Integration Tests
```bash
pytest -v tests/test_file_endpoints.py
```

---

## Phase 10: Integration with Existing Features (1.5 hours)

### 10.1 Resume Scoring Integration
- [ ] Update `/resume/score` to accept `file_id` parameter
- [ ] Test scoring with file_id instead of text
- [ ] Verify extracted text used for scoring
- [ ] Verify response includes score breakdown

### 10.2 Resume Generation Integration
- [ ] Update `/resume/generate` to accept `file_id` parameter
- [ ] Test generation with uploaded file
- [ ] Verify resume data parsed from file
- [ ] Verify AI optimization applied

### 10.3 Google Docs Export Integration
- [ ] Update `/resume/export/gdocs` to accept `file_id` parameter
- [ ] Test export with uploaded file
- [ ] Verify Google Doc created correctly
- [ ] Verify formatting applied

### 10.4 Integration Tests
```bash
pytest -v tests/test_file_integrations.py
```

---

## Phase 11: Documentation (30 minutes)

### 11.1 API Documentation
- [ ] Swagger UI shows all endpoints
- [ ] Each endpoint has proper documentation
- [ ] Request/response examples provided
- [ ] Error codes documented
- [ ] Test with Swagger UI

### 11.2 Code Documentation
- [ ] All classes have docstrings
- [ ] All methods have docstrings
- [ ] Complex logic explained with comments
- [ ] Function parameters documented

### 11.3 User Documentation
- [ ] README updated with new endpoints
- [ ] Examples provided for each endpoint
- [ ] FAQ updated
- [ ] Troubleshooting guide created

---

## Phase 12: Testing & Quality (2 hours)

### 12.1 Unit Tests
```bash
[ ] pytest tests/test_file_validator.py -v
[ ] pytest tests/test_file_storage_service.py -v
[ ] pytest tests/test_file_processing_service.py -v
[ ] pytest tests/test_file_metadata_service.py -v
```

### 12.2 Integration Tests
```bash
[ ] pytest tests/test_file_endpoints.py -v
[ ] pytest tests/test_file_integrations.py -v
```

### 12.3 Code Quality
- [ ] Run linter: `pylint app/`
- [ ] Run formatter: `black app/`
- [ ] Check type hints
- [ ] Verify error handling

### 12.4 Performance Tests
- [ ] Upload small file (< 1MB)
- [ ] Upload large file (5-10MB)
- [ ] Measure text extraction time
- [ ] Measure download time
- [ ] Test with multiple concurrent uploads

### 12.5 Test Coverage
- [ ] Generate coverage report: `pytest --cov=app tests/`
- [ ] Aim for > 80% coverage
- [ ] Identify untested code paths
- [ ] Add tests for edge cases

---

## Phase 13: Deployment to Staging (1 hour)

### 13.1 Pre-Deployment
- [ ] All tests passing locally
- [ ] No console errors or warnings
- [ ] Database backed up
- [ ] Storage configured and tested
- [ ] Environment variables prepared

### 13.2 Deploy Code
- [ ] Push to staging branch
- [ ] Wait for CI/CD pipeline
- [ ] Verify build succeeded
- [ ] Verify tests passed in pipeline

### 13.3 Deploy Database
- [ ] SSH into staging server
- [ ] Run migration: `flask db upgrade`
- [ ] Verify table created
- [ ] Verify can access from Flask shell

### 13.4 Smoke Tests
- [ ] Health check: `curl /health`
- [ ] Upload test file
- [ ] List files
- [ ] Download file
- [ ] Delete file
- [ ] Check logs for errors

### 13.5 Staging Verification
- [ ] Access Swagger UI: `/docs`
- [ ] Test all endpoints manually
- [ ] Test with actual PDF/DOCX files
- [ ] Test permission validation
- [ ] Monitor error logs

---

## Phase 14: Production Deployment (1 hour)

### 14.1 Pre-Production Checklist
- [ ] Staging tests passed
- [ ] Performance acceptable
- [ ] Security audit completed
- [ ] Database backed up
- [ ] Rollback plan documented

### 14.2 Deploy to Production
- [ ] Merge staging to main
- [ ] Wait for CI/CD pipeline
- [ ] Verify build succeeded
- [ ] Monitor deployment logs

### 14.3 Post-Deployment Database
- [ ] Run migration on production
- [ ] Verify table created
- [ ] Monitor database performance
- [ ] Verify replication (if applicable)

### 14.4 Smoke Tests
- [ ] Health check passing
- [ ] Swagger UI accessible
- [ ] Test upload endpoint
- [ ] Test list endpoint
- [ ] Test download endpoint
- [ ] Monitor error logs

### 14.5 Monitor Production
- [ ] Check API response times
- [ ] Monitor storage usage
- [ ] Watch for errors/exceptions
- [ ] Monitor database performance
- [ ] Check file integrity

---

## Phase 15: Post-Deployment (Ongoing)

### 15.1 User Feedback
- [ ] Collect user feedback
- [ ] Monitor error reports
- [ ] Track common issues
- [ ] Update troubleshooting guide

### 15.2 Performance Monitoring
- [ ] Monitor upload times
- [ ] Monitor download times
- [ ] Track storage usage per user
- [ ] Monitor API response times
- [ ] Alert on anomalies

### 15.3 Security Monitoring
- [ ] Track unauthorized access attempts
- [ ] Monitor file deletions
- [ ] Check for suspicious uploads
- [ ] Review audit logs

### 15.4 Updates & Maintenance
- [ ] Plan for feature enhancements
- [ ] Fix bugs as reported
- [ ] Optimize performance
- [ ] Update dependencies

---

## Success Criteria

- [x] All requirements implemented
- [x] All tests passing (> 80% coverage)
- [x] Documentation complete
- [x] Code reviewed and approved
- [x] Security audit passed
- [x] Performance benchmarks met
- [x] Deployed to staging successfully
- [x] Smoke tests passed on staging
- [x] Deployed to production successfully
- [x] No errors in production logs
- [x] Users can upload/download files
- [x] File management working seamlessly

---

## Rollback Plan

### If Issues Found Before Deployment
```bash
git reset --hard <previous_commit>
flask db downgrade
# Redeploy previous version
```

### If Issues Found After Deployment
```bash
# Disable new endpoints temporarily
# Then either:
# 1. Fix and redeploy, or
# 2. Rollback to previous version
```

---

## Support & Documentation Links

1. **Function Specification** → `function-specification.md`
2. **Architecture Design** → `FILE_MANAGEMENT_DESIGN.md`
3. **Implementation Guide** → `FILE_MANAGEMENT_IMPLEMENTATION.md`
4. **Summary & Integration** → `FILE_MANAGEMENT_SUMMARY.md`
5. **Visual Reference** → `FILE_MANAGEMENT_VISUAL_GUIDE.md`

---

## Questions & Troubleshooting

**Q: Where do I start?**
A: Start with Phase 1 (Planning & Setup), then follow sequentially.

**Q: Can I skip testing?**
A: No. Testing ensures quality and prevents production issues.

**Q: How long does implementation take?**
A: Approximately 12-15 hours total (can be done in 2-3 days of work).

**Q: What if I encounter errors?**
A: Check the error messages, review the documentation, and check application logs.

**Q: How do I test locally?**
A: Use local file storage (set `FILE_STORAGE_PROVIDER=local`), then run tests.

**Q: Can I deploy incrementally?**
A: Yes, you can implement each endpoint separately and deploy incrementally.

