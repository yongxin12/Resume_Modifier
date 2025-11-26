"""
Complete OAuth Session Fix Script
Integrates all fixes for OAuth state validation and session management in Docker
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/rex/project/resume-editor/project/Resume_Modifier/oauth_session_fix.log')
    ]
)

logger = logging.getLogger(__name__)

def fix_server_oauth_configuration():
    """Update server.py to use fixed OAuth authentication and session management."""
    
    server_file_path = '/home/rex/project/resume-editor/project/Resume_Modifier/core/app/server.py'
    
    # Read current server.py content
    try:
        with open(server_file_path, 'r') as f:
            content = f.read()
        logger.info("✅ Read current server.py content")
    except Exception as e:
        logger.error(f"Failed to read server.py: {e}")
        return False
    
    # Fixes to apply
    fixes_applied = []
    
    # Fix 1: Add missing imports
    import_fixes = """
# Enhanced OAuth and Session Management
from app.services.google_admin_auth_fixed import GoogleAdminAuthServiceFixed, create_oauth_temp_states_table, cleanup_expired_oauth_states
from app.services.flask_session_config import configure_flask_sessions_for_docker, setup_oauth_session_support, validate_session_configuration
import secrets
from datetime import datetime, timedelta
"""
    
    if 'GoogleAdminAuthServiceFixed' not in content:
        # Find the import section and add our imports
        import_section_end = content.find('\n\napp = Flask(__name__)')
        if import_section_end != -1:
            content = content[:import_section_end] + '\n' + import_fixes + content[import_section_end:]
            fixes_applied.append("Added enhanced OAuth imports")
    
    # Fix 2: Add session configuration after Flask app creation
    session_config_code = """
# Configure Flask sessions for Docker environment
configure_flask_sessions_for_docker(app)
setup_oauth_session_support(app)

# Validate session configuration
session_validation = validate_session_configuration(app)
if not session_validation.get('OVERALL_VALID', False):
    logger.error("Session configuration validation failed - OAuth may not work properly")

# Initialize OAuth temporary states table
with app.app_context():
    create_oauth_temp_states_table()
"""
    
    if 'configure_flask_sessions_for_docker' not in content:
        # Add after Flask app creation but before routes
        app_creation_line = content.find('app = Flask(__name__)')
        if app_creation_line != -1:
            # Find end of app configuration section
            next_route_start = content.find('\n@app.route', app_creation_line)
            if next_route_start != -1:
                content = content[:next_route_start] + '\n' + session_config_code + content[next_route_start:]
                fixes_applied.append("Added session configuration")
    
    # Fix 3: Replace GoogleAdminAuthService with fixed version
    if 'GoogleAdminAuthService()' in content:
        content = content.replace('GoogleAdminAuthService()', 'GoogleAdminAuthServiceFixed()')
        fixes_applied.append("Updated to use fixed OAuth authentication service")
    
    # Fix 4: Add enhanced error handling to OAuth callback
    enhanced_callback_code = '''
@app.route('/oauth/callback')
def oauth_callback():
    """Enhanced OAuth callback with improved state validation and session management."""
    try:
        # Clean up expired OAuth states first
        cleanup_expired_oauth_states()
        
        # Get authorization code and state from callback
        authorization_code = request.args.get('code')
        state = request.args.get('state')
        
        if not authorization_code:
            logger.error("OAuth callback missing authorization code")
            return jsonify({
                'status': 'error',
                'message': 'Authorization failed - no authorization code received'
            }), 400
        
        if not state:
            logger.error("OAuth callback missing state parameter")
            return jsonify({
                'status': 'error',
                'message': 'Authorization failed - no state parameter received'
            }), 400
        
        logger.info(f"OAuth callback received: code={authorization_code[:10]}..., state={state[:10]}...")
        
        # Debug session state
        from app.services.flask_session_config import debug_session_state
        session_debug = debug_session_state(dict(session))
        logger.info(f"Session state during callback:\\n{session_debug}")
        
        # Use fixed authentication service
        auth_service = GoogleAdminAuthServiceFixed()
        
        # Handle OAuth callback with enhanced error handling
        try:
            credentials = auth_service.handle_oauth_callback(authorization_code, state)
            
            logger.info("✅ OAuth callback successful - credentials stored")
            return jsonify({
                'status': 'success',
                'message': 'Google Drive authentication successful! You can now close this window.',
                'redirect_url': '/admin/google-drive-status'
            })
            
        except ValueError as ve:
            logger.error(f"OAuth validation error: {str(ve)}")
            return jsonify({
                'status': 'error',
                'message': f'Authentication validation failed: {str(ve)}',
                'debug_info': {
                    'state_provided': state[:10] + '...' if len(state) > 10 else state,
                    'session_keys': list(session.keys()),
                    'session_id': session.get('session_id', 'Not set')
                }
            }), 400
            
        except Exception as e:
            logger.error(f"OAuth processing error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Authentication processing failed: {str(e)}'
            }), 500
    
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'OAuth callback failed: {str(e)}'
        }), 500
'''
    
    # Find and replace the existing OAuth callback function
    callback_start = content.find('@app.route(\'/oauth/callback\')')
    if callback_start != -1:
        # Find the end of the function
        next_route_start = content.find('\n@app.route', callback_start + 1)
        next_function_start = content.find('\ndef ', callback_start + 1)
        
        # Use whichever comes first
        function_end = next_route_start if next_route_start != -1 and (next_function_start == -1 or next_route_start < next_function_start) else next_function_start
        
        if function_end != -1:
            content = content[:callback_start] + enhanced_callback_code + '\n' + content[function_end:]
            fixes_applied.append("Enhanced OAuth callback with improved error handling")
    
    # Fix 5: Add session cleanup endpoint for debugging
    cleanup_endpoint = '''
@app.route('/admin/clear-oauth-session', methods=['POST'])
@jwt_required()
def clear_oauth_session():
    """Clear OAuth session data for debugging purposes."""
    try:
        # Get current user and verify admin privileges
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'status': 'error', 'message': 'Admin privileges required'}), 403
        
        # Clear session OAuth data
        session.pop('oauth_session_store', None)
        session.pop('session_id', None)
        
        # Clear database temporary states
        cleanup_expired_oauth_states()
        
        logger.info(f"Cleared OAuth session data for admin user {current_user_id}")
        return jsonify({
            'status': 'success',
            'message': 'OAuth session data cleared'
        })
        
    except Exception as e:
        logger.error(f"Failed to clear OAuth session: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to clear session: {str(e)}'
        }), 500

'''
    
    if '/admin/clear-oauth-session' not in content:
        # Add before the final error handlers or at the end of routes
        end_of_routes = content.rfind('@app.route')
        if end_of_routes != -1:
            # Find end of that route
            next_section = content.find('\n\n# Error handlers', end_of_routes)
            if next_section == -1:
                next_section = content.find('\nif __name__', end_of_routes)
            if next_section == -1:
                next_section = len(content)
            
            content = content[:next_section] + '\n' + cleanup_endpoint + content[next_section:]
            fixes_applied.append("Added OAuth session cleanup endpoint")
    
    # Write the updated content
    try:
        with open(server_file_path, 'w') as f:
            f.write(content)
        logger.info("✅ Updated server.py with OAuth session fixes")
    except Exception as e:
        logger.error(f"Failed to write updated server.py: {e}")
        return False
    
    return fixes_applied


def install_flask_session_dependency():
    """Install Flask-Session for persistent session storage."""
    import subprocess
    
    try:
        # Install Flask-Session
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'Flask-Session'
        ], capture_output=True, text=True, check=True)
        
        logger.info("✅ Flask-Session installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Flask-Session: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False


def main():
    """Main execution function."""
    logger.info("🚀 Starting comprehensive OAuth session fix...")
    logger.info(f"Timestamp: {datetime.now()}")
    
    # Step 1: Install required dependencies
    logger.info("📦 Installing Flask-Session dependency...")
    if install_flask_session_dependency():
        logger.info("✅ Dependencies installed")
    else:
        logger.warning("⚠️  Flask-Session installation failed - will use basic session management")
    
    # Step 2: Update server configuration
    logger.info("🔧 Applying server.py OAuth fixes...")
    fixes = fix_server_oauth_configuration()
    
    if fixes:
        logger.info("✅ Server.py OAuth fixes applied:")
        for fix in fixes:
            logger.info(f"   • {fix}")
    else:
        logger.error("❌ Failed to apply server.py fixes")
        return False
    
    # Step 3: Create requirements update
    requirements_path = '/home/rex/project/resume-editor/project/Resume_Modifier/requirements.txt'
    try:
        # Read existing requirements
        with open(requirements_path, 'r') as f:
            requirements = f.read()
        
        # Add Flask-Session if not present
        if 'Flask-Session' not in requirements:
            requirements += '\\nFlask-Session>=0.4.0\\n'
            
            with open(requirements_path, 'w') as f:
                f.write(requirements)
            
            logger.info("✅ Added Flask-Session to requirements.txt")
    
    except Exception as e:
        logger.warning(f"Could not update requirements.txt: {e}")
    
    # Summary
    logger.info("🎉 OAuth session fix completed successfully!")
    logger.info("📋 Summary of changes:")
    logger.info("   • Enhanced OAuth authentication service with Docker session support")
    logger.info("   • Fixed session state validation and CSRF protection")
    logger.info("   • Added database fallback for OAuth state storage")
    logger.info("   • Improved error handling and debugging capabilities")
    logger.info("   • Added session cleanup utilities")
    
    logger.info("🔄 Next steps:")
    logger.info("   1. Restart your Flask application")
    logger.info("   2. Test OAuth flow: /admin/setup-google-drive")
    logger.info("   3. Monitor logs for any remaining issues")
    logger.info("   4. Use /admin/clear-oauth-session if needed for debugging")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)