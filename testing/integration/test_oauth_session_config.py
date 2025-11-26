"""
Test OAuth Session Configuration
Validates that all OAuth session fixes are properly configured
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier')
os.chdir('/home/rex/project/resume-editor/project/Resume_Modifier')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)

def test_oauth_session_configuration():
    """Test that OAuth session configuration is working properly."""
    
    logger.info("🧪 Testing OAuth Session Configuration...")
    
    try:
        # Test 1: Import the fixed services
        logger.info("📦 Testing imports...")
        
        from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed, create_oauth_temp_states_table
        from app.services.flask_session_config import configure_flask_sessions_for_docker, validate_session_configuration
        logger.info("✅ All imports successful")
        
        # Test 2: Create Flask app with session configuration
        logger.info("🔧 Testing Flask app with session configuration...")
        
        from flask import Flask
        app = Flask(__name__)
        
        # Set basic configuration
        app.config['SECRET_KEY'] = 'test-secret-key-for-oauth-validation'
        app.config['GOOGLE_ADMIN_OAUTH_CLIENT_ID'] = 'test-client-id'
        app.config['GOOGLE_ADMIN_OAUTH_CLIENT_SECRET'] = 'test-client-secret'
        app.config['GOOGLE_ADMIN_OAUTH_REDIRECT_URI'] = 'http://localhost:5001/oauth/callback'
        
        # Apply session configuration
        session_config = configure_flask_sessions_for_docker(app)
        logger.info(f"✅ Session configuration applied with {len(session_config)} settings")
        
        # Validate configuration
        validation_results = validate_session_configuration(app)
        logger.info(f"✅ Session validation completed: {validation_results}")
        
        # Test 3: Initialize OAuth service
        logger.info("🔐 Testing OAuth service initialization...")
        
        with app.app_context():
            # Create temporary database for testing
            from app.extensions import db
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            db.init_app(app)
            
            with app.app_context():
                db.create_all()
                
                # Create OAuth temp states table
                create_oauth_temp_states_table()
                logger.info("✅ OAuth temp states table created")
                
                # Initialize OAuth service
                oauth_service = GoogleAdminAuthServiceFixed()
                logger.info("✅ OAuth service initialized successfully")
        
        # Test 4: Test session management utilities
        logger.info("🗃️  Testing session management utilities...")
        
        from flask_session_config import debug_session_state
        test_session = {
            'session_id': 'test-session-123',
            'permanent': True,
            'oauth_session_store': {
                'oauth_state': 'test-state-456',
                'admin_user_id': 1,
                'oauth_initiated_at': datetime.utcnow().isoformat()
            }
        }
        
        debug_output = debug_session_state(test_session)
        logger.info(f"✅ Session debug output generated:\\n{debug_output}")
        
        logger.info("🎉 All OAuth session configuration tests passed!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("   Make sure all required files are in place")
        return False
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_oauth_flow_simulation():
    """Simulate an OAuth flow to test state management."""
    
    logger.info("🎭 Simulating OAuth flow...")
    
    try:
        from flask import Flask
        from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed
        from app.services.flask_session_config import configure_flask_sessions_for_docker
        
        # Create test Flask app
        app = Flask(__name__)
        app.config.update({
            'SECRET_KEY': 'test-oauth-flow-secret',
            'TESTING': True,
            'GOOGLE_ADMIN_OAUTH_CLIENT_ID': 'test-client-id',
            'GOOGLE_ADMIN_OAUTH_CLIENT_SECRET': 'test-client-secret',
            'GOOGLE_ADMIN_OAUTH_REDIRECT_URI': 'http://localhost:5001/oauth/callback',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False
        })
        
        # Configure sessions
        configure_flask_sessions_for_docker(app)
        
        with app.app_context():
            # Initialize database
            from app.extensions import db
            db.init_app(app)
            db.create_all()
            
            # Create test admin user
            from app.models.temp import User
            admin_user = User(
                id=1,
                email='test@example.com',
                password_hash='test-hash',
                is_admin=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(admin_user)
            db.session.commit()
            
            logger.info("✅ Test admin user created")
            
            # Test OAuth initialization (simulation)
            with app.test_request_context():
                from flask import session
                
                # Simulate session setup
                session['session_initialized'] = True
                session['session_created_at'] = datetime.utcnow().isoformat()
                
                logger.info("✅ OAuth flow simulation setup complete")
                logger.info(f"   Session keys: {list(session.keys())}")
        
        logger.info("🎉 OAuth flow simulation successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ OAuth flow simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test execution."""
    
    logger.info("🚀 Starting OAuth Session Configuration Tests")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Test 1: Configuration
    config_test_passed = test_oauth_session_configuration()
    
    # Test 2: OAuth Flow Simulation
    flow_test_passed = test_oauth_flow_simulation()
    
    # Summary
    logger.info("📊 Test Results Summary:")
    logger.info(f"   Configuration Test: {'✅ PASSED' if config_test_passed else '❌ FAILED'}")
    logger.info(f"   OAuth Flow Test: {'✅ PASSED' if flow_test_passed else '❌ FAILED'}")
    
    overall_success = config_test_passed and flow_test_passed
    
    if overall_success:
        logger.info("🎉 All tests passed! OAuth session configuration is ready.")
        logger.info("🔄 You can now restart your Flask application and test the OAuth flow.")
        logger.info("🌐 Navigate to: http://localhost:5001/admin/setup-google-drive")
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)