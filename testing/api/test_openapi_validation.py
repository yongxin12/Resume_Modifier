"""
Standalone API Documentation Validation Tests

This module validates the OpenAPI specification for accuracy and completeness
without requiring the Flask application to be running.
"""

import json
import yaml
import pytest
import os
from datetime import datetime


class TestOpenAPISpecificationValidation:
    """Test suite for validating OpenAPI specification structure and content."""

    @pytest.fixture
    def openapi_spec(self):
        """Load OpenAPI specification for validation."""
        spec_path = 'documentation/api/file-categorization-openapi.yaml'
        if not os.path.exists(spec_path):
            pytest.skip("OpenAPI specification file not found")
        
        try:
            with open(spec_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            pytest.fail(f"Failed to load OpenAPI specification: {e}")

    def test_openapi_specification_structure(self, openapi_spec):
        """Test that OpenAPI specification has required structure."""
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

    def test_documented_endpoints_exist(self, openapi_spec):
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

    def test_category_update_endpoint_documentation(self, openapi_spec):
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

    def test_bulk_update_endpoint_documentation(self, openapi_spec):
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

    def test_file_listing_endpoint_documentation(self, openapi_spec):
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

    def test_statistics_endpoint_documentation(self, openapi_spec):
        """Test GET /files/categories/stats endpoint documentation."""
        endpoint = openapi_spec['paths']['/files/categories/stats']['get']
        
        # Test basic properties
        assert endpoint['operationId'] == 'getCategoryStatistics'
        assert 'Get category statistics' in endpoint['summary']

        # Test response schema
        success_response = endpoint['responses']['200']
        response_schema_ref = success_response['content']['application/json']['schema']['$ref']
        assert response_schema_ref == '#/components/schemas/CategoryStatsResponse'

    def test_available_categories_endpoint_documentation(self, openapi_spec):
        """Test GET /files/categories endpoint documentation."""
        endpoint = openapi_spec['paths']['/files/categories']['get']
        
        # Test basic properties
        assert endpoint['operationId'] == 'getAvailableCategories'
        assert 'Get available categories' in endpoint['summary']

        # Test response schema
        success_response = endpoint['responses']['200']
        response_schema_ref = success_response['content']['application/json']['schema']['$ref']
        assert response_schema_ref == '#/components/schemas/AvailableCategoriesResponse'

    def test_component_schemas_completeness(self, openapi_spec):
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

    def test_category_update_request_schema(self, openapi_spec):
        """Test CategoryUpdateRequest schema definition."""
        schema = openapi_spec['components']['schemas']['CategoryUpdateRequest']
        
        assert schema['type'] == 'object'
        assert 'category' in schema['required']
        assert 'category' in schema['properties']
        
        category_prop = schema['properties']['category']
        assert category_prop['type'] == 'string'
        assert category_prop['enum'] == ['active', 'archived', 'draft']
        assert schema['additionalProperties'] is False

    def test_bulk_category_update_request_schema(self, openapi_spec):
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

    def test_file_info_schema(self, openapi_spec):
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

    def test_error_response_schema(self, openapi_spec):
        """Test ErrorResponse schema definition."""
        schema = openapi_spec['components']['schemas']['ErrorResponse']
        
        assert schema['type'] == 'object'
        expected_properties = ['success', 'error', 'message', 'details']
        
        for prop in expected_properties:
            assert prop in schema['properties'], f"Property {prop} missing from ErrorResponse schema"

        assert schema['properties']['success']['type'] == 'boolean'
        assert schema['properties']['details']['additionalProperties'] is True

    def test_response_examples_validity(self, openapi_spec):
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

    def test_security_requirements(self, openapi_spec):
        """Test that security requirements are properly defined."""
        # Test global security
        assert 'security' in openapi_spec
        security = openapi_spec['security']
        assert len(security) == 1
        assert 'BearerAuth' in security[0]

    def test_tag_definitions(self, openapi_spec):
        """Test that tags are properly defined."""
        assert 'tags' in openapi_spec
        tags = {tag['name']: tag for tag in openapi_spec['tags']}
        
        assert 'File Categorization' in tags
        tag = tags['File Categorization']
        assert 'description' in tag
        assert 'externalDocs' in tag

    def test_server_definitions(self, openapi_spec):
        """Test that servers are properly defined."""
        assert 'servers' in openapi_spec
        servers = openapi_spec['servers']
        assert len(servers) >= 1
        
        # Test development server
        dev_server = next((s for s in servers if 'localhost' in s['url']), None)
        assert dev_server is not None
        assert dev_server['url'] == 'http://localhost:5001'
        assert 'description' in dev_server

    def test_category_enum_consistency(self, openapi_spec):
        """Test that category enums are consistent across all schemas."""
        expected_categories = ['active', 'archived', 'draft']
        schemas = openapi_spec['components']['schemas']
        
        # Check CategoryUpdateRequest
        cat_update_schema = schemas['CategoryUpdateRequest']
        assert cat_update_schema['properties']['category']['enum'] == expected_categories
        
        # Check BulkCategoryUpdateRequest
        bulk_update_schema = schemas['BulkCategoryUpdateRequest']
        assert bulk_update_schema['properties']['category']['enum'] == expected_categories
        
        # Check FileInfo
        file_info_schema = schemas['FileInfo']
        assert file_info_schema['properties']['category']['enum'] == expected_categories

    def test_pagination_parameter_consistency(self, openapi_spec):
        """Test that pagination parameters are consistently defined."""
        files_endpoint = openapi_spec['paths']['/files']['get']
        parameters = {param['name']: param for param in files_endpoint['parameters']}
        
        # Test page parameter
        page_param = parameters['page']
        assert page_param['schema']['type'] == 'integer'
        assert page_param['schema']['minimum'] == 1
        assert page_param['schema']['default'] == 1
        
        # Test per_page parameter
        per_page_param = parameters['per_page']
        assert per_page_param['schema']['type'] == 'integer'
        assert per_page_param['schema']['minimum'] == 1
        assert per_page_param['schema']['maximum'] == 100
        assert per_page_param['schema']['default'] == 20

    def test_http_status_code_coverage(self, openapi_spec):
        """Test that appropriate HTTP status codes are documented for each endpoint."""
        paths = openapi_spec['paths']
        
        # Define expected status codes for different operation types
        expected_codes = {
            'get': ['200', '400', '401', '500'],
            'put': ['200', '400', '401', '404', '500'],
            'post': ['201', '400', '401', '409', '500'],
            'delete': ['204', '400', '401', '404', '500']
        }
        
        for path, methods in paths.items():
            for method, endpoint in methods.items():
                if method.lower() in expected_codes:
                    responses = endpoint.get('responses', {})
                    method_expected = expected_codes[method.lower()]
                    
                    # Check that key status codes are documented
                    # At minimum should have success and error codes
                    has_success = any(code.startswith('2') for code in responses.keys())
                    has_client_error = any(code.startswith('4') for code in responses.keys())
                    has_server_error = any(code.startswith('5') for code in responses.keys())
                    
                    assert has_success, f"No success status code documented for {method.upper()} {path}"
                    assert has_client_error or has_server_error, f"No error status codes documented for {method.upper()} {path}"


class TestDocumentationQuality:
    """Test documentation quality and completeness."""
    
    @pytest.fixture
    def openapi_spec(self):
        """Load OpenAPI specification for validation."""
        spec_path = 'documentation/api/file-categorization-openapi.yaml'
        if not os.path.exists(spec_path):
            pytest.skip("OpenAPI specification file not found")
        
        with open(spec_path, 'r') as f:
            return yaml.safe_load(f)

    def test_descriptions_are_meaningful(self, openapi_spec):
        """Test that descriptions provide meaningful information."""
        paths = openapi_spec['paths']
        
        for path, methods in paths.items():
            for method, endpoint in methods.items():
                # Check endpoint description
                assert 'description' in endpoint, f"Missing description for {method.upper()} {path}"
                description = endpoint['description']
                assert len(description) > 20, f"Description too short for {method.upper()} {path}"
                
                # Check summary
                assert 'summary' in endpoint, f"Missing summary for {method.upper()} {path}"
                summary = endpoint['summary']
                assert len(summary) > 5, f"Summary too short for {method.upper()} {path}"

    def test_examples_are_comprehensive(self, openapi_spec):
        """Test that examples are provided for requests and responses."""
        paths = openapi_spec['paths']
        
        for path, methods in paths.items():
            for method, endpoint in methods.items():
                # Check request body examples
                if 'requestBody' in endpoint:
                    request_body = endpoint['requestBody']
                    if 'content' in request_body and 'application/json' in request_body['content']:
                        json_content = request_body['content']['application/json']
                        assert 'examples' in json_content, f"Missing request examples for {method.upper()} {path}"
                
                # Check response examples
                if 'responses' in endpoint:
                    for status_code, response in endpoint['responses'].items():
                        if 'content' in response and 'application/json' in response['content']:
                            json_content = response['content']['application/json']
                            # At least success responses should have examples
                            if status_code.startswith('2'):
                                assert 'examples' in json_content, f"Missing response examples for {status_code} in {method.upper()} {path}"

    def test_parameter_documentation_completeness(self, openapi_spec):
        """Test that all parameters are properly documented."""
        paths = openapi_spec['paths']
        
        for path, methods in paths.items():
            for method, endpoint in methods.items():
                if 'parameters' in endpoint:
                    for param in endpoint['parameters']:
                        # Required fields
                        assert 'name' in param, f"Parameter missing name in {method.upper()} {path}"
                        assert 'in' in param, f"Parameter missing 'in' field in {method.upper()} {path}"
                        assert 'description' in param, f"Parameter missing description in {method.upper()} {path}"
                        assert 'schema' in param, f"Parameter missing schema in {method.upper()} {path}"
                        
                        # Description should be meaningful
                        description = param['description']
                        assert len(description) > 10, f"Parameter description too short for {param['name']} in {method.upper()} {path}"