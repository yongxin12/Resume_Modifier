"""
Comprehensive test suite for password reset functionality
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from app.extensions import db
from app.models.temp import User, PasswordResetToken
from app.services.password_reset_service import password_reset_service
from app.services.email_service import email_service


class TestPasswordResetRequest:
    """Test suite for password reset request functionality"""

    def test_password_reset_request_valid_email(self, client, sample_user):
        """Test password reset request with valid email"""
        with patch.object(email_service, 'send_password_reset_email') as mock_email:
            mock_email.return_value.success = True
            mock_email.return_value.error_message = None
            
            response = client.post('/api/auth/password-reset/request', 
                                 json={'email': 'test@test.com'},
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'If an account with this email exists' in data['message']
            
            # Verify token was created
            token = PasswordResetToken.query.filter_by(user_id=sample_user.id).first()
            assert token is not None
            assert token.is_valid()
            
            # Verify email was called
            mock_email.assert_called_once()

    def test_password_reset_request_nonexistent_email(self, client):
        """Test password reset request with non-existent email"""
        response = client.post('/api/auth/password-reset/request', 
                             json={'email': 'nonexistent@test.com'},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'If an account with this email exists' in data['message']
        
        # Verify no token was created
        token = PasswordResetToken.query.first()
        assert token is None

    def test_password_reset_request_missing_email(self, client):
        """Test password reset request without email"""
        response = client.post('/api/auth/password-reset/request', 
                             json={},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Email is required' in data['message']

    def test_password_reset_request_empty_email(self, client):
        """Test password reset request with empty email"""
        response = client.post('/api/auth/password-reset/request', 
                             json={'email': ''},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Email is required' in data['message']

    def test_password_reset_request_rate_limiting(self, client, sample_user):
        """Test rate limiting for password reset requests"""
        with patch.object(email_service, 'send_password_reset_email') as mock_email:
            mock_email.return_value.success = True
            
            # Make maximum allowed requests
            for i in range(5):  # Assuming 5 is the limit per hour
                response = client.post('/api/auth/password-reset/request', 
                                     json={'email': 'test@test.com'},
                                     content_type='application/json')
                assert response.status_code == 200
            
            # Next request should be rate limited
            response = client.post('/api/auth/password-reset/request', 
                                 json={'email': 'test@test.com'},
                                 content_type='application/json')
            
            assert response.status_code == 429
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'Too many password reset requests' in data['message']

    def test_password_reset_request_email_failure(self, client, sample_user):
        """Test password reset request when email sending fails"""
        with patch.object(email_service, 'send_password_reset_email') as mock_email:
            mock_email.return_value.success = False
            mock_email.return_value.error_message = "SMTP server error"
            
            response = client.post('/api/auth/password-reset/request', 
                                 json={'email': 'test@test.com'},
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'Failed to send password reset email' in data['message']

    def test_password_reset_request_case_insensitive_email(self, client, sample_user):
        """Test password reset request with different case email"""
        with patch.object(email_service, 'send_password_reset_email') as mock_email:
            mock_email.return_value.success = True
            
            response = client.post('/api/auth/password-reset/request', 
                                 json={'email': 'TEST@TEST.COM'},
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            
            # Verify token was created for the user
            token = PasswordResetToken.query.filter_by(user_id=sample_user.id).first()
            assert token is not None

    def test_password_reset_request_revokes_old_tokens(self, client, sample_user):
        """Test that new password reset request revokes old tokens"""
        # Create an existing token
        old_token_instance, old_raw_token = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        db.session.add(old_token_instance)
        db.session.commit()
        
        assert old_token_instance.is_valid()
        
        with patch.object(email_service, 'send_password_reset_email') as mock_email:
            mock_email.return_value.success = True
            
            response = client.post('/api/auth/password-reset/request', 
                                 json={'email': 'test@test.com'},
                                 content_type='application/json')
            
            assert response.status_code == 200
            
            # Check that old token is now revoked
            db.session.refresh(old_token_instance)
            assert old_token_instance.is_used


class TestPasswordResetValidation:
    """Test suite for password reset token validation"""

    def test_validate_valid_token(self, client, sample_user):
        """Test validating a valid token"""
        # Create a valid token
        token_instance, raw_token = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        db.session.add(token_instance)
        db.session.commit()
        
        response = client.get(f'/api/auth/password-reset/validate?token={raw_token}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['valid'] == True
        assert 'Token is valid' in data['message']
        assert 'expires_at' in data

    def test_validate_invalid_token(self, client):
        """Test validating an invalid token"""
        response = client.get('/api/auth/password-reset/validate?token=invalid_token')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['valid'] == False
        assert 'Invalid or expired token' in data['message']

    def test_validate_expired_token(self, client, sample_user):
        """Test validating an expired token"""
        # Create an expired token
        token_instance, raw_token = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        # Make it expired
        token_instance.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.session.add(token_instance)
        db.session.commit()
        
        response = client.get(f'/api/auth/password-reset/validate?token={raw_token}')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['valid'] == False

    def test_validate_used_token(self, client, sample_user):
        """Test validating a used token"""
        # Create and use a token
        token_instance, raw_token = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        token_instance.mark_used()
        db.session.add(token_instance)
        db.session.commit()
        
        response = client.get(f'/api/auth/password-reset/validate?token={raw_token}')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['valid'] == False

    def test_validate_missing_token(self, client):
        """Test validation without token parameter"""
        response = client.get('/api/auth/password-reset/validate')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['valid'] == False
        assert 'Token parameter is required' in data['message']


class TestPasswordResetVerification:
    """Test suite for password reset verification (password change)"""

    def test_reset_password_success(self, client, sample_user):
        """Test successful password reset"""
        # Create a valid token
        token_instance, raw_token = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        db.session.add(token_instance)
        db.session.commit()
        
        original_password_hash = sample_user.password
        
        response = client.post('/api/auth/password-reset/verify',
                             json={
                                 'token': raw_token,
                                 'password': 'newpassword123'
                             },
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'Password has been reset successfully' in data['message']
        
        # Verify password was changed
        db.session.refresh(sample_user)
        assert sample_user.password != original_password_hash
        assert sample_user.check_password('newpassword123')
        
        # Verify token was marked as used
        db.session.refresh(token_instance)
        assert token_instance.is_used

    def test_reset_password_invalid_token(self, client):
        """Test password reset with invalid token"""
        response = client.post('/api/auth/password-reset/verify',
                             json={
                                 'token': 'invalid_token',
                                 'password': 'newpassword123'
                             },
                             content_type='application/json')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid or expired token' in data['message']

    def test_reset_password_weak_password(self, client, sample_user):
        """Test password reset with weak password"""
        token_instance, raw_token = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        db.session.add(token_instance)
        db.session.commit()
        
        response = client.post('/api/auth/password-reset/verify',
                             json={
                                 'token': raw_token,
                                 'password': '123'  # Too short
                             },
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Password must be at least 8 characters long' in data['message']

    def test_reset_password_missing_fields(self, client):
        """Test password reset with missing fields"""
        response = client.post('/api/auth/password-reset/verify',
                             json={},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Token and password are required' in data['message']

    def test_reset_password_missing_token(self, client):
        """Test password reset with missing token"""
        response = client.post('/api/auth/password-reset/verify',
                             json={'password': 'newpassword123'},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Token and password are required' in data['message']

    def test_reset_password_missing_password(self, client, sample_user):
        """Test password reset with missing password"""
        token_instance, raw_token = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        db.session.add(token_instance)
        db.session.commit()
        
        response = client.post('/api/auth/password-reset/verify',
                             json={'token': raw_token},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Token and password are required' in data['message']

    def test_reset_password_revokes_all_user_tokens(self, client, sample_user):
        """Test that password reset revokes all user tokens"""
        # Create multiple tokens for the user
        token1_instance, raw_token1 = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        token2_instance, raw_token2 = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='192.168.1.1'
        )
        db.session.add_all([token1_instance, token2_instance])
        db.session.commit()
        
        # Use first token to reset password
        response = client.post('/api/auth/password-reset/verify',
                             json={
                                 'token': raw_token1,
                                 'password': 'newpassword123'
                             },
                             content_type='application/json')
        
        assert response.status_code == 200
        
        # Verify both tokens are now used/revoked
        db.session.refresh(token1_instance)
        db.session.refresh(token2_instance)
        assert token1_instance.is_used
        assert token2_instance.is_used

    def test_reset_password_token_consumed_once(self, client, sample_user):
        """Test that token can only be used once"""
        token_instance, raw_token = PasswordResetToken.create_token(
            user_id=sample_user.id,
            ip_address='127.0.0.1'
        )
        db.session.add(token_instance)
        db.session.commit()
        
        # First reset should succeed
        response1 = client.post('/api/auth/password-reset/verify',
                              json={
                                  'token': raw_token,
                                  'password': 'newpassword123'
                              },
                              content_type='application/json')
        
        assert response1.status_code == 200
        
        # Second reset with same token should fail
        response2 = client.post('/api/auth/password-reset/verify',
                              json={
                                  'token': raw_token,
                                  'password': 'anotherpassword123'
                              },
                              content_type='application/json')
        
        assert response2.status_code == 401
        data = json.loads(response2.data)
        assert data['status'] == 'error'
        assert 'Invalid or expired token' in data['message']


class TestPasswordResetIntegration:
    """Integration tests for complete password reset workflow"""

    def test_complete_password_reset_workflow(self, client, sample_user):
        """Test complete password reset workflow from request to reset"""
        original_password = 'password123'
        new_password = 'newpassword456'
        
        # Step 1: Request password reset
        with patch.object(email_service, 'send_password_reset_email') as mock_email:
            mock_email.return_value.success = True
            
            response = client.post('/api/auth/password-reset/request', 
                                 json={'email': 'test@test.com'},
                                 content_type='application/json')
            
            assert response.status_code == 200
        
        # Step 2: Get the token that was created
        token = PasswordResetToken.query.filter_by(user_id=sample_user.id).first()
        assert token is not None
        
        # Generate raw token for testing (normally this comes from email)
        raw_token = PasswordResetToken.generate_token()
        token_hash = PasswordResetToken.hash_token(raw_token)
        token.token_hash = token_hash
        db.session.commit()
        
        # Step 3: Validate the token
        response = client.get(f'/api/auth/password-reset/validate?token={raw_token}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['valid'] == True
        
        # Step 4: Reset the password
        response = client.post('/api/auth/password-reset/verify',
                             json={
                                 'token': raw_token,
                                 'password': new_password
                             },
                             content_type='application/json')
        
        assert response.status_code == 200
        
        # Step 5: Verify user can login with new password
        response = client.post('/api/login',
                             json={
                                 'email': 'test@test.com',
                                 'password': new_password
                             },
                             content_type='application/json')
        
        assert response.status_code == 200
        
        # Step 6: Verify user cannot login with old password
        response = client.post('/api/login',
                             json={
                                 'email': 'test@test.com',
                                 'password': original_password
                             },
                             content_type='application/json')
        
        assert response.status_code == 401

    def test_password_reset_security_logging(self, client, sample_user):
        """Test that security-relevant information is logged"""
        with patch.object(email_service, 'send_password_reset_email') as mock_email:
            mock_email.return_value.success = True
            
            # Make request with specific headers
            response = client.post('/api/auth/password-reset/request', 
                                 json={'email': 'test@test.com'},
                                 content_type='application/json',
                                 headers={'User-Agent': 'TestAgent/1.0'})
            
            assert response.status_code == 200
            
            # Verify token includes security metadata
            token = PasswordResetToken.query.filter_by(user_id=sample_user.id).first()
            assert token is not None
            assert token.ip_address is not None  # Should capture IP
            assert token.user_agent == 'TestAgent/1.0'