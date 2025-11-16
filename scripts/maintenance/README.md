# 🛠️ Scripts Directory

Helpful automation scripts for Resume Modifier development and deployment.

---

## 📜 Available Scripts

### `validate_config.py` - Environment Configuration Validator ⭐ NEW

Comprehensive validation tool for Resume Editor environment configuration with special focus on password recovery functionality.

#### Features
- ✅ Validates all required environment variables
- ✅ Tests database connection and table structure
- ✅ Validates email configuration and SMTP connectivity
- ✅ Tests password reset service functionality
- ✅ Checks security settings and best practices
- ✅ Sends test emails for verification
- ✅ Structured error reporting and helpful suggestions

#### Usage

```bash
# Validate all configuration
python scripts/validate_config.py

# Test specific components
python scripts/validate_config.py --component email
python scripts/validate_config.py --component database
python scripts/validate_config.py --component security

# Send test email
python scripts/validate_config.py --email test@example.com

# Verbose output for debugging
python scripts/validate_config.py --verbose
```

#### Components Tested

| Component | Description |
|-----------|-------------|
| **Environment Variables** | Checks all required and optional environment variables |
| **Database** | Tests connection, table existence, and basic queries |
| **Email Configuration** | Validates SMTP settings and template rendering |
| **Password Reset Service** | Tests rate limiting, token generation, and service logic |
| **Security Settings** | Validates password requirements, rate limits, and JWT configuration |

#### Example Output

```bash
🔍 Resume Editor - Environment Configuration Validator
📅 2024-10-25 14:30:00
============================================================

🔍 Checking required environment variables...
✅ OPENAI_API_KEY: Set
✅ DATABASE_URL: Set
✅ JWT_SECRET: Set
✅ Email configuration: Complete

🗄️  Testing database connection...
✅ Database connection: Success
✅ Table 'users': Exists
✅ Table 'password_reset_tokens': Exists
✅ Database queries: Working (5 users, 0 tokens)

📧 Testing email configuration...
✅ Email service: Initialized
✅ SMTP connection: Success
✅ Email templates: Working

📤 Sending test email to test@example.com...
✅ Test email: Sent successfully

🔐 Testing password reset service...
✅ Password reset service: Initialized
✅ Rate limiting: Working
✅ Token generation: Working

🛡️  Checking security settings...
✅ Password minimum length: 8
✅ Rate limiting: 5/hour per user, 10/hour per IP
✅ Token expiry: 24 hours
✅ JWT secret: Adequate length

🏁 VALIDATION SUMMARY
============================================================
🎉 All checks passed! Your configuration looks great.

📊 Results:
   ✅ Errors: 0
   ⚠️  Warnings: 0

🚀 Your application is ready to use!
```

#### Prerequisites

1. **Python environment activated**
   ```bash
   source venv/bin/activate
   ```

2. **Dependencies installed**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment file configured**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

---

### `railway_migrate.py` - Railway Database Migration Tool (Python)

**Recommended** - More reliable URL parsing than the bash version.

Simplifies running database migrations on Railway's PostgreSQL database from your local machine.

#### Features
- ✅ Automatically fetches Railway's public database URL with robust parsing
- ✅ Validates Railway CLI installation and authentication
- ✅ Supports multiple migration commands
- ✅ User-friendly output with emojis
- ✅ Better error handling than bash version

#### Usage

```bash
# Run database upgrade (default)
./scripts/railway_migrate.py

# Or specify a command:
./scripts/railway_migrate.py [command]
```

#### Commands

| Command | Description |
|---------|-------------|
| `upgrade` | Apply pending migrations (default) |
| `downgrade` | Revert the last migration |
| `current` | Show current migration version |
| `history` | Show full migration history |
| `stamp` | Mark database as up to date without running migrations |

#### Examples

```bash
# Apply all pending migrations
./scripts/railway_migrate.py upgrade

# Check current database version
./scripts/railway_migrate.py current

# View migration history
./scripts/railway_migrate.py history

# Rollback last migration
./scripts/railway_migrate.py downgrade
```

---

### `railway_migrate.sh` - Railway Database Migration Tool (Bash)

Alternative bash version of the migration tool.

#### Features
- ✅ Automatically fetches Railway's public database URL
- ✅ Validates Railway CLI installation and authentication
- ✅ Supports multiple migration commands
- ✅ User-friendly output with emojis and colors
- ✅ Error handling and helpful tips

#### Usage

```bash
# Run database upgrade (default)
./scripts/railway_migrate.sh

# Or specify a command:
./scripts/railway_migrate.sh [command]
```

#### Commands

| Command | Description |
|---------|-------------|
| `upgrade` | Apply pending migrations (default) |
| `downgrade` | Revert the last migration |
| `current` | Show current migration version |
| `history` | Show full migration history |
| `stamp` | Mark database as up to date without running migrations |

#### Examples

```bash
# Apply all pending migrations
./scripts/railway_migrate.sh upgrade

# Check current database version
./scripts/railway_migrate.sh current

# View migration history
./scripts/railway_migrate.sh history

# Rollback last migration
./scripts/railway_migrate.sh downgrade
```

#### Prerequisites

1. **Railway CLI installed**
   ```bash
   npm i -g @railway/cli
   ```

2. **Logged in to Railway**
   ```bash
   railway login
   ```

3. **Project linked**
   ```bash
   railway link
   ```

4. **Flask environment activated**
   ```bash
   source venv/bin/activate
   ```

#### Troubleshooting

**Error: "Railway CLI not found"**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Or using Homebrew (macOS)
brew install railway
```

**Error: "Not logged in to Railway"**
```bash
railway login
```

**Error: "Could not retrieve DATABASE_PUBLIC_URL"**
- Ensure you have a Postgres service in Railway
- Check Railway project is linked: `railway status`
- Manually verify: `railway variables --service Postgres`

---

## 🔧 Creating New Scripts

When adding new scripts to this directory:

1. **Make it executable**
   ```bash
   chmod +x scripts/your_script.sh
   ```

2. **Add shebang** at the top
   ```bash
   #!/bin/bash
   ```

3. **Include error handling**
   ```bash
   set -e  # Exit on error
   ```

4. **Document in this README**
   - Add to "Available Scripts" section
   - Include usage examples
   - List prerequisites

5. **Use clear output**
   - Use emojis for visual clarity
   - Echo what the script is doing
   - Provide helpful error messages

---

## 📋 Script Template

```bash
#!/bin/bash

# Script Name - Brief description
# Author: Your Name
# Date: YYYY-MM-DD

set -e  # Exit on error

echo "🚀 Script Name"
echo "================"
echo ""

# Check prerequisites
if ! command -v some_command &> /dev/null; then
    echo "❌ Error: some_command not found"
    echo "📥 Install it with: installation_command"
    exit 1
fi

# Main logic
echo "✅ Starting process..."
# Your code here

echo ""
echo "✅ Complete!"
```

---

## 🔐 Security Notes

⚠️ **Never commit:**
- Database credentials
- API keys
- Passwords
- Sensitive URLs

✅ **Always:**
- Use environment variables
- Add `.env*` to `.gitignore`
- Validate input
- Handle errors gracefully

---

## 📚 Additional Resources

- [Railway CLI Documentation](https://docs.railway.app/develop/cli)
- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [Bash Scripting Guide](https://www.gnu.org/software/bash/manual/bash.html)

---

**Need help?** Check [RAILWAY_MIGRATION_GUIDE.md](../RAILWAY_MIGRATION_GUIDE.md) for detailed migration troubleshooting.
