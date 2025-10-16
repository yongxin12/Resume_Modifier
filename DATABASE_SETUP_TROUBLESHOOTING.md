# 🗄️ Database Setup & Troubleshooting Guide

## 🚨 **CRITICAL ISSUE IDENTIFIED**

**Your current configuration is incompatible with the existing documentation.**

### ❌ **Current Problem:**
- **Documentation expects:** PostgreSQL database
- **Your .env has:** MySQL database configuration
- **Result:** Authentication errors and connection failures

---

## 🔍 **Root Cause Analysis**

### **Primary Issues:**

1. **Database Type Mismatch**
   - Documentation and Docker setup configured for PostgreSQL
   - Your `.env` file configured for MySQL
   - MySQL user authentication failing

2. **MySQL Authentication Problems**
   - User `mysql` doesn't exist or has wrong privileges
   - Password authentication failing
   - No database `resume_app` created

3. **Service Dependencies**
   - Flask app expects database to be running and accessible
   - Migration scripts expect valid database connection
   - No fallback for connection failures

---

## 🛠️ **Solution Options**

### **Option 1: Switch to PostgreSQL (RECOMMENDED)**

This aligns with existing documentation and Docker configuration.

#### **Step 1: Update Environment Configuration**
```bash
# Edit your .env file
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_app
```

#### **Step 2: Use Docker PostgreSQL**
```bash
# Start PostgreSQL container
docker-compose up db -d

# Verify PostgreSQL is running
docker-compose ps db

# Connect to PostgreSQL
docker-compose exec db psql -U postgres
```

#### **Step 3: Create Database**
```sql
-- Inside PostgreSQL shell
CREATE DATABASE resume_app;
\l  -- List databases to verify
\q  -- Exit
```

#### **Step 4: Run Migrations**
```bash
cd /home/rex/project/resume-editor/project/Resume_Modifier
python3 -c "
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Database tables created successfully')
"
```

### **Option 2: Fix MySQL Setup**

If you prefer to keep MySQL, follow these steps:

#### **Step 1: Fix MySQL User Authentication**
```bash
# Connect as root with sudo
sudo mysql

# Inside MySQL shell:
CREATE USER 'mysql'@'localhost' IDENTIFIED BY 'Mintmelon666!';
CREATE DATABASE IF NOT EXISTS resume_app;
GRANT ALL PRIVILEGES ON resume_app.* TO 'mysql'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### **Step 2: Test Connection**
```bash
mysql -u mysql -pMintmelon666! -h localhost -P 3306 resume_app
```

#### **Step 3: Update Docker Configuration**
You'll need to modify `docker-compose.yml` to use MySQL instead of PostgreSQL.

---

## 🔧 **Complete Setup Guide**

### **PostgreSQL Setup (Recommended)**

#### **1. Environment Configuration**
```bash
# .env file content
OPENAI_API_KEY=your_openai_api_key_here

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/resume_app

# Flask Configuration
FLASK_SECRET_KEY=your_flask_secret_key_here

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5001/auth/google/callback
```

#### **2. Start Database Service**
```bash
# Using Docker (recommended)
docker-compose up db -d

# Verify service is running
docker-compose ps db
docker-compose logs db
```

#### **3. Database Initialization**
```bash
# Method 1: Using Flask-Migrate
cd /home/rex/project/resume-editor/project/Resume_Modifier
export FLASK_APP=app.server
flask db upgrade

# Method 2: Direct table creation
python3 -c "
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Database initialized successfully')
"
```

#### **4. Verify Setup**
```bash
# Test database connection
python3 -c "
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        result = db.session.execute(text('SELECT 1')).scalar()
        print('✅ Database connection successful')
        print(f'Test query result: {result}')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
"
```

#### **5. Start Flask Application**
```bash
# Start the application
python3 -m app.server

# Or using Flask CLI
export FLASK_APP=app.server
flask run --host=0.0.0.0 --port=5001
```

---

## 🧪 **Testing Database Connection**

### **Connection Test Script**
```python
#!/usr/bin/env python3
"""
Database Connection Test Script
Run this to verify your database setup is working correctly.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def test_database_connection():
    # Load environment variables
    load_dotenv()
    
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    print(f"🔍 Testing connection to: {database_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1')).scalar()
            print(f"✅ Connection successful! Test query result: {result}")
            
            # Test Flask app context
            try:
                from app import create_app
                from app.extensions import db
                
                app = create_app()
                with app.app_context():
                    db.session.execute(text('SELECT 1'))
                    print("✅ Flask app database connection successful!")
                    
                    # List tables
                    tables = db.engine.table_names()
                    print(f"📋 Database tables: {tables}")
                    
            except Exception as flask_error:
                print(f"❌ Flask app connection failed: {flask_error}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
```

Save this as `test_database.py` and run:
```bash
python3 test_database.py
```

---

## 🚨 **Common Error Solutions**

### **Error: Access denied for user 'mysql'@'localhost'**
```bash
# Solution 1: Create MySQL user
sudo mysql
CREATE USER 'mysql'@'localhost' IDENTIFIED BY 'Mintmelon666!';
GRANT ALL PRIVILEGES ON *.* TO 'mysql'@'localhost';
FLUSH PRIVILEGES;

# Solution 2: Switch to PostgreSQL (recommended)
# Update DATABASE_URL in .env to use PostgreSQL
```

### **Error: Can't connect to MySQL server**
```bash
# Check if MySQL is running
sudo systemctl status mysql
sudo systemctl start mysql

# Check port availability
sudo netstat -tulnp | grep 3306

# Check MySQL configuration
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

### **Error: Database 'resume_app' doesn't exist**
```bash
# For MySQL:
mysql -u root -p
CREATE DATABASE resume_app;

# For PostgreSQL:
docker-compose exec db psql -U postgres
CREATE DATABASE resume_app;
```

### **Error: Flask-Migrate issues**
```bash
# Reset migrations (WARNING: Destroys data)
rm -rf migrations/
export FLASK_APP=app.server
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Or create tables directly
python3 -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

---

## 📊 **Database Management Commands**

### **PostgreSQL Management**
```bash
# Connect to database
docker-compose exec db psql -U postgres resume_app

# List databases
docker-compose exec db psql -U postgres -c "\l"

# List tables
docker-compose exec db psql -U postgres resume_app -c "\dt"

# Backup database
docker-compose exec db pg_dump -U postgres resume_app > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres resume_app < backup.sql

# Monitor connections
docker-compose exec db psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

### **MySQL Management**
```bash
# Connect to database
mysql -u mysql -pMintmelon666! resume_app

# Show databases
mysql -u mysql -pMintmelon666! -e "SHOW DATABASES;"

# Show tables
mysql -u mysql -pMintmelon666! resume_app -e "SHOW TABLES;"

# Backup database
mysqldump -u mysql -pMintmelon666! resume_app > backup.sql

# Restore database
mysql -u mysql -pMintmelon666! resume_app < backup.sql
```

---

## 🔍 **Debugging Steps**

### **1. Environment Variables Check**
```bash
# Check if all required variables are set
python3 -c "
import os
from dotenv import load_dotenv

load_dotenv()
required_vars = ['DATABASE_URL', 'OPENAI_API_KEY', 'FLASK_SECRET_KEY']

for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive data
        if 'KEY' in var or 'SECRET' in var:
            masked = value[:10] + '...' if len(value) > 10 else '***'
            print(f'✅ {var}: {masked}')
        else:
            print(f'✅ {var}: {value}')
    else:
        print(f'❌ {var}: Not set')
"
```

### **2. Service Status Check**
```bash
# Check database service
if [[ $DATABASE_URL == *"postgresql"* ]]; then
    echo "Checking PostgreSQL..."
    docker-compose ps db
    docker-compose logs db | tail -10
elif [[ $DATABASE_URL == *"mysql"* ]]; then
    echo "Checking MySQL..."
    sudo systemctl status mysql
    sudo netstat -tulnp | grep 3306
fi
```

### **3. Flask App Health Check**
```bash
# Test Flask app startup
python3 -c "
from app import create_app
import traceback

try:
    app = create_app()
    print('✅ Flask app created successfully')
    print(f'📍 App config: {app.config.get(\"SQLALCHEMY_DATABASE_URI\", \"Not set\")}')
    
    with app.app_context():
        from app.extensions import db
        # Test database
        db.session.execute('SELECT 1')
        print('✅ Database connection in Flask context successful')
        
except Exception as e:
    print(f'❌ Flask app initialization failed: {e}')
    traceback.print_exc()
"
```

---

## 📋 **Pre-flight Checklist**

Before running `flask run`, ensure:

- [ ] **Database Service Running**
  ```bash
  # PostgreSQL
  docker-compose ps db
  
  # MySQL
  sudo systemctl status mysql
  ```

- [ ] **Environment Variables Set**
  ```bash
  cat .env | grep -E "(DATABASE_URL|OPENAI_API_KEY|FLASK_SECRET_KEY)"
  ```

- [ ] **Database Exists**
  ```bash
  # Test connection
  python3 test_database.py
  ```

- [ ] **Tables Created**
  ```bash
  # Run migrations or create tables
  flask db upgrade
  # OR
  python3 -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
  ```

- [ ] **Dependencies Installed**
  ```bash
  pip install -r requirements.txt
  ```

---

## 🚀 **Quick Fix Commands**

### **Complete PostgreSQL Setup (Recommended)**
```bash
# 1. Update .env
sed -i 's|mysql+pymysql://mysql:Mintmelon666!@localhost:3306/resume_app|postgresql://postgres:postgres@localhost:5432/resume_app|' .env

# 2. Start PostgreSQL
docker-compose up db -d

# 3. Create database and tables
docker-compose exec db psql -U postgres -c "CREATE DATABASE resume_app;"
python3 -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"

# 4. Test connection
python3 -c "from app import create_app; from app.extensions import db; from sqlalchemy import text; app = create_app(); app.app_context().push(); print('Result:', db.session.execute(text('SELECT 1')).scalar())"

# 5. Start Flask app
python3 -m app.server
```

### **MySQL Fix (Alternative)**
```bash
# 1. Create MySQL user and database
sudo mysql -e "
CREATE USER IF NOT EXISTS 'mysql'@'localhost' IDENTIFIED BY 'Mintmelon666!';
CREATE DATABASE IF NOT EXISTS resume_app;
GRANT ALL PRIVILEGES ON resume_app.* TO 'mysql'@'localhost';
FLUSH PRIVILEGES;
"

# 2. Test connection
mysql -u mysql -pMintmelon666! resume_app -e "SELECT 1;"

# 3. Create tables
python3 -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"

# 4. Start Flask app
python3 -m app.server
```

---

## 📞 **Getting Help**

If you continue to experience issues:

1. **Run the diagnostic script**: `python3 test_database.py`
2. **Check the logs**: Look for specific error messages
3. **Verify environment**: Ensure all required variables are set
4. **Test connectivity**: Use the connection test commands above

**Most Common Solution**: Switch to PostgreSQL by updating your `.env` file and using Docker Compose as documented in the README.md.

---

*This troubleshooting guide addresses the specific database connectivity issues identified in your setup.*