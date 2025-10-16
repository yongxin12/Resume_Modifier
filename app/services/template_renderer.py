"""
Template Renderer Service
Handles Jinja2 template rendering for resume generation with comprehensive styling and conditional logic.
"""
import logging
from typing import Dict, Any, Optional
from jinja2 import Environment, BaseLoader, TemplateNotFound
import json

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """Service for rendering resume templates using Jinja2."""

    def __init__(self):
        """Initialize the template renderer with Jinja2 environment."""
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters for template rendering
        self.env.filters['format_date'] = self._format_date
        self.env.filters['clean_text'] = self._clean_text
        self.env.filters['format_phone'] = self._format_phone
        
    def render(self, resume_data: Dict[str, Any], template_obj: Any) -> str:
        """
        Render resume data using the provided template.
        
        Args:
            resume_data: Resume data dictionary
            template_obj: Template object containing template content and configuration
            
        Returns:
            Rendered HTML string
        """
        try:
            # Get template content from template object
            template_content = self._get_template_content(template_obj)
            
            # Create Jinja2 template
            template = self.env.from_string(template_content)
            
            # Prepare context with resume data and template config
            context = {
                'resume': resume_data,
                'config': self._get_template_config(template_obj),
                'styles': self._generate_styles(template_obj)
            }
            
            # Render template with context
            rendered_html = template.render(**context)
            
            logger.info(f"Successfully rendered template with {len(rendered_html)} characters")
            return rendered_html
            
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            # Return fallback template on error
            return self._render_fallback_template(resume_data)

    def _get_template_content(self, template_obj: Any) -> str:
        """Extract template content from template object."""
        if hasattr(template_obj, 'template_content'):
            return template_obj.template_content
        elif hasattr(template_obj, 'content'):
            return template_obj.content
        else:
            # Return default professional template
            return self._get_default_template()

    def _get_template_config(self, template_obj: Any) -> Dict[str, Any]:
        """Extract template configuration from template object."""
        if hasattr(template_obj, 'style_config'):
            if isinstance(template_obj.style_config, str):
                return json.loads(template_obj.style_config)
            return template_obj.style_config
        else:
            return self._get_default_config()

    def _generate_styles(self, template_obj: Any) -> str:
        """Generate CSS styles from template configuration."""
        config = self._get_template_config(template_obj)
        
        # Extract style configuration
        font_family = config.get('font_family', 'Arial, sans-serif')
        color_scheme = config.get('color_scheme', {})
        layout = config.get('layout', {})
        
        # Generate CSS styles
        styles = f"""
        <style>
        body {{
            font-family: {font_family};
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: {color_scheme.get('text', '#333333')};
            background-color: {color_scheme.get('background', '#ffffff')};
        }}
        
        .header {{
            background-color: {color_scheme.get('primary', '#2c3e50')};
            color: {color_scheme.get('header_text', '#ffffff')};
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .section {{
            margin-bottom: 25px;
            padding: 15px;
            border-left: 3px solid {color_scheme.get('primary', '#2c3e50')};
        }}
        
        .section-title {{
            color: {color_scheme.get('primary', '#2c3e50')};
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            text-transform: uppercase;
            border-bottom: 1px solid {color_scheme.get('secondary', '#ecf0f1')};
            padding-bottom: 5px;
        }}
        
        .work-experience, .education {{
            margin-bottom: 15px;
        }}
        
        .company-name, .institution-name {{
            font-weight: bold;
            color: {color_scheme.get('accent', '#e74c3c')};
        }}
        
        .job-title, .degree {{
            font-style: italic;
            color: {color_scheme.get('secondary_text', '#7f8c8d')};
        }}
        
        .dates {{
            font-size: 14px;
            color: {color_scheme.get('muted', '#95a5a6')};
        }}
        
        .skills {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .skill {{
            background-color: {color_scheme.get('tag_bg', '#ecf0f1')};
            color: {color_scheme.get('tag_text', '#2c3e50')};
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 14px;
        }}
        
        @media screen and (max-width: 768px) {{
            body {{ padding: 10px; }}
            .header {{ padding: 15px; }}
            .section {{ padding: 10px; }}
            .skills {{ flex-direction: column; }}
        }}
        
        @media print {{
            body {{ margin: 0; padding: 10px; }}
            .header {{ background-color: transparent !important; color: #000 !important; }}
        }}
        </style>
        """
        
        return styles

    def _get_default_template(self) -> str:
        """Return default professional resume template."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ resume.userInfo.firstName }} {{ resume.userInfo.lastName }} - Resume</title>
            {{ styles|safe }}
        </head>
        <body>
            <div class="header">
                <h1>{{ resume.userInfo.firstName }} {{ resume.userInfo.lastName }}</h1>
                {% if resume.userInfo.headLine %}
                <p>{{ resume.userInfo.headLine }}</p>
                {% endif %}
                <p>
                    {% if resume.userInfo.email %}{{ resume.userInfo.email }}{% endif %}
                    {% if resume.userInfo.phoneNumber %} | {{ resume.userInfo.phoneNumber|format_phone }}{% endif %}
                    {% if resume.userInfo.linkedInURL %} | {{ resume.userInfo.linkedInURL }}{% endif %}
                </p>
            </div>

            {% if resume.summary %}
            <div class="section">
                <div class="section-title">Professional Summary</div>
                <p>{{ resume.summary|clean_text }}</p>
            </div>
            {% endif %}

            {% if resume.workExperience %}
            <div class="section">
                <div class="section-title">Work Experience</div>
                {% for experience in resume.workExperience %}
                <div class="work-experience">
                    <div class="company-name">{{ experience.companyName }}</div>
                    <div class="job-title">{{ experience.jobTitle }}</div>
                    <div class="dates">
                        {{ experience.fromDate|format_date }} - 
                        {% if experience.isPresent %}Present{% else %}{{ experience.toDate|format_date }}{% endif %}
                        {% if experience.city %} | {{ experience.city }}{% if experience.country %}, {{ experience.country }}{% endif %}{% endif %}
                    </div>
                    {% if experience.description %}
                    <p>{{ experience.description|clean_text }}</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if resume.education %}
            <div class="section">
                <div class="section-title">Education</div>
                {% for edu in resume.education %}
                <div class="education">
                    <div class="institution-name">{{ edu.institutionName }}</div>
                    <div class="degree">{{ edu.degree }}{% if edu.fieldOfStudy %} - {{ edu.fieldOfStudy }}{% endif %}</div>
                    {% if edu.grade %}<div>{{ edu.grade }}</div>{% endif %}
                    <div class="dates">
                        {% if edu.fromDate %}{{ edu.fromDate|format_date }} - {% endif %}
                        {% if edu.isPresent %}Present{% else %}{{ edu.toDate|format_date }}{% endif %}
                        {% if edu.city %} | {{ edu.city }}{% if edu.country %}, {{ edu.country }}{% endif %}{% endif %}
                    </div>
                    {% if edu.description %}
                    <p>{{ edu.description|clean_text }}</p>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if resume.skills %}
            <div class="section">
                <div class="section-title">Skills</div>
                <div class="skills">
                    {% for skill in resume.skills %}
                    <span class="skill">{{ skill.name or skill }}</span>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            {% if resume.achievements %}
            <div class="section">
                <div class="section-title">Achievements</div>
                {% for achievement in resume.achievements %}
                <div>• {{ achievement.title or achievement }}</div>
                {% endfor %}
            </div>
            {% endif %}

            {% if resume.certifications %}
            <div class="section">
                <div class="section-title">Certifications</div>
                {% for cert in resume.certifications %}
                <div>{{ cert.name or cert }}{% if cert.issuer %} - {{ cert.issuer }}{% endif %}</div>
                {% endfor %}
            </div>
            {% endif %}
        </body>
        </html>
        """

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default template configuration."""
        return {
            "font_family": "Arial, sans-serif",
            "color_scheme": {
                "primary": "#2c3e50",
                "secondary": "#ecf0f1",
                "accent": "#e74c3c",
                "text": "#333333",
                "background": "#ffffff",
                "header_text": "#ffffff",
                "secondary_text": "#7f8c8d",
                "muted": "#95a5a6",
                "tag_bg": "#ecf0f1",
                "tag_text": "#2c3e50"
            },
            "layout": {
                "margin": "20px",
                "section_spacing": "25px"
            }
        }

    def _render_fallback_template(self, resume_data: Dict[str, Any]) -> str:
        """Render a simple fallback template when main rendering fails."""
        user_info = resume_data.get('userInfo', {})
        
        return f"""
        <html>
        <head>
            <title>Resume - {user_info.get('firstName', '')} {user_info.get('lastName', '')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .section {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>{user_info.get('firstName', '')} {user_info.get('lastName', '')}</h1>
            <div class="section">
                <strong>Email:</strong> {user_info.get('email', 'N/A')}<br>
                <strong>Phone:</strong> {user_info.get('phoneNumber', 'N/A')}
            </div>
            <div class="section">
                <h2>Resume</h2>
                <p>Resume content could not be fully rendered. Please try again.</p>
            </div>
        </body>
        </html>
        """

    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        if not date_str:
            return ""
        
        try:
            # Handle YYYY-MM format
            if len(date_str) == 7 and '-' in date_str:
                year, month = date_str.split('-')
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                return f"{months[int(month)-1]} {year}"
            # Handle YYYY-MM-DD format
            elif len(date_str) == 10 and date_str.count('-') == 2:
                year, month, day = date_str.split('-')
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                return f"{months[int(month)-1]} {year}"
            else:
                return date_str
        except (ValueError, IndexError):
            return date_str

    def _clean_text(self, text: str) -> str:
        """Clean and format text content."""
        if not text:
            return ""
        
        # Replace bullet points with HTML entities
        text = text.replace('•', '&bull;')
        text = text.replace('\n', '<br>')
        
        return text

    def _format_phone(self, phone: str) -> str:
        """Format phone number for display."""
        if not phone:
            return ""
        
        # Remove non-numeric characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Format US phone numbers
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone