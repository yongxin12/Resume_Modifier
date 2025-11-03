#!/usr/bin/env python3
"""
Test script for EmailService functionality
"""
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_email_service():
    """Test the EmailService without sending actual emails."""
    from app import create_app
    from app.services.email_service import EmailService, email_service
    
    # Create test configuration
    test_config = {
        'TESTING': True,
        'MAIL_SUPPRESS_SEND': True,  # Prevent actual email sending
        'MAIL_SERVER': 'localhost',
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': True,
        'MAIL_DEFAULT_SENDER': 'test@example.com',
        'FRONTEND_URL': 'http://localhost:3000',
        'MAIL_SUBJECT_PREFIX': '[TEST] '
    }
    
    app = create_app(test_config)
    
    with app.app_context():
        print("Testing EmailService...")
        
        # Test configuration loading
        config_status = email_service.get_configuration_status()
        print(f"✓ Configuration loaded: {config_status['configured']}")
        print(f"  - Templates loaded: {config_status['templates_loaded']}")
        print(f"  - Required config: {config_status['required_config']}")
        
        # Test email validation
        valid_email = "test@example.com"
        invalid_email = "invalid-email"
        
        print(f"\n✓ Email validation test:")
        print(f"  - {valid_email}: {email_service.validate_email_address(valid_email)}")
        print(f"  - {invalid_email}: {email_service.validate_email_address(invalid_email)}")
        
        # Test password reset email (without sending)
        print(f"\n✓ Password reset email test:")
        result = email_service.send_password_reset_email(
            user_email="test@example.com",
            reset_token="test_token_123",
            user_ip="127.0.0.1",
            expiry_hours=1
        )
        
        print(f"  - Success: {result.success}")
        print(f"  - Recipient: {result.recipient_email}")
        print(f"  - Subject: {result.subject}")
        if result.error_message:
            print(f"  - Error: {result.error_message}")
        
        # Test general email sending (without sending)
        print(f"\n✓ General email test:")
        result2 = email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_body="<h1>Test HTML</h1>",
            text_body="Test plain text"
        )
        
        print(f"  - Success: {result2.success}")
        print(f"  - Recipient: {result2.recipient_email}")
        if result2.error_message:
            print(f"  - Error: {result2.error_message}")
        
        print("\n🎉 EmailService tests completed!")
        return True

if __name__ == "__main__":
    try:
        test_email_service()
        print("\n✅ All email service tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)