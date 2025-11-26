#!/usr/bin/env python3
"""
Update Railway production database to set admin privileges
"""
import os
import sys

# Add the path for Railway commands
sys.path.append('/home/rex/project/resume-editor/project/Resume_Modifier')

def update_production_admin():
    """Update the production database to set admin privileges"""
    
    print("🗄️  UPDATING PRODUCTION DATABASE")
    print("=" * 50)
    
    # SQL command to set admin privileges
    sql_command = """
    UPDATE users 
    SET is_admin = true, updated_at = NOW() 
    WHERE email = 'admin@resumemodifier.com';
    """
    
    print("SQL Command to execute:")
    print(sql_command)
    
    print("\n📋 RAILWAY DATABASE UPDATE STEPS:")
    print("1. Go to Railway dashboard: https://railway.app")
    print("2. Select your Resume Modifier project")
    print("3. Click on PostgreSQL service")
    print("4. Go to 'Query' or 'Data' tab")
    print("5. Execute the SQL command above")
    print("6. Verify the update worked")
    
    print("\n🔍 VERIFICATION QUERY:")
    verification_query = """
    SELECT id, email, is_admin, created_at 
    FROM users 
    WHERE email = 'admin@resumemodifier.com';
    """
    print(verification_query)
    
    print("\n✅ Expected result: is_admin should be 'true'")

def test_admin_oauth():
    """Test admin OAuth setup"""
    
    print("\n🔐 ADMIN OAUTH SETUP INSTRUCTIONS")
    print("=" * 50)
    
    print("After updating the database:")
    print("1. 🌐 Visit: https://resumemodifier-production-44a2.up.railway.app/auth/google/admin")
    print("2. 🔑 Login with: admin@resumemodifier.com / SecureAdmin123!")
    print("3. 🔐 Complete Google OAuth authentication")
    print("4. ✅ Grant Google Drive permissions")
    print("5. 🧪 Test file upload with Google Drive integration")
    
    print("\n🧪 TEST FILE UPLOAD:")
    test_curl = """
    curl -X POST "https://resumemodifier-production-44a2.up.railway.app/api/files/upload?google_drive=true" \\
      -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
      -F "file=@sample.pdf"
    """
    print(test_curl)

def provide_troubleshooting():
    """Provide troubleshooting steps"""
    
    print("\n🔧 TROUBLESHOOTING TRANSACTION ERRORS")
    print("=" * 50)
    
    print("If you still get database transaction errors:")
    print("1. 🔄 Restart the Railway service")
    print("2. 🗄️  Check database connection pool settings")
    print("3. 📊 Monitor database logs for errors")
    print("4. 🔍 Verify all database migrations are applied")
    
    print("\n📋 RAILWAY SERVICE RESTART:")
    print("1. Go to Railway dashboard")
    print("2. Select Resume Modifier project")
    print("3. Click on the web service")
    print("4. Click 'Restart' or redeploy")
    
    print("\n🎯 KEY FIXES APPLIED:")
    print("✅ Enhanced transaction management with proper rollback")
    print("✅ Connection state reset before operations")
    print("✅ Explicit transaction blocks with auto-commit")
    print("✅ Better error handling for integrity constraints")

def main():
    """Main function"""
    
    print("🔧 PRODUCTION DATABASE & ADMIN SETUP")
    print("=" * 60)
    
    # Update database instructions
    update_production_admin()
    
    # OAuth setup instructions
    test_admin_oauth()
    
    # Troubleshooting
    provide_troubleshooting()
    
    print("\n🎉 SUMMARY:")
    print("1. ✅ Admin user created: admin@resumemodifier.com")
    print("2. 🔧 Transaction fixes applied to codebase")
    print("3. 📋 Manual database update required")
    print("4. 🔐 OAuth setup needed after database update")
    
    print("\n🚀 Next: Execute the SQL command in Railway dashboard!")

if __name__ == "__main__":
    main()