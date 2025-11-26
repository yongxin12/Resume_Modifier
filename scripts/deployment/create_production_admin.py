#!/usr/bin/env python3
"""
Create admin user for production Railway deployment
"""
import requests
import json
import sys
from datetime import datetime

def create_production_admin():
    """Create admin user for production deployment"""
    
    print("👤 CREATING PRODUCTION ADMIN USER")
    print("=" * 50)
    
    base_url = "https://resumemodifier-production-44a2.up.railway.app"
    
    # Test connectivity first
    try:
        health_check = requests.get(f"{base_url}", timeout=10)
        print(f"✅ Production site accessible: {health_check.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach production site: {e}")
        return False
    
    # Try different endpoints to create admin
    endpoints_to_try = [
        "/api/auth/register",
        "/api/users/register", 
        "/api/register",
        "/auth/register"
    ]
    
    # Admin user data
    admin_data = {
        "email": "admin@resumemodifier.com",
        "password": "SecureAdmin123!",
        "first_name": "Admin",
        "last_name": "User",
        "is_admin": True
    }
    
    print(f"Admin email: {admin_data['email']}")
    print(f"Admin password: {admin_data['password']}")
    
    for endpoint in endpoints_to_try:
        try:
            print(f"\n🔍 Trying endpoint: {endpoint}")
            
            response = requests.post(
                f"{base_url}{endpoint}",
                json=admin_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "AdminCreator/1.0"
                },
                timeout=15
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ Admin user created successfully!")
                try:
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                    return True
                except:
                    print(f"Response text: {response.text[:500]}")
                    return True
                    
            elif response.status_code == 409:
                print("ℹ️  User might already exist")
                print(f"Response: {response.text[:200]}")
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            continue
    
    print("\n🔧 ALTERNATIVE: MANUAL ADMIN SETUP")
    print("Since automatic creation failed, you can:")
    print("1. Register normally at the production site")
    print("2. Then manually update the database to set is_admin=true")
    print("3. Or use the production database admin panel")
    
    return False

def test_oauth_setup():
    """Test OAuth setup after admin creation"""
    
    print("\n🔐 TESTING OAUTH SETUP")
    print("=" * 50)
    
    base_url = "https://resumemodifier-production-44a2.up.railway.app"
    
    try:
        # Test OAuth initiation
        oauth_response = requests.get(f"{base_url}/auth/google/admin", timeout=10)
        print(f"OAuth admin endpoint: {oauth_response.status_code}")
        
        if oauth_response.status_code == 302:
            print("✅ OAuth redirect working")
            print(f"Location: {oauth_response.headers.get('Location', 'N/A')[:100]}...")
        elif oauth_response.status_code == 401:
            print("ℹ️  OAuth endpoint requires authentication (expected)")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth test failed: {e}")
        return False

def provide_manual_steps():
    """Provide manual steps for admin setup"""
    
    print("\n📋 MANUAL ADMIN SETUP STEPS")
    print("=" * 50)
    
    steps = [
        "1. 🌐 Go to https://resumemodifier-production-44a2.up.railway.app",
        "2. 📝 Register a new account with admin@resumemodifier.com",
        "3. 🔑 Use password: SecureAdmin123!",
        "4. 🗄️  Access Railway database dashboard",
        "5. ⚙️  Run SQL: UPDATE users SET is_admin = true WHERE email = 'admin@resumemodifier.com'",
        "6. 🔐 Navigate to /auth/google/admin to set up OAuth",
        "7. ✅ Complete Google Drive authentication",
        "8. 🧪 Test file upload with google_drive=true parameter"
    ]
    
    for step in steps:
        print(step)
    
    print("\n🎯 DATABASE UPDATE COMMAND:")
    print("UPDATE users SET is_admin = true WHERE email = 'admin@resumemodifier.com';")
    
    print("\n🔗 USEFUL LINKS:")
    print("• Production site: https://resumemodifier-production-44a2.up.railway.app")
    print("• Admin OAuth: https://resumemodifier-production-44a2.up.railway.app/auth/google/admin")
    print("• Railway dashboard: https://railway.app")

def main():
    """Main function"""
    
    print("🚀 PRODUCTION ADMIN SETUP UTILITY")
    print("=" * 60)
    
    # Try to create admin automatically
    success = create_production_admin()
    
    # Test OAuth setup
    test_oauth_setup()
    
    # Provide manual steps regardless
    provide_manual_steps()
    
    if success:
        print("\n🎉 SUCCESS: Admin user created!")
    else:
        print("\n⚠️  MANUAL SETUP REQUIRED")
        print("Follow the manual steps above to complete admin setup")
    
    print("\n✅ Setup utility completed")

if __name__ == "__main__":
    main()