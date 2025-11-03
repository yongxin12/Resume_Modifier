"""
Email Service for handling SMTP email operations
Supports password reset emails and other transactional emails

Author: Resume Modifier Backend Team
Date: November 2024
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from flask import Flask, current_app, render_template_string
from flask_mail import Mail, Message
import smtplib
from email_validator import validate_email, EmailNotValidError


class EmailError(Exception):
    """Custom exception for email-related errors"""
    pass


@dataclass
class EmailResult:
    """Result object for email operations"""
    success: bool
    message_id: Optional[str] = None
    recipient_email: Optional[str] = None
    subject: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None


class EmailService:
    """
    Service for handling email operations using Flask-Mail.
    Supports SMTP configuration, email validation, and template rendering.
    """

    def __init__(self, app: Optional[Flask] = None):
        """
        Initialize EmailService with optional Flask app.
        
        Args:
            app: Flask application instance
        """
        self.mail = Mail()
        self.logger = logging.getLogger(__name__)
        self._templates = {}
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """
        Initialize the service with Flask app configuration.
        
        Args:
            app: Flask application instance
        """
        self.mail.init_app(app)
        self.app = app
        
        # Load configuration with defaults
        self._load_config(app)
        
        # Initialize email templates
        self._load_templates()
        
        self.logger.info("EmailService initialized successfully")

    def _load_config(self, app: Flask) -> None:
        """
        Load email configuration from Flask app config.
        
        Args:
            app: Flask application instance
        """
        # SMTP Configuration
        app.config.setdefault('MAIL_SERVER', os.getenv('SMTP_SERVER', 'localhost'))
        app.config.setdefault('MAIL_PORT', int(os.getenv('SMTP_PORT', '587')))
        app.config.setdefault('MAIL_USE_TLS', os.getenv('SMTP_USE_TLS', 'true').lower() == 'true')
        app.config.setdefault('MAIL_USE_SSL', os.getenv('SMTP_USE_SSL', 'false').lower() == 'true')
        app.config.setdefault('MAIL_USERNAME', os.getenv('SMTP_USERNAME'))
        app.config.setdefault('MAIL_PASSWORD', os.getenv('SMTP_PASSWORD'))
        app.config.setdefault('MAIL_DEFAULT_SENDER', os.getenv('SMTP_FROM_EMAIL', 'noreply@example.com'))
        
        # Email Configuration
        app.config.setdefault('MAIL_SUBJECT_PREFIX', os.getenv('MAIL_SUBJECT_PREFIX', '[Resume Modifier] '))
        app.config.setdefault('MAIL_SUPPRESS_SEND', os.getenv('MAIL_SUPPRESS_SEND', 'false').lower() == 'true')
        app.config.setdefault('MAIL_DEBUG', app.debug)
        
        # Password Reset Configuration
        app.config.setdefault('FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:3000'))

    def _load_templates(self) -> None:
        """Load email templates."""
        self._templates = {
            'password_reset': {
                'subject': 'Password Reset Request',
                'html_template': """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset Request</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #f8f9fa; padding: 20px; text-align: center; border-radius: 5px; }
        .content { padding: 20px 0; }
        .button { display: inline-block; padding: 12px 24px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { font-size: 12px; color: #666; text-align: center; margin-top: 30px; }
        .warning { background: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello {{ user_email }},</p>
            
            <p>We received a request to reset your password for your Resume Modifier account. If you made this request, click the button below to reset your password:</p>
            
            <div style="text-align: center;">
                <a href="{{ reset_link }}" class="button">Reset Password</a>
            </div>
            
            <p>Alternatively, you can copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 3px;">{{ reset_link }}</p>
            
            <div class="warning">
                <strong>Security Notice:</strong>
                <ul>
                    <li>This link will expire in {{ expiry_hours }} hour(s)</li>
                    <li>If you didn't request this password reset, please ignore this email</li>
                    <li>For security, this link can only be used once</li>
                </ul>
            </div>
            
            <p>If you continue to have problems, please contact our support team.</p>
        </div>
        <div class="footer">
            <p>This email was sent from {{ request_ip }} at {{ timestamp }}.</p>
            <p>© 2024 Resume Modifier. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
                """,
                'text_template': """
Password Reset Request

Hello {{ user_email }},

We received a request to reset your password for your Resume Modifier account.

Reset your password by visiting this link:
{{ reset_link }}

Security Notice:
- This link will expire in {{ expiry_hours }} hour(s)
- If you didn't request this password reset, please ignore this email
- For security, this link can only be used once

This email was sent from {{ request_ip }} at {{ timestamp }}.

© 2024 Resume Modifier. All rights reserved.
                """
            }
        }

    def validate_email_address(self, email: str, check_deliverability: bool = False) -> bool:
        """
        Validate email address format and optionally deliverability.
        
        Args:
            email: Email address to validate
            check_deliverability: Whether to check if domain accepts email (default: False)
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        try:
            # Validate email format and optionally check deliverability
            valid = validate_email(email, check_deliverability=check_deliverability)
            return True
        except EmailNotValidError as e:
            self.logger.warning(f"Invalid email address {email}: {e}")
            return False

    def send_email(
        self,
        to_email: Union[str, List[str]],
        subject: str,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> EmailResult:
        """
        Send an email using Flask-Mail.
        
        Args:
            to_email: Recipient email address(es)
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body
            from_email: Sender email address (optional)
            reply_to: Reply-to email address (optional)
            attachments: List of attachments (optional)
            
        Returns:
            EmailResult: Result of the email operation
        """
        try:
            # Ensure we have a current app context
            if not current_app:
                raise EmailError("No Flask application context available")

            # Validate recipient email(s)
            recipients = [to_email] if isinstance(to_email, str) else to_email
            for email in recipients:
                if not self.validate_email_address(email, check_deliverability=False):
                    raise EmailError(f"Invalid recipient email: {email}")

            # Create message
            message = Message(
                subject=current_app.config.get('MAIL_SUBJECT_PREFIX', '') + subject,
                recipients=recipients,
                sender=from_email or current_app.config['MAIL_DEFAULT_SENDER'],
                reply_to=reply_to
            )

            # Set message body
            if html_body:
                message.html = html_body
            if text_body:
                message.body = text_body

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    message.attach(
                        attachment.get('filename', 'attachment'),
                        attachment.get('content_type', 'application/octet-stream'),
                        attachment.get('data', b'')
                    )

            # Send email
            self.mail.send(message)

            result = EmailResult(
                success=True,
                recipient_email=recipients[0],
                subject=subject,
                sent_at=datetime.utcnow()
            )

            self.logger.info(f"Email sent successfully to {recipients}")
            return result

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                recipient_email=recipients[0] if 'recipients' in locals() else to_email,
                subject=subject,
                error_message=error_msg
            )

    def send_password_reset_email(
        self,
        user_email: str,
        reset_token: str,
        user_ip: str = None,
        expiry_hours: int = 1
    ) -> EmailResult:
        """
        Send password reset email using predefined template.
        
        Args:
            user_email: User's email address
            reset_token: Password reset token
            user_ip: IP address of the request (for security logging)
            expiry_hours: Hours until token expires
            
        Returns:
            EmailResult: Result of the email operation
        """
        try:
            # Get template
            template = self._templates['password_reset']
            
            # Build reset link
            frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"
            
            # Template variables
            template_vars = {
                'user_email': user_email,
                'reset_link': reset_link,
                'reset_token': reset_token,
                'expiry_hours': expiry_hours,
                'request_ip': user_ip or 'Unknown',
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            # Render templates
            html_body = render_template_string(template['html_template'], **template_vars)
            text_body = render_template_string(template['text_template'], **template_vars)
            
            # Send email
            return self.send_email(
                to_email=user_email,
                subject=template['subject'],
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            error_msg = f"Failed to send password reset email: {str(e)}"
            self.logger.error(error_msg)
            return EmailResult(
                success=False,
                recipient_email=user_email,
                subject='Password Reset Request',
                error_message=error_msg
            )

    def test_smtp_connection(self) -> Dict[str, Any]:
        """
        Test SMTP connection and configuration.
        
        Returns:
            Dict: Test result with connection status and details
        """
        try:
            if not current_app:
                return {
                    'success': False,
                    'error': 'No Flask application context available'
                }

            config = current_app.config
            
            # Test SMTP connection
            if config.get('MAIL_USE_SSL'):
                server = smtplib.SMTP_SSL(config['MAIL_SERVER'], config['MAIL_PORT'])
            else:
                server = smtplib.SMTP(config['MAIL_SERVER'], config['MAIL_PORT'])
                if config.get('MAIL_USE_TLS'):
                    server.starttls()

            if config.get('MAIL_USERNAME') and config.get('MAIL_PASSWORD'):
                server.login(config['MAIL_USERNAME'], config['MAIL_PASSWORD'])

            server.quit()

            return {
                'success': True,
                'message': 'SMTP connection successful',
                'server': config['MAIL_SERVER'],
                'port': config['MAIL_PORT'],
                'use_tls': config.get('MAIL_USE_TLS', False),
                'use_ssl': config.get('MAIL_USE_SSL', False)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'SMTP connection failed: {str(e)}'
            }

    def get_configuration_status(self) -> Dict[str, Any]:
        """
        Get email service configuration status.
        
        Returns:
            Dict: Configuration status and details
        """
        if not current_app:
            return {'configured': False, 'error': 'No Flask application context'}

        config = current_app.config
        
        required_config = {
            'MAIL_SERVER': config.get('MAIL_SERVER'),
            'MAIL_PORT': config.get('MAIL_PORT'),
            'MAIL_DEFAULT_SENDER': config.get('MAIL_DEFAULT_SENDER')
        }
        
        optional_config = {
            'MAIL_USERNAME': config.get('MAIL_USERNAME'),
            'MAIL_PASSWORD': '***' if config.get('MAIL_PASSWORD') else None,
            'MAIL_USE_TLS': config.get('MAIL_USE_TLS'),
            'MAIL_USE_SSL': config.get('MAIL_USE_SSL'),
            'FRONTEND_URL': config.get('FRONTEND_URL')
        }
        
        # Check if required configuration is present
        missing_required = [key for key, value in required_config.items() if not value]
        
        return {
            'configured': len(missing_required) == 0,
            'required_config': required_config,
            'optional_config': optional_config,
            'missing_required': missing_required,
            'templates_loaded': len(self._templates)
        }


# Global instance
email_service = EmailService()