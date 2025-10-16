"""
Template management service for resume templates
"""

from typing import Dict, List, Any, Optional
from app.models.temp import ResumeTemplate
from app.extensions import db
from datetime import datetime


class TemplateService:
    """Service class for managing resume templates"""
    
    @staticmethod
    def get_all_templates() -> List[Dict[str, Any]]:
        """
        Get all active resume templates
        
        Returns:
            List of template dictionaries with metadata
        """
        templates = ResumeTemplate.query.filter_by(is_active=True).all()
        
        return [
            {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "style_config": template.style_config,
                "sections": template.sections,
                "created_at": template.created_at.isoformat()
            }
            for template in templates
        ]
    
    @staticmethod
    def get_template_by_id(template_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by ID
        
        Args:
            template_id: The template ID to retrieve
            
        Returns:
            Template dictionary or None if not found
        """
        template = ResumeTemplate.query.filter_by(id=template_id, is_active=True).first()
        
        if not template:
            return None
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "style_config": template.style_config,
            "sections": template.sections,
            "created_at": template.created_at.isoformat()
        }
    
    @staticmethod
    def create_template(name: str, description: str, style_config: Dict, sections: List[str]) -> Dict[str, Any]:
        """
        Create a new resume template
        
        Args:
            name: Template name
            description: Template description
            style_config: Style configuration dictionary
            sections: List of section names
            
        Returns:
            Created template dictionary
            
        Raises:
            Exception: If template creation fails
        """
        template = ResumeTemplate(
            name=name,
            description=description,
            style_config=style_config,
            sections=sections,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            db.session.add(template)
            db.session.commit()
            
            return {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "style_config": template.style_config,
                "sections": template.sections,
                "created_at": template.created_at.isoformat()
            }
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create template: {str(e)}")
    
    @staticmethod
    def update_template(template_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Update an existing template
        
        Args:
            template_id: Template ID to update
            **kwargs: Fields to update
            
        Returns:
            Updated template dictionary or None if not found
        """
        template = ResumeTemplate.query.filter_by(id=template_id, is_active=True).first()
        
        if not template:
            return None
        
        # Update allowed fields
        allowed_fields = ['name', 'description', 'style_config', 'sections']
        for field in allowed_fields:
            if field in kwargs:
                setattr(template, field, kwargs[field])
        
        template.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            return {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "style_config": template.style_config,
                "sections": template.sections,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to update template: {str(e)}")
    
    @staticmethod
    def delete_template(template_id: int) -> bool:
        """
        Soft delete a template (mark as inactive)
        
        Args:
            template_id: Template ID to delete
            
        Returns:
            True if successful, False if template not found
        """
        template = ResumeTemplate.query.filter_by(id=template_id, is_active=True).first()
        
        if not template:
            return False
        
        template.is_active = False
        template.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to delete template: {str(e)}")
    
    @staticmethod
    def seed_default_templates() -> None:
        """
        Seed the database with default resume templates
        """
        default_templates = [
            {
                "name": "Professional Modern",
                "description": "Clean, modern design with blue accents suitable for corporate environments",
                "style_config": {
                    "font_family": "Arial",
                    "header_font_size": 16,
                    "body_font_size": 11,
                    "line_spacing": 1.2,
                    "color_scheme": {
                        "primary": "#2E86AB",
                        "secondary": "#A23B72",
                        "text": "#333333",
                        "accent": "#F18F01"
                    },
                    "margins": {
                        "top": 0.8,
                        "bottom": 0.8,
                        "left": 0.8,
                        "right": 0.8
                    }
                },
                "sections": ["header", "summary", "experience", "education", "skills", "certifications"]
            },
            {
                "name": "Creative Designer",
                "description": "Eye-catching design with creative elements, perfect for design and creative roles",
                "style_config": {
                    "font_family": "Calibri",
                    "header_font_size": 18,
                    "body_font_size": 11,
                    "line_spacing": 1.3,
                    "color_scheme": {
                        "primary": "#E74C3C",
                        "secondary": "#9B59B6",
                        "text": "#2C3E50",
                        "accent": "#F39C12"
                    },
                    "margins": {
                        "top": 0.7,
                        "bottom": 0.7,
                        "left": 0.9,
                        "right": 0.9
                    }
                },
                "sections": ["header", "summary", "portfolio", "experience", "education", "skills", "projects"]
            },
            {
                "name": "Executive Classic",
                "description": "Sophisticated and traditional design for senior-level positions",
                "style_config": {
                    "font_family": "Times New Roman",
                    "header_font_size": 14,
                    "body_font_size": 10,
                    "line_spacing": 1.1,
                    "color_scheme": {
                        "primary": "#1B4332",
                        "secondary": "#2D6A4F",
                        "text": "#000000",
                        "accent": "#B7E4C7"
                    },
                    "margins": {
                        "top": 1.0,
                        "bottom": 1.0,
                        "left": 1.0,
                        "right": 1.0
                    }
                },
                "sections": ["header", "executive_summary", "experience", "education", "board_positions", "achievements"]
            }
        ]
        
        for template_data in default_templates:
            # Check if template already exists
            existing = ResumeTemplate.query.filter_by(name=template_data["name"]).first()
            if not existing:
                template = ResumeTemplate(
                    name=template_data["name"],
                    description=template_data["description"],
                    style_config=template_data["style_config"],
                    sections=template_data["sections"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(template)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to seed templates: {str(e)}")