"""
Test-driven development for Resume Generation Engine
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from app.models.temp import Resume, ResumeTemplate


class TestResumeGenerationService:
    """Test suite for resume generation service"""
    
    @pytest.mark.ai
    def test_create_resume_generator_service(self):
        """Test ResumeGenerator service class creation"""
        from app.services.resume_generator import ResumeGenerator
        
        generator = ResumeGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_content')
        assert hasattr(generator, 'optimize_for_job')
        assert hasattr(generator, 'apply_template')
        
    @pytest.mark.ai
    def test_generate_resume_from_user_data(self, sample_user, sample_template, sample_resume_data, sample_job_description):
        """Test generating resume content from user data and job description"""
        from app.services.resume_generator import ResumeGenerator
        
        generator = ResumeGenerator()
        
        # Mock OpenAI response
        with patch('app.services.resume_ai.ResumeAI') as mock_ai:
            mock_ai.return_value.optimize_content.return_value = {
                'optimized_content': 'Enhanced resume content with job-specific keywords',
                'improvements': ['Added relevant technical skills', 'Improved job descriptions'],
                'ats_score': 88
            }
            
            result = generator.generate_content(
                user_data=sample_resume_data,
                job_description=sample_job_description,
                template_id=sample_template.id
            )
            
            assert 'optimized_content' in result
            assert 'improvements' in result
            assert 'ats_score' in result
            assert result['ats_score'] >= 80
            
    @pytest.mark.ai
    def test_job_description_keyword_extraction(self, sample_job_description):
        """Test extracting keywords from job description"""
        from app.services.resume_generator import ResumeGenerator
        
        generator = ResumeGenerator()
        keywords = generator.extract_job_keywords(sample_job_description)
        
        # Expected keywords should match what's in sample_job_description fixture
        expected_keywords = ['Python', 'Flask', 'Django', 'PostgreSQL', 'MySQL', 'Bachelor', 'Computer Science']
        
        for keyword in expected_keywords:
            assert keyword in keywords or keyword.lower() in [k.lower() for k in keywords]
            
    @pytest.mark.ai
    def test_resume_optimization_for_ats(self, sample_resume_data, sample_job_description):
        """Test optimizing resume content for ATS compatibility"""
        from app.services.resume_generator import ResumeGenerator
        
        generator = ResumeGenerator()
        
        with patch('app.services.resume_ai.ResumeAI') as mock_ai:
            mock_ai.return_value.optimize_for_ats.return_value = {
                'ats_optimized_content': sample_resume_data,
                'ats_score': 92,
                'improvements': ['Improved keyword density', 'Standardized formatting']
            }
            
            result = generator.optimize_for_ats(sample_resume_data, sample_job_description)
            
            assert 'ats_optimized_content' in result
            assert 'ats_score' in result
            assert result['ats_score'] >= 85
            
    @pytest.mark.templates
    def test_apply_template_formatting(self, sample_resume_data, sample_template):
        """Test applying template formatting to resume content"""
        from app.services.resume_generator import ResumeGenerator
        
        generator = ResumeGenerator()
        formatted_resume = generator.apply_template(sample_resume_data, sample_template)
        
        assert 'formatted_content' in formatted_resume
        assert 'template_applied' in formatted_resume
        assert formatted_resume['template_applied'] == sample_template.id
        
    @pytest.mark.templates
    def test_template_section_ordering(self, sample_resume_data, sample_template):
        """Test that resume sections are ordered according to template"""
        from app.services.resume_generator import ResumeGenerator
        
        generator = ResumeGenerator()
        result = generator.apply_template(sample_resume_data, sample_template)
        
        # Template sections: ['header', 'summary', 'experience', 'education', 'skills']
        formatted_sections = result['formatted_content']['sections']
        section_order = list(formatted_sections.keys())
        
        expected_order = ['header', 'summary', 'experience', 'education', 'skills']
        assert section_order == expected_order
        
    @pytest.mark.ai
    def test_content_personalization(self, sample_user, sample_resume_data, sample_job_description):
        """Test personalizing content based on user profile"""
        from app.services.resume_generator import ResumeGenerator
        
        generator = ResumeGenerator()
        
        # Add user profile information
        user_profile = {
            'first_name': sample_user.first_name,
            'last_name': sample_user.last_name,
            'city': sample_user.city,
            'bio': sample_user.bio
        }
        
        result = generator.personalize_content(sample_resume_data, user_profile, sample_job_description)
        
        assert 'personalized_content' in result
        assert result['personalized_content']['userInfo']['firstName'] == sample_user.first_name
        assert result['personalized_content']['userInfo']['lastName'] == sample_user.last_name


class TestResumeGenerationAPI:
    """Test suite for resume generation API endpoints"""
    
    @pytest.mark.api
    def test_generate_resume_endpoint(self, client, authenticated_headers, sample_template, sample_resume_data, sample_job_description):
        """Test /api/resume/generate endpoint"""
        request_data = {
            'user_data': sample_resume_data,
            'job_description': sample_job_description,
            'template_id': sample_template.id
        }
        
        with patch('app.services.resume_generator.ResumeGenerator') as mock_generator:
            mock_generator.return_value.generate_content.return_value = {
                'generated_resume': sample_resume_data,
                'optimizations_applied': ['keyword_optimization', 'ats_formatting'],
                'ats_score': 87
            }
            
            response = client.post('/api/resume/generate',
                                 json=request_data,
                                 headers=authenticated_headers)
            
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['status'] == 200
            assert 'data' in json_data
            assert 'generated_resume' in json_data['data']
            assert 'ats_score' in json_data['data']
            
    @pytest.mark.api
    def test_generate_resume_missing_data(self, client, authenticated_headers):
        """Test resume generation with missing required data"""
        incomplete_data = {
            'template_id': 1
            # Missing user_data and job_description
        }
        
        response = client.post('/api/resume/generate',
                             json=incomplete_data,
                             headers=authenticated_headers)
        
        assert response.status_code == 400
        json_data = response.get_json()
        assert 'error' in json_data
        assert 'required_fields' in json_data['error']
        
    @pytest.mark.api
    def test_generate_resume_invalid_template(self, client, authenticated_headers, sample_resume_data, sample_job_description):
        """Test resume generation with invalid template ID"""
        request_data = {
            'user_data': sample_resume_data,
            'job_description': sample_job_description,
            'template_id': 999  # Non-existent template
        }
        
        response = client.post('/api/resume/generate',
                             json=request_data,
                             headers=authenticated_headers)
        
        assert response.status_code == 404
        json_data = response.get_json()
        assert 'error' in json_data
        assert 'template_not_found' in json_data['error']
        
    @pytest.mark.api
    def test_generate_resume_with_authentication(self, client, sample_template, sample_resume_data, sample_job_description):
        """Test that resume generation requires authentication"""
        request_data = {
            'user_data': sample_resume_data,
            'job_description': sample_job_description,
            'template_id': sample_template.id
        }
        
        # Request without authentication headers
        response = client.post('/api/resume/generate', json=request_data)
        
        assert response.status_code == 401
        json_data = response.get_json()
        assert 'error' in json_data
        assert 'authentication_required' in json_data['error']


class TestTemplateRendering:
    """Test suite for template rendering with Jinja2"""
    
    @pytest.mark.templates
    def test_jinja2_template_rendering(self, sample_resume_data, sample_template):
        """Test rendering resume data with Jinja2 template"""
        from app.services.template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        rendered_html = renderer.render(sample_resume_data, sample_template)
        
        # Check for HTML structure (case insensitive)
        assert '<html' in rendered_html.lower()
        assert sample_resume_data['userInfo']['firstName'] in rendered_html
        assert sample_resume_data['userInfo']['lastName'] in rendered_html
        assert sample_resume_data['workExperience'][0]['companyName'] in rendered_html
        
    @pytest.mark.templates
    def test_template_style_application(self, sample_resume_data, sample_template):
        """Test that template styles are properly applied"""
        from app.services.template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        rendered_html = renderer.render(sample_resume_data, sample_template)
        
        # Check for style elements from template config
        assert 'font-family: Arial' in rendered_html
        assert sample_template.style_config['color_scheme']['primary'] in rendered_html
        
    @pytest.mark.templates
    def test_template_section_conditional_rendering(self, sample_template):
        """Test conditional rendering of resume sections"""
        from app.services.template_renderer import TemplateRenderer
        
        # Resume data with missing sections
        incomplete_resume_data = {
            'userInfo': {
                'firstName': 'Test',
                'lastName': 'User'
            },
            'workExperience': [
                {
                    'companyName': 'Test Company',
                    'jobTitle': 'Test Position'
                }
            ]
            # Missing education, skills, etc.
        }
        
        renderer = TemplateRenderer()
        rendered_html = renderer.render(incomplete_resume_data, sample_template)
        
        # Should render available sections
        assert 'Test User' in rendered_html
        assert 'Test Company' in rendered_html
        
        # Should not render missing sections (check section titles, not CSS)
        assert 'Education</div>' not in rendered_html or '>Education<' not in rendered_html
        
    @pytest.mark.templates
    def test_template_responsive_design(self, sample_resume_data, sample_template):
        """Test that templates generate responsive HTML"""
        from app.services.template_renderer import TemplateRenderer
        
        renderer = TemplateRenderer()
        rendered_html = renderer.render(sample_resume_data, sample_template)
        
        # Check for responsive design elements
        assert '@media' in rendered_html or 'viewport' in rendered_html
        assert 'responsive' in rendered_html or 'mobile' in rendered_html or 'max-width' in rendered_html


class TestAIContentOptimization:
    """Test suite for AI-powered content optimization"""
    
    @pytest.mark.ai
    def test_ai_keyword_matching(self, sample_resume_data, sample_job_description):
        """Test AI keyword matching between resume and job description"""
        from app.services.ai_optimizer import AIOptimizer
        
        optimizer = AIOptimizer()
        
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'keyword_matches': ['Python', 'Flask', 'PostgreSQL'],
                            'missing_keywords': ['AWS', 'Docker'],
                            'optimization_suggestions': ['Add cloud experience', 'Emphasize database skills']
                        })
                    }
                }]
            }
            
            result = optimizer.analyze_keywords(sample_resume_data, sample_job_description)
            
            assert 'keyword_matches' in result
            assert 'missing_keywords' in result
            assert 'optimization_suggestions' in result
            assert len(result['keyword_matches']) > 0
            
    @pytest.mark.ai
    def test_ai_language_enhancement(self, sample_resume_data):
        """Test AI language and clarity enhancement"""
        from app.services.ai_optimizer import AIOptimizer
        
        optimizer = AIOptimizer()
        
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'enhanced_content': sample_resume_data,
                            'language_improvements': ['Improved action verbs', 'Enhanced clarity'],
                            'readability_score': 95
                        })
                    }
                }]
            }
            
            result = optimizer.enhance_language(sample_resume_data)
            
            assert 'enhanced_content' in result
            assert 'language_improvements' in result
            assert 'readability_score' in result
            assert result['readability_score'] >= 90
            
    @pytest.mark.ai
    def test_ai_ats_optimization(self, sample_resume_data, sample_job_description):
        """Test AI optimization for ATS systems"""
        from app.services.ai_optimizer import AIOptimizer
        
        optimizer = AIOptimizer()
        
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'ats_optimized_content': sample_resume_data,
                            'ats_score': 91,
                            'ats_improvements': ['Standardized formatting', 'Improved keyword density'],
                            'compliance_check': True
                        })
                    }
                }]
            }
            
            result = optimizer.optimize_for_ats(sample_resume_data, sample_job_description)
            
            assert 'ats_optimized_content' in result
            assert 'ats_score' in result
            assert 'compliance_check' in result
            assert result['ats_score'] >= 85
            assert result['compliance_check'] is True