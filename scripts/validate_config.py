#!/usr/bin/env python3
"""
Environment Configuration Validation Script

This script validates the environment configuration for the Resume Editor application,
with special focus on password recovery functionality.

Usage:
    python scripts/validate_config.py
    python scripts/validate_config.py --email test@example.com
    python scripts/validate_config.py --component email
    python scripts/validate_config.py --component database
"""

import os
import sys
import argparse
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.extensions import db
    from app.services.email_service import EmailService
    from app.services.password_reset_service import PasswordResetService
    from app.models.temp import User, PasswordResetToken
    from app import create_app
except ImportError as e:
    print(f"❌ Failed to import application modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

class ConfigValidator:
    """Validates environment configuration for the Resume Editor app."""
    
    def __init__(self):
        self.app = None
        self.results = []
        self.warnings = []
        self.errors = []
        
    def check_required_env_vars(self) -> bool:
        """Check if all required environment variables are set."""
        print("🔍 Checking required environment variables...")
        
        required_vars = [
            'OPENAI_API_KEY',
            'DATABASE_URL', 
            'JWT_SECRET'
        ]
        
        email_vars = [
            'MAIL_SERVER',
            'MAIL_USERNAME', 
            'MAIL_PASSWORD'
        ]
        
        all_good = True
        
        # Check core required variables
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required environment variable: {var}")
                print(f"❌ {var}: Not set")
                all_good = False
            elif var == 'OPENAI_API_KEY' and not value.startswith('sk-'):
                self.warnings.append(f"{var} doesn't look like a valid OpenAI API key")
                print(f"⚠️  {var}: Set but format looks incorrect")
            else:
                print(f"✅ {var}: Set")
        
        # Check email configuration
        email_configured = all(os.getenv(var) for var in email_vars)
        if not email_configured:
            print("\n📧 Email configuration:")
            for var in email_vars:
                value = os.getenv(var)
                if not value:
                    print(f"❌ {var}: Not set")
                    self.errors.append(f"Missing email configuration: {var}")
                    all_good = False
                else:
                    print(f"✅ {var}: Set")
        else:
            print("✅ Email configuration: Complete")
            
        return all_good
    
    def check_database_connection(self) -> bool:
        """Test database connection."""
        print("\n🗄️  Testing database connection...")
        
        try:
            self.app = create_app()
            with self.app.app_context():
                # Test basic connection
                result = db.engine.execute(db.text('SELECT 1')).scalar()
                if result == 1:
                    print("✅ Database connection: Success")
                    
                    # Check if required tables exist
                    self.check_database_tables()
                    return True
                else:
                    self.errors.append("Database connection test failed")
                    print("❌ Database connection: Failed")
                    return False
                    
        except Exception as e:
            self.errors.append(f"Database connection error: {str(e)}")
            print(f"❌ Database connection: Error - {e}")
            return False
    
    def check_database_tables(self):
        """Check if required database tables exist."""
        print("🔍 Checking database tables...")
        
        required_tables = ['users', 'password_reset_tokens']
        
        try:
            # Check if tables exist
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            for table in required_tables:
                if table in existing_tables:
                    print(f"✅ Table '{table}': Exists")
                else:
                    self.warnings.append(f"Table '{table}' not found - run migrations")
                    print(f"⚠️  Table '{table}': Not found")
                    
            # Test model operations
            try:
                user_count = User.query.count()
                token_count = PasswordResetToken.query.count()
                print(f"✅ Database queries: Working ({user_count} users, {token_count} tokens)")
            except Exception as e:
                self.warnings.append(f"Database query test failed: {str(e)}")
                print(f"⚠️  Database queries: Failed - {e}")
                
        except Exception as e:
            self.warnings.append(f"Table inspection failed: {str(e)}")
            print(f"⚠️  Table inspection: Failed - {e}")
    
    def check_email_configuration(self, test_email: Optional[str] = None) -> bool:
        """Test email configuration."""
        print("\n📧 Testing email configuration...")
        
        if not self.app:
            try:
                self.app = create_app()
            except Exception as e:
                self.errors.append(f"Failed to create app for email testing: {e}")
                return False
        
        try:
            with self.app.app_context():
                email_service = EmailService()
                
                # Test email service initialization
                print("✅ Email service: Initialized")
                
                # Test SMTP connection
                try:
                    if hasattr(email_service, 'test_connection'):
                        email_service.test_connection()
                        print("✅ SMTP connection: Success")
                    else:
                        print("⚠️  SMTP connection: Cannot test (no test method)")
                        
                except Exception as e:
                    self.warnings.append(f"SMTP connection test failed: {str(e)}")
                    print(f"⚠️  SMTP connection: Failed - {e}")
                
                # Test email template rendering
                try:
                    # This tests template rendering without sending
                    token = "test-token-12345"
                    username = "Test User"
                    
                    if hasattr(email_service, '_render_template'):
                        html_content = email_service._render_template(
                            'password_reset.html', 
                            username=username,
                            reset_link=f"http://localhost:3000/reset-password?token={token}",
                            expiry_hours=24
                        )
                        if html_content and len(html_content) > 100:
                            print("✅ Email templates: Working")
                        else:
                            self.warnings.append("Email template rendering produced short content")
                            print("⚠️  Email templates: Rendered but content seems short")
                    else:
                        print("⚠️  Email templates: Cannot test (no render method)")
                        
                except Exception as e:
                    self.warnings.append(f"Email template test failed: {str(e)}")
                    print(f"⚠️  Email templates: Failed - {e}")
                
                # Send test email if requested
                if test_email:
                    print(f"\n📤 Sending test email to {test_email}...")
                    try:
                        result = email_service.send_password_reset_email(
                            test_email, "test-token-12345", "Test User"
                        )
                        if result.get('success'):
                            print("✅ Test email: Sent successfully")
                        else:
                            self.errors.append(f"Test email failed: {result.get('message', 'Unknown error')}")
                            print(f"❌ Test email: Failed - {result.get('message', 'Unknown error')}")
                            return False
                    except Exception as e:
                        self.errors.append(f"Test email failed: {str(e)}")
                        print(f"❌ Test email: Failed - {e}")
                        return False
                
                return True
                
        except Exception as e:
            self.errors.append(f"Email configuration test failed: {str(e)}")
            print(f"❌ Email configuration: Failed - {e}")
            return False
    
    def check_password_reset_service(self) -> bool:
        """Test password reset service functionality."""
        print("\n🔐 Testing password reset service...")
        
        if not self.app:
            try:
                self.app = create_app()
            except Exception as e:
                self.errors.append(f"Failed to create app for service testing: {e}")
                return False
        
        try:
            with self.app.app_context():
                service = PasswordResetService()
                print("✅ Password reset service: Initialized")
                
                # Test rate limiting check (without actually hitting limits)
                try:
                    # This should not raise an exception for a test email
                    rate_check = service._check_rate_limits("test@example.com", "127.0.0.1", "Test-Agent")
                    print("✅ Rate limiting: Working")
                except Exception as e:
                    self.warnings.append(f"Rate limiting test failed: {str(e)}")
                    print(f"⚠️  Rate limiting: Failed - {e}")
                
                # Test token generation (without saving to database)
                try:
                    from app.models.temp import PasswordResetToken
                    token_data = PasswordResetToken.generate_token()
                    if token_data and len(token_data) == 64:
                        print("✅ Token generation: Working")
                    else:
                        self.warnings.append("Token generation produced unexpected result")
                        print("⚠️  Token generation: Unexpected result")
                except Exception as e:
                    self.warnings.append(f"Token generation test failed: {str(e)}")
                    print(f"⚠️  Token generation: Failed - {e}")
                
                return True
                
        except Exception as e:
            self.errors.append(f"Password reset service test failed: {str(e)}")
            print(f"❌ Password reset service: Failed - {e}")
            return False
    
    def check_security_settings(self) -> bool:
        """Check security configuration."""
        print("\n🛡️  Checking security settings...")
        
        # Check password requirements
        min_length = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
        if min_length >= 8:
            print(f"✅ Password minimum length: {min_length}")
        else:
            self.warnings.append(f"Password minimum length is low: {min_length}")
            print(f"⚠️  Password minimum length: {min_length} (consider 8+)")
        
        # Check rate limiting settings
        user_limit = int(os.getenv('PASSWORD_RESET_RATE_LIMIT_USER', 5))
        ip_limit = int(os.getenv('PASSWORD_RESET_RATE_LIMIT_IP', 10))
        
        if user_limit > 0 and ip_limit > 0:
            print(f"✅ Rate limiting: {user_limit}/hour per user, {ip_limit}/hour per IP")
        else:
            self.warnings.append("Rate limiting is disabled")
            print("⚠️  Rate limiting: Disabled")
        
        # Check token expiry
        expiry_hours = int(os.getenv('PASSWORD_RESET_TOKEN_EXPIRY_HOURS', 24))
        if 1 <= expiry_hours <= 48:
            print(f"✅ Token expiry: {expiry_hours} hours")
        else:
            self.warnings.append(f"Token expiry is unusual: {expiry_hours} hours")
            print(f"⚠️  Token expiry: {expiry_hours} hours (consider 24)")
        
        # Check JWT secret strength
        jwt_secret = os.getenv('JWT_SECRET', '')
        if len(jwt_secret) >= 32:
            print("✅ JWT secret: Adequate length")
        else:
            self.warnings.append("JWT secret is short - consider longer secret")
            print("⚠️  JWT secret: Short (consider longer)")
        
        return True
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "="*60)
        print("🏁 VALIDATION SUMMARY")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("🎉 All checks passed! Your configuration looks great.")
        else:
            if self.errors:
                print(f"\n❌ ERRORS ({len(self.errors)}):")
                for i, error in enumerate(self.errors, 1):
                    print(f"   {i}. {error}")
            
            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"   {i}. {warning}")
        
        print(f"\n📊 Results:")
        print(f"   ✅ Errors: {len(self.errors)}")
        print(f"   ⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n🔧 Next steps:")
            print("   1. Fix the errors listed above")
            print("   2. Check your .env file configuration")
            print("   3. Run this script again to verify")
            print("   4. See ENVIRONMENT_CONFIG.md for detailed setup instructions")
        else:
            print("\n🚀 Your application is ready to use!")
            if self.warnings:
                print("   Consider addressing the warnings for optimal security.")

def main():
    parser = argparse.ArgumentParser(description='Validate Resume Editor environment configuration')
    parser.add_argument('--email', help='Send test email to this address')
    parser.add_argument('--component', choices=['email', 'database', 'security', 'all'], 
                       default='all', help='Test specific component only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    print("🔍 Resume Editor - Environment Configuration Validator")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    validator = ConfigValidator()
    
    # Always check environment variables first
    env_ok = validator.check_required_env_vars()
    
    if not env_ok:
        print("\n❌ Cannot proceed with tests due to missing environment variables.")
        validator.print_summary()
        sys.exit(1)
    
    # Run component-specific tests
    if args.component in ['all', 'database']:
        validator.check_database_connection()
    
    if args.component in ['all', 'email']:
        validator.check_email_configuration(args.email)
    
    if args.component in ['all']:
        validator.check_password_reset_service()
    
    if args.component in ['all', 'security']:
        validator.check_security_settings()
    
    # Print final summary
    validator.print_summary()
    
    # Exit with error code if there are errors
    if validator.errors:
        sys.exit(1)

if __name__ == '__main__':
    main()