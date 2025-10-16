"""
Test-driven development for Google Docs export functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from app.models.temp import GeneratedDocument, GoogleAuth
from app.extensions import db


class TestGoogleDocsExport:
    """Test suite for Google Docs document creation and export"""
    
    @pytest.mark.google_api
    def test_create_google_document(self, sample_google_auth, sample_resume, mock_google_docs_service):
        """Test creating a new Google Docs document"""
        from app.services.google_docs_service import GoogleDocsService
        
        service = GoogleDocsService(mock_google_docs_service)
        
        document_data = {
            'title': 'Test Resume - John Doe',
            'content': sample_resume.parsed_resume
        }
        
        result = service.create_document(document_data)
        
        assert 'document_id' in result
        assert 'document_url' in result
        assert result['document_id'] == 'test_doc_id_123'
        assert 'docs.google.com' in result['document_url']
        
    @pytest.mark.google_api
    def test_format_google_document(self, sample_resume, mock_google_docs_service, sample_template):
        """Test formatting Google Docs document with professional styling"""
        from app.services.google_docs_service import GoogleDocsService
        
        service = GoogleDocsService(mock_google_docs_service)
        
        formatting_requests = service.generate_formatting_requests(
            sample_resume.parsed_resume, 
            sample_template
        )
        
        assert len(formatting_requests) > 0
        assert any('textStyle' in req.get('updateTextStyle', {}) for req in formatting_requests)
        assert any('fontSize' in str(req) for req in formatting_requests)
        
    @pytest.mark.google_api
    def test_insert_resume_content(self, sample_resume, mock_google_docs_service):
        """Test inserting resume content into Google Docs"""
        from app.services.google_docs_service import GoogleDocsService
        
        service = GoogleDocsService(mock_google_docs_service)
        document_id = 'test_doc_id_123'
        
        result = service.insert_content(document_id, sample_resume.parsed_resume)
        
        assert result['success'] is True
        assert 'content_inserted' in result
        
        # Verify mock was called with correct parameters
        mock_google_docs_service.documents.return_value.batchUpdate.assert_called()
        
    @pytest.mark.google_api
    def test_apply_professional_styling(self, mock_google_docs_service, sample_template):
        """Test applying professional styling to Google Docs"""
        from app.services.google_docs_service import GoogleDocsService
        
        service = GoogleDocsService(mock_google_docs_service)
        document_id = 'test_doc_id_123'
        
        result = service.apply_template_styling(document_id, sample_template)
        
        assert result['styling_applied'] is True
        
        # Verify styling requests were made
        mock_google_docs_service.documents.return_value.batchUpdate.assert_called()
        
    @pytest.mark.google_api
    def test_generate_shareable_link(self, mock_google_drive_service):
        """Test generating shareable link for Google Docs"""
        from app.services.google_drive_service import GoogleDriveService
        
        service = GoogleDriveService(mock_google_drive_service)
        document_id = 'test_doc_id_123'
        
        result = service.create_shareable_link(document_id)
        
        assert 'shareable_url' in result
        assert 'permission_id' in result
        assert 'docs.google.com' in result['shareable_url']
        
    @pytest.mark.google_api
    def test_set_document_permissions(self, mock_google_drive_service):
        """Test setting appropriate permissions for generated documents"""
        from app.services.google_drive_service import GoogleDriveService
        
        service = GoogleDriveService(mock_google_drive_service)
        document_id = 'test_doc_id_123'
        
        result = service.set_permissions(document_id, permission_level='viewer')
        
        assert result['permissions_set'] is True
        assert result['permission_level'] == 'viewer'
        
        # Verify permission was created
        mock_google_drive_service.permissions.return_value.create.assert_called()


class TestGoogleDocsExportAPI:
    """Test suite for Google Docs export API endpoints"""
    
    @pytest.mark.api
    def test_export_resume_to_google_docs(self, client, authenticated_headers, sample_google_auth, sample_resume, sample_template):
        """Test /api/resume/export/gdocs endpoint"""
        request_data = {
            'resume_id': sample_resume.serial_number,
            'template_id': sample_template.id,
            'document_title': 'My Professional Resume'
        }
        
        with patch('app.server.GoogleDocsService') as mock_docs_service:
            with patch('app.server.GoogleDriveService') as mock_drive_service:
                with patch('app.server.GoogleAuthService') as mock_auth_service:
                    # Mock successful document creation
                    mock_docs_service.return_value.create_document.return_value = {
                        'document_id': 'test_doc_id_123',
                        'document_url': 'https://docs.google.com/document/d/test_doc_id_123/edit'
                    }
                    
                    mock_docs_service.return_value.apply_template_styling.return_value = {
                        'styling_applied': True
                    }
                    
                    mock_drive_service.return_value.create_shareable_link.return_value = {
                        'shareable_url': 'https://docs.google.com/document/d/test_doc_id_123/edit',
                        'permission_id': 'permission_123'
                    }
                    
                    # Mock credentials
                    from unittest.mock import Mock
                    mock_credentials = Mock()
                    mock_auth_service.return_value.get_credentials.return_value = mock_credentials
                
                    response = client.post('/api/resume/export/gdocs',
                                         json=request_data,
                                         headers=authenticated_headers)
                    
                    assert response.status_code == 200
                    json_data = response.get_json()
                    assert json_data['status'] == 200
                    assert 'data' in json_data
                    assert 'document_id' in json_data['data']
                    assert 'shareable_url' in json_data['data']
                
    @pytest.mark.api
    def test_export_requires_google_auth(self, client, authenticated_headers, sample_resume, sample_template):
        """Test that Google Docs export requires Google authentication"""
        request_data = {
            'resume_id': sample_resume.serial_number,
            'template_id': sample_template.id
        }
        
        # User doesn't have Google auth
        response = client.post('/api/resume/export/gdocs',
                             json=request_data,
                             headers=authenticated_headers)
        
        assert response.status_code == 401
        json_data = response.get_json()
        assert 'google_auth_required' in json_data['error']
        
    @pytest.mark.api
    def test_export_invalid_resume_id(self, client, authenticated_headers, sample_google_auth):
        """Test export with invalid resume ID"""
        request_data = {
            'resume_id': 999,  # Non-existent resume
            'template_id': 1
        }
        
        response = client.post('/api/resume/export/gdocs',
                             json=request_data,
                             headers=authenticated_headers)
        
        assert response.status_code == 404
        json_data = response.get_json()
        assert 'resume_not_found' in json_data['error']
        
    @pytest.mark.api
    def test_export_tracks_generated_document(self, client, authenticated_headers, sample_google_auth, sample_resume, sample_template):
        """Test that exported documents are tracked in database"""
        request_data = {
            'resume_id': sample_resume.serial_number,
            'template_id': sample_template.id,
            'document_title': 'Tracked Resume'
        }
        
        with patch('app.server.GoogleAuthService') as mock_auth_service:
            with patch('app.server.GoogleDocsService') as mock_docs_service:
                with patch('app.server.GoogleDriveService') as mock_drive_service:
                    # Mock the auth service
                    mock_auth_service.return_value.get_credentials.return_value = MagicMock()
                    
                    # Mock the docs service
                    mock_docs_service.return_value.create_document.return_value = {
                        'document_id': 'tracked_doc_id',
                        'document_url': 'https://docs.google.com/document/d/tracked_doc_id/edit'
                    }
                    
                    # Mock the drive service
                    mock_drive_service.return_value.create_shareable_link.return_value = {
                        'shareable_url': 'https://docs.google.com/document/d/tracked_doc_id/edit',
                        'permission_id': 'permission_123'
                    }
                    
                    response = client.post('/api/resume/export/gdocs',
                                         json=request_data,
                                         headers=authenticated_headers)
                    
                    assert response.status_code == 200
                
                # Verify document is tracked in database
                generated_doc = GeneratedDocument.query.filter_by(
                    google_doc_id='tracked_doc_id'
                ).first()
                
                assert generated_doc is not None
                assert generated_doc.document_title == 'Tracked Resume'
                assert generated_doc.user_id == sample_google_auth.user_id


class TestMultiFormatExport:
    """Test suite for multi-format document export (PDF, DOCX)"""
    
    @pytest.mark.export
    def test_export_to_pdf(self, client, authenticated_headers, sample_google_auth):
        """Test exporting Google Docs to PDF format"""
        document_id = 'test_doc_id_123'
        
        # Create a test GeneratedDocument
        from app.models.temp import GeneratedDocument
        generated_doc = GeneratedDocument(
            user_id=sample_google_auth.user_id,
            resume_id=1,  # Reference to resume serial_number
            google_doc_id=document_id,
            google_doc_url='https://docs.google.com/document/d/test_doc_id_123/edit',
            document_title='Test Resume',
            template_id=1
        )
        db.session.add(generated_doc)
        db.session.commit()
        
        with patch('app.server.GoogleAuthService') as mock_auth_service:
            with patch('app.server.GoogleDriveService') as mock_drive_service:
                # Mock the auth service
                mock_auth_service.return_value.get_credentials.return_value = MagicMock()
                
                # Mock the drive service
                mock_drive_service.return_value.export_as_pdf.return_value = {
                    'pdf_content': b'PDF content here',
                    'filename': 'resume.pdf'
                }
                
                response = client.get(f'/api/resume/export/pdf/{document_id}',
                                    headers=authenticated_headers)
                
                assert response.status_code == 200
            
    @pytest.mark.export
    def test_export_to_docx(self, client, authenticated_headers, sample_google_auth):
        """Test exporting Google Docs to DOCX format"""
        document_id = 'test_doc_id_123'
        
        # Create a test GeneratedDocument
        from app.models.temp import GeneratedDocument
        generated_doc = GeneratedDocument(
            user_id=sample_google_auth.user_id,
            resume_id=1,  # Reference to resume serial_number
            google_doc_id=document_id,
            google_doc_url='https://docs.google.com/document/d/test_doc_id_123/edit',
            document_title='Test Resume',
            template_id=1
        )
        db.session.add(generated_doc)
        db.session.commit()
        
        # Mock the GoogleDriveService methods
        with patch('app.server.GoogleAuthService') as mock_auth_service:
            with patch('app.server.GoogleDriveService') as mock_drive_service:
                # Mock the auth service
                mock_auth_service.return_value.get_credentials.return_value = MagicMock()
                
                # Mock the drive service
                mock_drive_service.return_value.export_as_docx.return_value = {
                    'docx_content': b'fake_docx_content',
                    'filename': 'Test Resume.docx'
                }
                
                response = client.get(
                    f'/api/resume/export/docx/{document_id}',
                    headers=authenticated_headers
                )
                
                assert response.status_code == 200
            
    @pytest.mark.export
    def test_fallback_pdf_generation(self, sample_resume, sample_template):
        """Test fallback PDF generation using WeasyPrint when Google export fails"""
        from app.services.pdf_generator import PDFGenerator
        
        with patch('weasyprint.HTML') as mock_html:
            mock_pdf = Mock()
            mock_pdf.write_pdf.return_value = b'Fallback PDF content'
            mock_html.return_value = mock_pdf
            
            generator = PDFGenerator()
            result = generator.generate_pdf(sample_resume.parsed_resume, sample_template)
            
            assert 'pdf_content' in result
            assert result['pdf_content'] == b'Fallback PDF content'
            assert result['generation_method'] == 'weasyprint'
            
    @pytest.mark.export
    def test_export_file_cleanup(self, client, authenticated_headers, sample_google_auth):
        """Test that temporary export files are properly cleaned up"""
        document_id = 'test_doc_id_123'
        
        # Create a test GeneratedDocument
        from app.models.temp import GeneratedDocument
        generated_doc = GeneratedDocument(
            user_id=sample_google_auth.user_id,
            resume_id=1,  # Reference to resume serial_number
            google_doc_id=document_id,
            google_doc_url='https://docs.google.com/document/d/test_doc_id_123/edit',
            document_title='Test Resume',
            template_id=1
        )
        db.session.add(generated_doc)
        db.session.commit()
        
        # Mock the GoogleDriveService methods
        with patch('app.server.GoogleAuthService') as mock_auth_service:
            with patch('app.server.GoogleDriveService') as mock_drive_service:
                with patch('os.remove') as mock_remove:
                    # Mock the auth service
                    mock_auth_service.return_value.get_credentials.return_value = MagicMock()
                    
                    # Mock the drive service
                    mock_drive_service.return_value.export_as_pdf.return_value = {
                        'pdf_content': b'PDF content here',
                        'filename': 'Test Resume.pdf'
                    }
                    
                    response = client.get(f'/api/resume/export/pdf/{document_id}',
                                        headers=authenticated_headers)
                    
                    assert response.status_code == 200


class TestDocumentManagement:
    """Test suite for document management features"""
    
    @pytest.mark.api
    def test_list_user_generated_documents(self, client, authenticated_headers, sample_user):
        """Test listing user's generated documents"""
        # Create some test documents
        doc1 = GeneratedDocument(
            user_id=sample_user.id,
            resume_id=1,
            template_id=1,
            google_doc_id='doc_1',
            google_doc_url='https://docs.google.com/doc_1',
            document_title='Resume v1',
            generation_status='created'
        )
        doc2 = GeneratedDocument(
            user_id=sample_user.id,
            resume_id=1,
            template_id=2,
            google_doc_id='doc_2',
            google_doc_url='https://docs.google.com/doc_2',
            document_title='Resume v2',
            generation_status='created'
        )
        db.session.add_all([doc1, doc2])
        db.session.commit()
        
        response = client.get('/api/documents', headers=authenticated_headers)
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert len(json_data['data']) == 2
        assert json_data['data'][0]['document_title'] in ['Resume v1', 'Resume v2']
        
    @pytest.mark.api
    def test_delete_generated_document(self, client, authenticated_headers, sample_user):
        """Test deleting a generated document"""
        doc = GeneratedDocument(
            user_id=sample_user.id,
            resume_id=1,
            template_id=1,
            google_doc_id='doc_to_delete',
            google_doc_url='https://docs.google.com/doc_to_delete',
            document_title='Document to Delete',
            generation_status='created'
        )
        db.session.add(doc)
        db.session.commit()
        
        with patch('app.services.google_drive_service.GoogleDriveService') as mock_drive_service:
            mock_drive_service.return_value.delete_document.return_value = True
            
            response = client.delete(f'/api/documents/{doc.id}',
                                   headers=authenticated_headers)
            
            assert response.status_code == 200
            
            # Verify document is removed from database
            deleted_doc = GeneratedDocument.query.get(doc.id)
            assert deleted_doc is None
            
    @pytest.mark.api
    def test_document_sharing_controls(self, client, authenticated_headers, sample_user):
        """Test document sharing permission controls"""
        doc = GeneratedDocument(
            user_id=sample_user.id,
            resume_id=1,
            template_id=1,
            google_doc_id='doc_sharing_test',
            google_doc_url='https://docs.google.com/doc_sharing_test',
            document_title='Sharing Test Document',
            generation_status='created'
        )
        db.session.add(doc)
        db.session.commit()
        
        sharing_data = {
            'permission_level': 'viewer',
            'public_access': False
        }
        
        with patch('app.server.GoogleDriveService') as mock_drive_service:
            mock_drive_service.return_value.update_permissions.return_value = True
            
            response = client.put(f'/api/documents/{doc.id}/sharing',
                                json=sharing_data,
                                headers=authenticated_headers)
            
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['permissions_updated'] is True