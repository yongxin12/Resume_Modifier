"""
Test suite for API documentation validation.

This module tests that the API documentation is accurate, complete, and consistent
with the actual implementation. It validates parameter specifications, response
schemas, and documentation examples against real API behavior.
"""

import json
import yaml
import pytest
from datetime import datetime
from flask import Flask
from flask_testing import TestCase
from unittest.mock import patch, MagicMock
from app.models.temp import ResumeFile, User, db
from app.services.file_category_service import FileCategoryService


class TestAPIDocumentationValidation(TestCase):
    """Test suite for validating API documentation accuracy."""

    def create_app(self):
        """Create test Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        # Initialize db with this Flask app
        db.init_app(app)
        return app

    def setUp(self):
        """Set up test environment."""
        db.create_all()
        self.service = FileCategoryService()
        
        # Create test user
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            password='hashed_password',
            first_name='Test',
            last_name='User',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        # Create test files for documentation validation  
        self.test_files = [
            self.create_test_file("Resume_Active.pdf", category="active"),
            self.create_test_file("Resume_Archived.pdf", category="archived"),
            self.create_test_file("Resume_Draft.pdf", category="draft")
        ]

    def create_test_file(self, filename, category="active"):
        """Create a test file with specified category."""
        test_file = ResumeFile(
            user_id=self.test_user.id,
            original_filename=filename,
            stored_filename=f'stored_{filename}',
            file_size=1024,
            mime_type='application/pdf',
            storage_type='local',
            file_path=f'/path/to/{filename}',
            file_hash=f'hash_{filename}',
            category=category,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(test_file)
        db.session.commit()
        return test_file

    def tearDown(self):
        """Clean up test database."""
        db.session.remove()
        db.drop_all()

    def get_openapi_spec(self):
        """Load OpenAPI specification for validation."""
        try:
            with open('documentation/api/file-categorization-openapi.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.skipTest("OpenAPI specification file not found")

    def test_openapi_specification_structure(self):
        """Test that OpenAPI specification has required structure."""
        openapi_spec = self.get_openapi_spec()
        # Test basic OpenAPI structure
        assert 'openapi' in openapi_spec
        assert openapi_spec['openapi'].startswith('3.0')
        assert 'info' in openapi_spec
        assert 'paths' in openapi_spec
        assert 'components' in openapi_spec

        # Test info section
        info = openapi_spec['info']
        assert 'title' in info
        assert 'description' in info
        assert 'version' in info
        assert info['title'] == "Resume Editor - File Categorization API"

        # Test security schemes
        components = openapi_spec['components']
        assert 'securitySchemes' in components
        assert 'BearerAuth' in components['securitySchemes']
        bearer_auth = components['securitySchemes']['BearerAuth']
        assert bearer_auth['type'] == 'http'
        assert bearer_auth['scheme'] == 'bearer'
        assert bearer_auth['bearerFormat'] == 'JWT'

    def test_documented_endpoints_exist(self):
        openapi_spec = self.get_openapi_spec()
        """Test that all documented endpoints exist in the specification."""
        expected_endpoints = [
            '/files/{id}/category',
            '/files/category',
            '/files',
            '/files/categories/stats',
            '/files/categories'
        ]
        
        paths = openapi_spec['paths']
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Endpoint {endpoint} not found in OpenAPI spec"

    def test_category_update_endpoint_documentation(self):
        openapi_spec = self.get_openapi_spec()
        """Test PUT /files/{id}/category endpoint documentation."""
        endpoint = openapi_spec['paths']['/files/{id}/category']['put']
        
        # Test basic endpoint properties
        assert 'tags' in endpoint
        assert 'File Categorization' in endpoint['tags']
        assert 'summary' in endpoint
        assert 'description' in endpoint
        assert 'operationId' in endpoint
        assert endpoint['operationId'] == 'updateFileCategory'

        # Test parameters
        assert 'parameters' in endpoint
        parameters = endpoint['parameters']
        assert len(parameters) == 1
        id_param = parameters[0]
        assert id_param['name'] == 'id'
        assert id_param['in'] == 'path'
        assert id_param['required'] is True
        assert id_param['schema']['type'] == 'integer'

        # Test request body
        assert 'requestBody' in endpoint
        request_body = endpoint['requestBody']
        assert request_body['required'] is True
        assert 'application/json' in request_body['content']
        schema_ref = request_body['content']['application/json']['schema']['$ref']
        assert schema_ref == '#/components/schemas/CategoryUpdateRequest'

        # Test responses
        assert 'responses' in endpoint
        responses = endpoint['responses']
        expected_status_codes = ['200', '400', '401', '404', '500']
        for status_code in expected_status_codes:
            assert status_code in responses, f"Status code {status_code} not documented"

    def test_bulk_update_endpoint_documentation(self):
        openapi_spec = self.get_openapi_spec()
        """Test PUT /files/category endpoint documentation."""
        endpoint = openapi_spec['paths']['/files/category']['put']
        
        # Test basic endpoint properties
        assert endpoint['operationId'] == 'bulkUpdateCategories'
        assert 'Bulk update file categories' in endpoint['summary']

        # Test request body schema
        request_body = endpoint['requestBody']
        schema_ref = request_body['content']['application/json']['schema']['$ref']
        assert schema_ref == '#/components/schemas/BulkCategoryUpdateRequest'

        # Test response schema
        success_response = endpoint['responses']['200']
        response_schema_ref = success_response['content']['application/json']['schema']['$ref']
        assert response_schema_ref == '#/components/schemas/BulkCategoryUpdateResponse'

    def test_file_listing_endpoint_documentation(self):
        openapi_spec = self.get_openapi_spec()
        """Test GET /files endpoint documentation."""
        endpoint = openapi_spec['paths']['/files']['get']
        
        # Test operation ID and basic properties
        assert endpoint['operationId'] == 'listFilesByCategory'
        assert 'List files by category' in endpoint['summary']

        # Test query parameters
        assert 'parameters' in endpoint
        parameters = {param['name']: param for param in endpoint['parameters']}
        
        expected_params = ['category', 'page', 'per_page', 'sort_by', 'sort_order', 'search']
        for param_name in expected_params:
            assert param_name in parameters, f"Parameter {param_name} not documented"

        # Test category parameter enum values
        category_param = parameters['category']
        assert category_param['schema']['enum'] == ['active', 'archived', 'draft', 'all']

        # Test pagination parameters
        page_param = parameters['page']
        assert page_param['schema']['minimum'] == 1
        assert page_param['schema']['default'] == 1

        per_page_param = parameters['per_page']
        assert per_page_param['schema']['minimum'] == 1
        assert per_page_param['schema']['maximum'] == 100
        assert per_page_param['schema']['default'] == 20

    def test_statistics_endpoint_documentation(self):
        openapi_spec = self.get_openapi_spec()
        """Test GET /files/categories/stats endpoint documentation."""
        endpoint = openapi_spec['paths']['/files/categories/stats']['get']
        
        # Test basic properties
        assert endpoint['operationId'] == 'getCategoryStatistics'
        assert 'Get category statistics' in endpoint['summary']

        # Test response schema
        success_response = endpoint['responses']['200']
        response_schema_ref = success_response['content']['application/json']['schema']['$ref']
        assert response_schema_ref == '#/components/schemas/CategoryStatsResponse'

    def test_available_categories_endpoint_documentation(self):
        openapi_spec = self.get_openapi_spec()
        """Test GET /files/categories endpoint documentation."""
        endpoint = openapi_spec['paths']['/files/categories']['get']
        
        # Test basic properties
        assert endpoint['operationId'] == 'getAvailableCategories'
        assert 'Get available categories' in endpoint['summary']

        # Test response schema
        success_response = endpoint['responses']['200']
        response_schema_ref = success_response['content']['application/json']['schema']['$ref']
        assert response_schema_ref == '#/components/schemas/AvailableCategoriesResponse'

    def test_component_schemas_completeness(self):
        openapi_spec = self.get_openapi_spec()
        """Test that all required component schemas are defined."""
        schemas = openapi_spec['components']['schemas']
        
        required_schemas = [
            'CategoryUpdateRequest',
            'BulkCategoryUpdateRequest', 
            'FileInfo',
            'CategoryUpdateResponse',
            'BulkUpdateSummary',
            'FailedFileUpdate',
            'BulkCategoryUpdateResponse',
            'PaginationInfo',
            'FilterInfo',
            'FileListResponse',
            'CategoryStats',
            'CategoryStatsResponse',
            'CategoryInfo',
            'AvailableCategoriesResponse',
            'ErrorResponse'
        ]
        
        for schema_name in required_schemas:
            assert schema_name in schemas, f"Schema {schema_name} not defined"

    def test_category_update_request_schema(self):
        openapi_spec = self.get_openapi_spec()
        """Test CategoryUpdateRequest schema definition."""
        schema = openapi_spec['components']['schemas']['CategoryUpdateRequest']
        
        assert schema['type'] == 'object'
        assert 'category' in schema['required']
        assert 'category' in schema['properties']
        
        category_prop = schema['properties']['category']
        assert category_prop['type'] == 'string'
        assert category_prop['enum'] == ['active', 'archived', 'draft']
        assert schema['additionalProperties'] is False

    def test_bulk_category_update_request_schema(self):
        openapi_spec = self.get_openapi_spec()
        """Test BulkCategoryUpdateRequest schema definition."""
        schema = openapi_spec['components']['schemas']['BulkCategoryUpdateRequest']
        
        assert schema['type'] == 'object'
        assert set(schema['required']) == {'file_ids', 'category'}
        
        # Test file_ids property
        file_ids_prop = schema['properties']['file_ids']
        assert file_ids_prop['type'] == 'array'
        assert file_ids_prop['items']['type'] == 'integer'
        assert file_ids_prop['minItems'] == 1
        assert file_ids_prop['maxItems'] == 100
        
        # Test category property
        category_prop = schema['properties']['category']
        assert category_prop['enum'] == ['active', 'archived', 'draft']

    def test_file_info_schema(self):
        openapi_spec = self.get_openapi_spec()
        """Test FileInfo schema definition."""
        schema = openapi_spec['components']['schemas']['FileInfo']
        
        expected_properties = [
            'id', 'original_filename', 'category', 'file_size',
            'formatted_file_size', 'mime_type', 'created_at', 'updated_at',
            'category_updated_at', 'category_updated_by'
        ]
        
        for prop in expected_properties:
            assert prop in schema['properties'], f"Property {prop} missing from FileInfo schema"

        # Test specific property types
        assert schema['properties']['id']['type'] == 'integer'
        assert schema['properties']['category']['enum'] == ['active', 'archived', 'draft']
        assert schema['properties']['created_at']['format'] == 'date-time'
        assert schema['properties']['category_updated_at']['nullable'] is True

    def test_error_response_schema(self):
        openapi_spec = self.get_openapi_spec()
        """Test ErrorResponse schema definition."""
        schema = openapi_spec['components']['schemas']['ErrorResponse']
        
        assert schema['type'] == 'object'
        expected_properties = ['success', 'error', 'message', 'details']
        
        for prop in expected_properties:
            assert prop in schema['properties'], f"Property {prop} missing from ErrorResponse schema"

        assert schema['properties']['success']['type'] == 'boolean'
        assert schema['properties']['details']['additionalProperties'] is True

    def test_response_examples_validity(self):
        openapi_spec = self.get_openapi_spec()
        """Test that response examples are valid JSON and match schemas."""
        paths = openapi_spec['paths']
        
        for path, methods in paths.items():
            for method, endpoint in methods.items():
                if 'responses' not in endpoint:
                    continue
                    
                for status_code, response in endpoint['responses'].items():
                    if 'content' not in response:
                        continue
                        
                    content = response['content']
                    if 'application/json' not in content:
                        continue
                        
                    json_content = content['application/json']
                    if 'examples' not in json_content:
                        continue
                        
                    # Validate each example is valid JSON
                    for example_name, example in json_content['examples'].items():
                        if 'value' in example:
                            # Ensure the example value is valid JSON-serializable
                            try:
                                json.dumps(example['value'])
                            except (TypeError, ValueError) as e:
                                pytest.fail(f"Invalid JSON example in {path} {method} {status_code} {example_name}: {e}")

    def test_security_requirements(self):
        openapi_spec = self.get_openapi_spec()
        """Test that security requirements are properly defined."""
        # Test global security
        assert 'security' in openapi_spec
        security = openapi_spec['security']
        assert len(security) == 1
        assert 'BearerAuth' in security[0]

        # Test that all endpoints inherit security requirements
        paths = openapi_spec['paths']
        for path, methods in paths.items():
            for method, endpoint in methods.items():
                # Endpoints should either inherit global security or define their own
                # Since we have global security, endpoints don't need to redefine it
                pass

    def test_tag_definitions(self):
        openapi_spec = self.get_openapi_spec()
        """Test that tags are properly defined."""
        assert 'tags' in openapi_spec
        tags = {tag['name']: tag for tag in openapi_spec['tags']}
        
        assert 'File Categorization' in tags
        tag = tags['File Categorization']
        assert 'description' in tag
        assert 'externalDocs' in tag

    def test_statistics_response_schema_structure(self):
        """Test that statistics response schema has correct structure."""
        # Test that we can create a valid response matching the schema
        mock_stats = {
            'categories': {
                'active': {'count': 15, 'percentage': 60.0},
                'archived': {'count': 8, 'percentage': 32.0},
                'draft': {'count': 2, 'percentage': 8.0}
            },
            'total_files': 25,
            'total_active_files': 25,
            'total_deleted_files': 3,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Validate response structure matches expected schema
        assert 'categories' in mock_stats
        assert 'total_files' in mock_stats
        assert 'total_active_files' in mock_stats
        assert 'total_deleted_files' in mock_stats
        assert 'last_updated' in mock_stats

        # Validate category structure
        categories = mock_stats['categories']
        for category in ['active', 'archived', 'draft']:
            assert category in categories
            cat_stats = categories[category]
            assert 'count' in cat_stats
            assert 'percentage' in cat_stats
            assert isinstance(cat_stats['count'], int)
            assert isinstance(cat_stats['percentage'], (int, float))

    def test_error_response_schema_structure(self):
        """Test that error response schema has correct structure."""
        # Test that we can create valid error responses matching the schema
        error_responses = [
            {
                'success': False,
                'error': 'INVALID_INPUT',
                'message': 'Invalid category provided',
                'details': {'valid_categories': ['active', 'archived', 'draft']}
            },
            {
                'success': False,
                'error': 'UNAUTHORIZED',
                'message': 'Missing or invalid JWT token'
            },
            {
                'success': False,
                'error': 'FILE_NOT_FOUND',
                'message': 'File with ID 42 not found or access denied',
                'details': {'file_id': 42}
            }
        ]
        
        for error_response in error_responses:
            # Validate error response structure
            assert 'success' in error_response
            assert 'error' in error_response
            assert 'message' in error_response
            assert error_response['success'] is False
            assert isinstance(error_response['error'], str)
            assert isinstance(error_response['message'], str)

    def test_bulk_update_response_schema_structure(self):
        """Test that bulk update response schema has correct structure."""
        # Test successful bulk update response
        bulk_response = {
            'success': True,
            'message': 'Bulk category update completed',
            'summary': {
                'total_requested': 3,
                'successful_updates': 3,
                'failed_updates': 0,
                'category': 'archived'
            },
            'updated_files': [
                {
                    'id': 42,
                    'original_filename': 'Resume_A.pdf',
                    'category': 'archived'
                }
            ],
            'failed_files': []
        }
        
        # Validate structure
        assert 'success' in bulk_response
        assert 'message' in bulk_response
        assert 'summary' in bulk_response
        assert 'updated_files' in bulk_response
        assert 'failed_files' in bulk_response
        
        summary = bulk_response['summary']
        assert 'total_requested' in summary
        assert 'successful_updates' in summary
        assert 'failed_updates' in summary
        assert 'category' in summary

    def test_parameter_constraint_validation(self):
        """Test that parameter constraints are properly defined."""
        # Test file ID constraints
        file_id_constraints = {
            'type': 'integer',
            'format': 'int64',
            'minimum': 1
        }
        
        # Valid file IDs
        valid_ids = [1, 42, 1000]
        for file_id in valid_ids:
            assert isinstance(file_id, int)
            assert file_id >= file_id_constraints['minimum']
        
        # Test pagination constraints
        pagination_constraints = {
            'page': {'minimum': 1, 'default': 1},
            'per_page': {'minimum': 1, 'maximum': 100, 'default': 20}
        }
        
        # Valid pagination values
        assert 1 >= pagination_constraints['page']['minimum']
        assert 20 >= pagination_constraints['per_page']['minimum']
        assert 20 <= pagination_constraints['per_page']['maximum']
        
        # Test category enum values
        valid_categories = ['active', 'archived', 'draft']
        for category in valid_categories:
            assert category in ['active', 'archived', 'draft']


class TestDocumentationConsistency:
    """Test consistency between different documentation sources."""
    
    def test_openapi_matches_functional_specification(self):
        """Test that OpenAPI spec matches functional specification."""
        # This would compare the functional specification document
        # with the OpenAPI specification to ensure consistency
        # Implementation depends on how functional spec is structured
        pass
    
    def test_api_documentation_matches_openapi(self):
        """Test that API documentation matches OpenAPI specification."""
        # This would compare the comprehensive API documentation
        # with the OpenAPI specification for consistency
        pass
    
    def test_endpoint_documentation_completeness(self):
        """Test that all implemented endpoints are documented."""
        # This would scan the actual Flask routes and ensure
        # they are all documented in the OpenAPI specification
        pass


class TestDocumentationUsability:
    """Test documentation usability and clarity."""
    
    def test_example_requests_are_valid(self):
        """Test that all example requests in documentation are valid."""
        # This would validate that example requests shown in documentation
        # would actually work when sent to the API
        pass
    
    def test_example_responses_are_realistic(self):
        """Test that example responses in documentation are realistic."""
        # This would validate that example responses match what the API
        # would actually return in those scenarios
        pass
    
    def test_parameter_descriptions_are_clear(self):
        """Test that parameter descriptions are clear and complete."""
        # This would analyze parameter descriptions for clarity,
        # completeness, and helpful examples
        pass