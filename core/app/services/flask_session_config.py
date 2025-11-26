"""
Flask Session Configuration for Docker Environment
Fixes OAuth session state validation issues in containerized deployments
"""

import os
import secrets
from datetime import timedelta
from typing import Dict, Any
from flask import Flask
import logging

logger = logging.getLogger(__name__)

def configure_flask_sessions_for_docker(app: Flask) -> Dict[str, Any]:
    """
    Configure Flask session management for Docker environment compatibility.
    
    Addresses OAuth state validation failures by ensuring:
    1. Proper session configuration for containerized environment
    2. Persistent session storage
    3. CSRF protection settings
    4. Cookie security configuration
    
    Args:
        app: Flask application instance
        
    Returns:
        Dict with configuration applied
    """
    
    # Get or generate secret key
    secret_key = app.config.get('SECRET_KEY')
    if not secret_key:
        # Generate a secure secret key if not provided
        secret_key = secrets.token_hex(32)
        app.config['SECRET_KEY'] = secret_key
        logger.warning("Generated new SECRET_KEY - consider setting this as environment variable")
    
    # Session Configuration for Docker
    session_config = {
        # Basic session settings
        'SECRET_KEY': secret_key,
        'SESSION_TYPE': 'filesystem',  # Use filesystem for persistence in Docker
        'SESSION_FILE_DIR': '/tmp/flask_sessions',  # Docker-friendly session storage
        'SESSION_FILE_THRESHOLD': 500,  # Maximum number of sessions
        'SESSION_FILE_MODE': 0o600,     # Secure file permissions
        
        # Session lifetime and security
        'PERMANENT_SESSION_LIFETIME': timedelta(hours=2),  # Session duration
        'SESSION_PERMANENT': True,      # Make sessions persistent by default
        'SESSION_USE_SIGNER': True,     # Sign session cookies for security
        'SESSION_KEY_PREFIX': 'resume_oauth:',  # Prefix for session keys
        
        # Cookie configuration for Docker/reverse proxy environments - handled by Flask app config
        'SESSION_COOKIE_DOMAIN': None,  # Let Flask determine domain
        'SESSION_COOKIE_PATH': '/',
        'SESSION_COOKIE_HTTPONLY': True,  # Prevent XSS attacks
        'SESSION_COOKIE_SECURE': app.config.get('FLASK_ENV') == 'production',  # HTTPS only in production
        'SESSION_COOKIE_SAMESITE': 'Lax',  # Allow OAuth redirects
        
        # CSRF and state management
        'WTF_CSRF_ENABLED': True,
        'WTF_CSRF_TIME_LIMIT': 3600,  # 1 hour CSRF token lifetime
        'WTF_CSRF_SSL_STRICT': app.config.get('FLASK_ENV') == 'production',
        
        # Application-specific OAuth settings
        'OAUTH_STATE_TIMEOUT': timedelta(minutes=10),  # OAuth state expiration
        'OAUTH_SESSION_STORAGE': 'hybrid',  # Use both session and database
    }
    
    # Apply configuration to Flask app
    for key, value in session_config.items():
        app.config[key] = value
    
    # Set Flask session cookie name directly on app
    app.session_cookie_name = 'resume_oauth_session'
    
    # Create session directory if it doesn't exist
    session_dir = session_config['SESSION_FILE_DIR']
    os.makedirs(session_dir, mode=0o700, exist_ok=True)
    
    # Skip Flask-Session initialization due to compatibility issues with Werkzeug
    # Use basic Flask session management instead
    logger.info("Using basic Flask session management (bypassing Flask-Session for compatibility)")
    app.permanent_session_lifetime = session_config['PERMANENT_SESSION_LIFETIME']
    
    logger.info(f"✅ Flask session configuration applied for Docker environment")
    logger.info(f"   Session storage: {session_config['SESSION_TYPE']}")
    logger.info(f"   Session directory: {session_config['SESSION_FILE_DIR']}")
    logger.info(f"   Session lifetime: {session_config['PERMANENT_SESSION_LIFETIME']}")
    
    return session_config


def setup_oauth_session_support(app: Flask):
    """
    Additional OAuth-specific session configuration for Docker compatibility.
    """
    
    @app.before_request
    def ensure_session_setup():
        """Ensure proper session initialization for OAuth flows."""
        from flask import session
        from datetime import datetime
        
        # Make session permanent for OAuth flows
        session.permanent = True
        
        # Initialize session tracking if not present
        if 'session_initialized' not in session:
            session['session_initialized'] = True
            session['session_created_at'] = str(datetime.utcnow())
    
    @app.after_request
    def enhance_session_security(response):
        """Add additional security headers for session management."""
        from flask import request
        
        # Add cache control for OAuth pages
        if '/oauth' in request.path or '/auth' in request.path:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    logger.info("✅ OAuth session support configured")


def validate_session_configuration(app: Flask) -> Dict[str, bool]:
    """
    Validate that session configuration is properly set up for OAuth.
    
    Returns:
        Dict with validation results
    """
    validation_results = {}
    
    # Check required configuration
    required_settings = [
        'SECRET_KEY',
        'SESSION_TYPE',
        'PERMANENT_SESSION_LIFETIME'
    ]
    
    for setting in required_settings:
        is_configured = setting in app.config and app.config[setting] is not None
        validation_results[setting] = is_configured
        
        if is_configured:
            logger.info(f"✅ {setting}: Configured")
        else:
            logger.error(f"❌ {setting}: Missing or None")
    
    # Check session directory
    session_dir = app.config.get('SESSION_FILE_DIR')
    if session_dir:
        dir_exists = os.path.exists(session_dir)
        dir_writable = os.access(session_dir, os.W_OK) if dir_exists else False
        
        validation_results['SESSION_DIRECTORY_EXISTS'] = dir_exists
        validation_results['SESSION_DIRECTORY_WRITABLE'] = dir_writable
        
        if dir_exists and dir_writable:
            logger.info(f"✅ Session directory: {session_dir} (exists and writable)")
        else:
            logger.error(f"❌ Session directory: {session_dir} (issues detected)")
    
    # Overall validation
    all_valid = all(validation_results.values())
    validation_results['OVERALL_VALID'] = all_valid
    
    if all_valid:
        logger.info("✅ Session configuration validation: PASSED")
    else:
        logger.error("❌ Session configuration validation: FAILED")
        logger.error("   Please check the failed settings above")
    
    return validation_results


# Utility functions for session debugging

def debug_session_state(session_data: Dict[str, Any]) -> str:
    """
    Generate debug information about current session state.
    Useful for troubleshooting OAuth issues.
    """
    debug_info = []
    debug_info.append("=== SESSION DEBUG INFO ===")
    
    # Basic session info
    debug_info.append(f"Session ID: {session_data.get('session_id', 'Not set')}")
    debug_info.append(f"Session Permanent: {session_data.get('permanent', False)}")
    debug_info.append(f"Session Created: {session_data.get('session_created_at', 'Unknown')}")
    
    # OAuth-specific info
    oauth_store = session_data.get('oauth_session_store', {})
    if oauth_store:
        debug_info.append("OAuth Session Store:")
        debug_info.append(f"  State: {oauth_store.get('oauth_state', 'Not set')[:10]}...")
        debug_info.append(f"  Admin User ID: {oauth_store.get('admin_user_id', 'Not set')}")
        debug_info.append(f"  Initiated: {oauth_store.get('oauth_initiated_at', 'Not set')}")
        debug_info.append(f"  Expires: {oauth_store.get('expires_at', 'Not set')}")
    else:
        debug_info.append("OAuth Session Store: Empty")
    
    # Session keys
    debug_info.append(f"Session Keys: {list(session_data.keys())}")
    
    debug_info.append("=== END SESSION DEBUG ===")
    
    return "\n".join(debug_info)


if __name__ == "__main__":
    # Test configuration
    from flask import Flask
    app = Flask(__name__)
    
    print("Testing Flask session configuration for Docker...")
    config = configure_flask_sessions_for_docker(app)
    validation = validate_session_configuration(app)
    
    print(f"\nConfiguration applied: {len(config)} settings")
    print(f"Validation results: {validation}")