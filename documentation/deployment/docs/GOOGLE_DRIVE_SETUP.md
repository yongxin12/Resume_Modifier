# Google Drive Integration Setup Guide

This guide explains how to set up Google Drive integration for the Resume Modifier application, including service account authentication, file upload, document conversion, and sharing capabilities.

## Overview

The Google Drive integration provides:
- **File Upload**: Automatic upload of resume files to Google Drive
- **Document Conversion**: Convert PDF files to editable Google Docs
- **User Sharing**: Automatic sharing of documents with file owners
- **Folder Organization**: Organized storage with user-specific folders
- **Link Generation**: Direct access links to Drive files and Google Docs

## Prerequisites

1. Google Cloud Platform (GCP) account
2. A GCP project with Google Drive API enabled
3. Service account with appropriate permissions

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID for later use

## Step 2: Enable Google Drive API

1. In the Google Cloud Console, navigate to **APIs & Services** > **Library**
2. Search for "Google Drive API"
3. Click on it and press **Enable**
4. Also enable **Google Docs API** if you plan to use document conversion

## Step 3: Create a Service Account

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **Service Account**
3. Fill in the service account details:
   - **Name**: `resume-modifier-drive-service`
   - **Description**: `Service account for Resume Modifier Google Drive integration`
4. Click **Create and Continue**
5. Grant the service account the following roles:
   - **Editor** (for file management)
   - **Storage Admin** (for folder creation)
6. Click **Continue** and then **Done**

## Step 4: Generate Service Account Key

1. In the **Credentials** page, find your service account
2. Click on the service account email
3. Go to the **Keys** tab
4. Click **Add Key** > **Create New Key**
5. Select **JSON** format
6. Download the key file (e.g., `resume-modifier-service-account.json`)
7. **Important**: Keep this file secure and never commit it to version control

## Step 5: Create a Shared Google Drive Folder (Optional)

1. Create a folder in Google Drive where uploaded files will be stored
2. Right-click the folder and select **Share**
3. Add your service account email (found in the JSON key file) with **Editor** permissions
4. Note the folder ID from the URL (e.g., `https://drive.google.com/drive/folders/FOLDER_ID_HERE`)

## Step 6: Environment Configuration

Add the following environment variables to your `.env` file:

### Option 1: Using Service Account File Path
```bash
# Google Drive Service Account Configuration
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=/path/to/your/service-account-key.json

# Optional: Specify a parent folder for user folders
GOOGLE_DRIVE_PARENT_FOLDER_ID=your_parent_folder_id_here
```

### Option 2: Using Service Account JSON Content (Recommended for Production)
```bash
# Google Drive Service Account Configuration (JSON content as string)
GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO='{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id-here",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
  "client_email": "resume-modifier-drive-service@your-project-id.iam.gserviceaccount.com",
  "client_id": "client-id-here",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/resume-modifier-drive-service%40your-project-id.iam.gserviceaccount.com"
}'

# Optional: Specify a parent folder for user folders
GOOGLE_DRIVE_PARENT_FOLDER_ID=your_parent_folder_id_here
```

### Additional Configuration Options
```bash
# Enable/disable Google Drive integration
GOOGLE_DRIVE_ENABLED=true

# Default conversion setting (true/false)
GOOGLE_DRIVE_AUTO_CONVERT_PDF=true

# Default sharing setting (true/false)
GOOGLE_DRIVE_AUTO_SHARE=true

# Folder naming pattern (user_id, email, or custom)
GOOGLE_DRIVE_FOLDER_PATTERN=user_id
```

## Step 7: Docker Configuration

If using Docker, you can mount the service account file or pass it as an environment variable:

### Docker Compose Example
```yaml
version: '3.8'
services:
  web:
    build: .
    environment:
      - GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=/app/credentials/service-account.json
      - GOOGLE_DRIVE_PARENT_FOLDER_ID=your_folder_id
    volumes:
      - ./path/to/service-account.json:/app/credentials/service-account.json:ro
    # ... other configuration
```

### Using Environment Variable in Docker
```yaml
version: '3.8'
services:
  web:
    build: .
    environment:
      - GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO=${GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO}
      - GOOGLE_DRIVE_PARENT_FOLDER_ID=${GOOGLE_DRIVE_PARENT_FOLDER_ID}
    # ... other configuration
```

## Step 8: Testing the Setup

1. Start your application
2. Check the logs for Google Drive initialization:
   ```
   INFO: Google Drive service initialized successfully
   ```

3. Test file upload with Google Drive integration:
   ```bash
   curl -X POST http://localhost:5001/api/files/upload \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "file=@test-resume.pdf" \
     -F "google_drive=true"
   ```

4. Verify the response includes Google Drive information:
   ```json
   {
     "success": true,
     "file": {
       "google_drive": {
         "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
         "doc_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
         "drive_link": "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view",
         "doc_link": "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit",
         "is_shared": true
       }
     }
   }
   ```

## Security Best Practices

1. **Never commit service account keys to version control**
2. **Rotate service account keys regularly**
3. **Use minimum required permissions**
4. **Monitor service account usage in GCP Console**
5. **Use environment variables for sensitive data**
6. **Encrypt service account keys in production environments**

## Troubleshooting

### Common Issues

#### 1. Authentication Error
```
Error: Failed to initialize Google Drive service: No JSON object could be decoded
```
**Solution**: Verify your `GOOGLE_DRIVE_SERVICE_ACCOUNT_INFO` is valid JSON.

#### 2. Permission Denied
```
Error: HttpError 403: Insufficient Permission
```
**Solution**: Ensure your service account has the necessary roles (Editor, Storage Admin).

#### 3. API Not Enabled
```
Error: Google Drive API has not been used in project
```
**Solution**: Enable the Google Drive API in the Google Cloud Console.

#### 4. Quota Exceeded
```
Error: Quota exceeded for quota metric 'Queries' and limit 'Queries per day'
```
**Solution**: Check your API usage in the GCP Console and request quota increases if needed.

### Debug Mode

Enable debug logging by setting:
```bash
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

This will provide detailed logs about Google Drive operations.

## API Endpoints

### Upload with Google Drive Integration
```http
POST /api/files/upload?google_drive=true&convert_to_doc=true&share_with_user=true
```

### Access Google Doc
```http
GET /api/files/{file_id}/google-doc?ensure_sharing=true
```

### List Files (includes Google Drive info)
```http
GET /api/files
```

## Folder Structure

The service will create the following folder structure in Google Drive:

```
Resume Modifier Files/
├── User_1/
│   ├── 2024-11-14/
│   │   ├── resume.pdf
│   │   └── resume (Google Doc)
│   └── 2024-11-15/
│       └── cover-letter.pdf
├── User_2/
│   └── 2024-11-14/
│       └── portfolio.pdf
└── ...
```

## Rate Limits and Quotas

Google Drive API has the following default limits:
- **Queries per day**: 1 billion
- **Queries per 100 seconds per user**: 1,000
- **Queries per 100 seconds**: 10,000

Monitor your usage in the [Google Cloud Console](https://console.cloud.google.com/apis/dashboard).

## Support

For issues specific to Google Drive integration:
1. Check the application logs
2. Verify your service account permissions
3. Test with a simple API call using Google's API Explorer
4. Consult the [Google Drive API documentation](https://developers.google.com/drive/api/v3/about-sdk)