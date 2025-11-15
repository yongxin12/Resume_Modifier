"""
Resume Generation Engine
Handles AI-powered resume generation, content optimization, and template application
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from flask import current_app
from app.models.temp import Resume, ResumeTemplate, User
from app.services.resume_ai import ResumeAI
from app.extensions import db


class ResumeGenerator:
    """Service for generating and optimizing resumes using AI"""
    
    def __init__(self):
        """Initialize the resume generator"""
        # Don't initialize ResumeAI here since it requires extracted_text
        # We'll create it as needed in the methods
        pass
        
    def generate_content(self, user_data: Dict[str, Any], job_description: str, template_id: int) -> Dict[str, Any]:
        """
        Generate optimized resume content from user data and job description
        
        Args:
            user_data: User's resume data
            job_description: Target job description for optimization
            template_id: ID of the template to apply
            
        Returns:
            Dictionary containing optimized content, improvements, and ATS score
        """
        try:
            # Extract keywords from job description
            job_keywords = self.extract_job_keywords(job_description)
            
            # Get template
            template = ResumeTemplate.query.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Optimize content using AI
            ai_service = ResumeAI(extracted_text="")  # Empty text for generation mode
            optimization_result = ai_service.optimize_content(
                resume_data=user_data,
                job_description=job_description,
                keywords=job_keywords
            )
            
            # Apply template formatting
            formatted_content = self.apply_template(
                content=optimization_result.get('optimized_content', ''),
                template=template,
                user_data=user_data
            )
            
            return {
                'optimized_content': formatted_content,
                'improvements': optimization_result.get('improvements', []),
                'ats_score': optimization_result.get('ats_score', 0),
                'keywords_matched': job_keywords,
                'template_applied': template.name
            }
            
        except Exception as e:
            current_app.logger.error(f"Resume generation error: {str(e)}")
            raise
    
    def extract_job_keywords(self, job_description: str) -> List[str]:
        """
        Extract relevant keywords from job description
        
        Args:
            job_description: Job description text
            
        Returns:
            List of extracted keywords
        """
        # Common technical skills and qualifications
        skill_patterns = [
            r'\b(Python|Java|JavaScript|React|Angular|Vue|Node\.js|Express)\b',
            r'\b(Flask|Django|FastAPI|Spring|Laravel|Ruby on Rails)\b',
            r'\b(PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\b',
            r'\b(AWS|Azure|GCP|Docker|Kubernetes|Jenkins)\b',
            r'\b(Git|GitHub|GitLab|Agile|Scrum|DevOps)\b',
            r'\b(Machine Learning|AI|Data Science|Analytics)\b',
            r'\b(Bachelor|Master|PhD|Computer Science|Engineering)\b',
            r'\b(\d+)\+?\s*years?\s*experience\b',
        ]
        
        keywords = []
        job_text = job_description.upper()
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            keywords.extend(matches)
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def optimize_for_job(self, resume_content: str, job_description: str) -> Dict[str, Any]:
        """
        Optimize existing resume content for a specific job
        
        Args:
            resume_content: Current resume content
            job_description: Target job description
            
        Returns:
            Dictionary with optimized content and recommendations
        """
        try:
            job_keywords = self.extract_job_keywords(job_description)
            
            # Use AI service to optimize content
            ai_service = ResumeAI(extracted_text="")  # Empty text for optimization mode
            result = ai_service.optimize_content(
                resume_data={'content': resume_content},
                job_description=job_description,
                keywords=job_keywords
            )
            
            return {
                'optimized_content': result.get('optimized_content', resume_content),
                'keyword_recommendations': job_keywords,
                'ats_score': result.get('ats_score', 0),
                'improvements': result.get('improvements', [])
            }
            
        except Exception as e:
            current_app.logger.error(f"Resume optimization error: {str(e)}")
            raise
    
    def optimize_for_ats(self, resume_content: str, job_description: str) -> Dict[str, Any]:
        """
        Optimize resume content for ATS (Applicant Tracking Systems)
        Alias for optimize_for_job method with ATS-specific return format
        """
        result = self.optimize_for_job(resume_content, job_description)
        # Rename optimized_content to ats_optimized_content for ATS tests
        if 'optimized_content' in result:
            result['ats_optimized_content'] = result.pop('optimized_content')
        return result
    
    def apply_template(self, content: str, template: ResumeTemplate, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Apply template formatting to resume content
        
        Args:
            content: Resume content to format
            template: Template to apply
            user_data: Optional user data for personalization
            
        Returns:
            Dictionary with formatted content and template info
        """
        try:
            # Default user_data if not provided
            if user_data is None:
                user_data = {}
                
            # Get template configuration
            style_config = template.style_config if hasattr(template, 'style_config') else {}
            template_sections = template.sections if hasattr(template, 'sections') else []
            
            # If content is a dict (structured resume data), apply section ordering
            if isinstance(content, dict):
                formatted_content = content.copy()
                
                # Apply section ordering from template
                if template_sections and 'sections' not in formatted_content:
                    formatted_content['sections'] = template_sections
                    
            else:
                # For string content, create structured content with template sections
                formatted_content = {
                    'content': content,
                    'sections': template_sections if template_sections else ['summary', 'experience', 'education', 'skills']
                }
            
            # Apply template-specific formatting
            if template.name == 'Professional':
                formatted_content = self._apply_professional_formatting(formatted_content, user_data)
            elif template.name == 'Creative':
                formatted_content = self._apply_creative_formatting(formatted_content, user_data)
            elif template.name == 'Technical':
                formatted_content = self._apply_technical_formatting(formatted_content, user_data)
            else:
                # Default formatting
                formatted_content = self._apply_default_formatting(content, user_data)
            
            return {
                'formatted_content': formatted_content,
                'template_applied': template.id,
                'template_name': template.name
            }
            
        except Exception as e:
            current_app.logger.error(f"Template application error: {str(e)}")
            return {
                'formatted_content': content,
                'template_applied': template.id if template else None,
                'error': str(e)
            }
    
    def _apply_professional_formatting(self, content: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply professional template formatting"""
        # Professional template emphasizes clean structure and formal presentation
        if isinstance(content, dict):
            formatted = content.copy()
            # Ensure professional section ordering as ordered dict
            from collections import OrderedDict
            formatted['sections'] = OrderedDict([
                ('header', {}),
                ('summary', {}),
                ('experience', {}),
                ('education', {}),
                ('skills', {})
            ])
            formatted['style'] = 'professional'
            return formatted
        else:
            # Fallback for string content
            from collections import OrderedDict
            return {
                'content': content, 
                'style': 'professional', 
                'sections': OrderedDict([
                    ('header', {}),
                    ('summary', {}),
                    ('experience', {}),
                    ('education', {}),
                    ('skills', {})
                ])
            }
    
    def _apply_creative_formatting(self, content: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply creative template formatting"""
        if isinstance(content, dict):
            formatted = content.copy()
            from collections import OrderedDict
            formatted['sections'] = OrderedDict([
                ('header', {}),
                ('summary', {}),
                ('skills', {}),
                ('experience', {}),
                ('education', {})
            ])
            formatted['style'] = 'creative'
            return formatted
        else:
            from collections import OrderedDict
            return {
                'content': content, 
                'style': 'creative', 
                'sections': OrderedDict([
                    ('header', {}),
                    ('summary', {}),
                    ('skills', {}),
                    ('experience', {}),
                    ('education', {})
                ])
            }
    
    def _apply_technical_formatting(self, content: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply technical template formatting"""
        if isinstance(content, dict):
            formatted = content.copy()
            from collections import OrderedDict
            formatted['sections'] = OrderedDict([
                ('header', {}),
                ('summary', {}),
                ('skills', {}),
                ('experience', {}),
                ('certifications', {})
            ])
            formatted['style'] = 'technical'
            return formatted
        else:
            from collections import OrderedDict
            return {
                'content': content, 
                'style': 'technical', 
                'sections': OrderedDict([
                    ('header', {}),
                    ('summary', {}),
                    ('skills', {}),
                    ('experience', {}),
                    ('certifications', {})
                ])
            }
    
    def _apply_default_formatting(self, content: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default template formatting"""
        if isinstance(content, dict):
            formatted = content.copy()
            if 'sections' not in formatted:
                from collections import OrderedDict
                formatted['sections'] = OrderedDict([
                    ('header', {}),
                    ('summary', {}),
                    ('experience', {}),
                    ('education', {}),
                    ('skills', {})
                ])
            formatted['style'] = 'default'
            return formatted
        else:
            from collections import OrderedDict
            return {
                'content': content, 
                'style': 'default', 
                'sections': OrderedDict([
                    ('header', {}),
                    ('summary', {}),
                    ('experience', {}),
                    ('education', {}),
                    ('skills', {})
                ])
            }
    
    def personalize_content(self, content: str, user_profile: Dict[str, Any], job_description: str = None) -> Dict[str, Any]:
        """
        Personalize resume content based on user profile and job description
        
        Args:
            content: Resume content to personalize
            user_profile: User profile data including preferences, style, etc.
            job_description: Optional job description for targeted personalization
            
        Returns:
            Dictionary with personalized resume content
        """
        try:
            # If content is already a dict (structured resume), work with it directly
            if isinstance(content, dict):
                personalized_content = content.copy()
            else:
                # For string content, create a basic structure
                personalized_content = {'content': content}
            
            # Add user information to the personalized content
            if 'userInfo' not in personalized_content:
                personalized_content['userInfo'] = {}
            
            # Populate user information from profile
            personalized_content['userInfo']['firstName'] = user_profile.get('first_name', '')
            personalized_content['userInfo']['lastName'] = user_profile.get('last_name', '')
            personalized_content['userInfo']['city'] = user_profile.get('city', '')
            personalized_content['userInfo']['bio'] = user_profile.get('bio', '')
            
            # Apply tone preferences from user profile
            tone = user_profile.get('preferences', {}).get('tone', 'professional')
            if tone == 'casual' and isinstance(content, str):
                personalized_content['content'] = self._apply_casual_tone(content)
            elif tone == 'confident' and isinstance(content, str):
                personalized_content['content'] = self._apply_confident_tone(content)
            
            # Apply length preferences
            length = user_profile.get('preferences', {}).get('length', 'medium')
            if length == 'concise' and isinstance(content, str):
                personalized_content['content'] = self._make_concise(content)
            elif length == 'detailed' and isinstance(content, str):
                personalized_content['content'] = self._make_detailed(content)
            
            return {'personalized_content': personalized_content}
            
        except Exception as e:
            current_app.logger.error(f"Content personalization error: {str(e)}")
            return {'personalized_content': content if isinstance(content, dict) else {'content': content}}
    
    def _apply_casual_tone(self, content: str) -> str:
        """Apply casual tone to content"""
        # Simple tone adjustments (could be enhanced with NLP)
        replacements = {
            'utilized': 'used',
            'facilitated': 'helped',
            'implemented': 'built',
            'collaborated': 'worked with'
        }
        
        result = content
        for formal, casual in replacements.items():
            result = result.replace(formal, casual)
        
        return result
    
    def _apply_confident_tone(self, content: str) -> str:
        """Apply confident tone to content"""
        # Add action words and confident language
        confident_words = {
            'helped': 'led',
            'worked on': 'spearheaded',
            'participated in': 'drove',
            'contributed to': 'delivered'
        }
        
        result = content
        for weak, strong in confident_words.items():
            result = result.replace(weak, strong)
        
        return result
    
    def _make_concise(self, content: str) -> str:
        """Make content more concise"""
        # Simple concision (could be enhanced with NLP)
        lines = content.split('\n')
        concise_lines = []
        
        for line in lines:
            if len(line.strip()) > 0:
                # Remove redundant words
                line = re.sub(r'\b(very|really|quite|rather)\b', '', line)
                line = re.sub(r'\s+', ' ', line).strip()
                concise_lines.append(line)
        
        return '\n'.join(concise_lines)
    
    def _make_detailed(self, content: str) -> str:
        """Add more detail to content"""
        # This would typically involve AI enhancement
        # For now, just return original content
        return content