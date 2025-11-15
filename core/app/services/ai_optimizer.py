"""
AI-powered content optimization service for resume enhancement
"""

import json
import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Import openai for easier mocking in tests
import openai

load_dotenv()


class AIOptimizer:
    """Service for AI-powered resume content optimization"""
    
    def __init__(self):
        """Initialize the AI optimizer with OpenAI configuration"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    def analyze_keywords(self, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Analyze keyword matching between resume and job description
        
        Args:
            resume_data: Parsed resume data
            job_description: Target job description text
            
        Returns:
            Dictionary with keyword analysis results
        """
        try:
            # Prepare the prompt for keyword analysis
            resume_text = self._extract_resume_text(resume_data)
            
            prompt = f"""
            Analyze the keyword matching between this resume and job description.
            
            Resume:
            {resume_text}
            
            Job Description:
            {job_description}
            
            Return a JSON response with:
            - keyword_matches: array of keywords that match between resume and job
            - missing_keywords: array of important keywords from job that are missing in resume
            - optimization_suggestions: array of specific suggestions to improve keyword matching
            """
            
            # Use openai.ChatCompletion.create for consistency with test mocking
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert resume analyzer. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Handle both mock (dict) and real OpenAI response (object) formats
            if isinstance(response, dict):
                content = response['choices'][0]['message']['content']
            else:
                content = response.choices[0].message.content
                
            result = json.loads(content)
            return result
            
        except Exception as e:
            # Return fallback structure if OpenAI fails
            return {
                'keyword_matches': [],
                'missing_keywords': [],
                'optimization_suggestions': [f'Error in AI analysis: {str(e)}'],
                'error': str(e)
            }
    
    def enhance_language(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance resume language for better impact and readability
        
        Args:
            resume_data: Parsed resume data
            
        Returns:
            Dictionary with enhanced content suggestions
        """
        try:
            resume_text = self._extract_resume_text(resume_data)
            
            prompt = f"""
            Enhance the language in this resume for better impact and professional presentation.
            
            Resume:
            {resume_text}
            
            Return a JSON response with:
            - enhanced_summary: improved professional summary
            - enhanced_skills: array of better-phrased skills
            - enhanced_experience: array of improved job descriptions with stronger action words
            - language_improvements: array of specific language enhancement suggestions
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert resume writer. Focus on strong action words and quantifiable achievements. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4
            )
            
            # Handle both mock (dict) and real OpenAI response (object) formats
            if isinstance(response, dict):
                content = response['choices'][0]['message']['content']
            else:
                content = response.choices[0].message.content
                
            result = json.loads(content)
            return result
            
        except Exception as e:
            return {
                'enhanced_summary': '',
                'enhanced_skills': [],
                'enhanced_experience': [],
                'language_improvements': [f'Error in language enhancement: {str(e)}'],
                'error': str(e)
            }
    
    def optimize_for_ats(self, resume_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Optimize resume for Applicant Tracking Systems (ATS)
        
        Args:
            resume_data: Parsed resume data
            job_description: Target job description text
            
        Returns:
            Dictionary with ATS optimization suggestions
        """
        try:
            resume_text = self._extract_resume_text(resume_data)
            
            prompt = f"""
            Analyze this resume for ATS (Applicant Tracking System) optimization against the job description.
            
            Resume:
            {resume_text}
            
            Job Description:
            {job_description}
            
            Return a JSON response with:
            - ats_score: numerical score from 0-100 for ATS compatibility
            - formatting_issues: array of formatting problems that might hurt ATS parsing
            - keyword_density: object with key skills and their frequency in resume
            - optimization_tips: array of specific tips to improve ATS performance
            - section_recommendations: array of recommended section improvements
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an ATS optimization expert. Focus on formatting, keywords, and parsing compatibility. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Handle both mock (dict) and real OpenAI response (object) formats
            if isinstance(response, dict):
                content = response['choices'][0]['message']['content']
            else:
                content = response.choices[0].message.content
                
            result = json.loads(content)
            return result
            
        except Exception as e:
            return {
                'ats_score': 0,
                'formatting_issues': [],
                'keyword_density': {},
                'optimization_tips': [f'Error in ATS analysis: {str(e)}'],
                'section_recommendations': [],
                'error': str(e)
            }
    
    def _extract_resume_text(self, resume_data: Dict[str, Any]) -> str:
        """
        Extract text content from parsed resume data
        
        Args:
            resume_data: Parsed resume data structure
            
        Returns:
            String representation of resume content
        """
        text_parts = []
        
        # Extract personal information
        personal_info = resume_data.get('personal_info', {})
        if personal_info:
            text_parts.append(f"Name: {personal_info.get('name', '')}")
            text_parts.append(f"Email: {personal_info.get('email', '')}")
            text_parts.append(f"Phone: {personal_info.get('phone', '')}")
        
        # Extract summary
        summary = resume_data.get('summary', '')
        if summary:
            text_parts.append(f"Summary: {summary}")
        
        # Extract skills
        skills = resume_data.get('skills', [])
        if skills:
            text_parts.append(f"Skills: {', '.join(skills)}")
        
        # Extract experience
        experience = resume_data.get('experience', [])
        if experience:
            for exp in experience:
                text_parts.append(f"Experience: {exp.get('company', '')} - {exp.get('position', '')}")
                text_parts.append(f"Description: {exp.get('description', '')}")
        
        # Extract education
        education = resume_data.get('education', [])
        if education:
            for edu in education:
                text_parts.append(f"Education: {edu.get('institution', '')} - {edu.get('degree', '')}")
        
        return '\n'.join(text_parts)