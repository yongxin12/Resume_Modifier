# Custom Template API - Complete Guide

## What Are Custom Templates?

Custom templates allow you to convert your beautifully formatted Google Drive resume into a reusable template that can be applied to all your resumes. This ensures consistent styling, branding, and layout across your entire resume library.

## Quick Start

### 1. Get Your JWT Token

```bash
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@example.com",
    "password": "your_password"
  }'
```

Response includes:
```json
{
  "status": "success",
  "token": "YOUR_JWT_TOKEN",
  "user": {
    "id": 7,
    "email": "your.email@example.com"
  }
}
```

### 2. Analyze Your Google Drive Resume

Extract these details from your formatted resume:
- **Font family** (Arial, Calibri, Georgia, etc.)
- **Font sizes** (header and body)
- **Line spacing** (1.0, 1.15, 1.2, 1.3, etc.)
- **Color hex codes** for primary, secondary, text, and accent colors
- **Margins** (in inches)
- **Section order** (header, summary, experience, education, skills, etc.)

### 3. Create Your Template

```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "My Custom Resume Template",
    "description": "Professional template based on my Google Drive resume",
    "style_config": {
      "font_family": "Arial",
      "header_font_size": 14,
      "body_font_size": 11,
      "line_spacing": 1.15,
      "color_scheme": {
        "primary": "#1F4788",
        "secondary": "#4A90E2",
        "text": "#2C3E50",
        "accent": "#E8B724"
      },
      "margins": {
        "top": 0.75,
        "bottom": 0.75,
        "left": 0.75,
        "right": 0.75
      }
    },
    "sections": ["header", "summary", "experience", "education", "skills"]
  }'
```

### 4. Use Your Template

When creating or updating a resume, reference your custom template ID:

```bash
curl -X POST http://localhost:5001/api/resume/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "My Resume",
    "template_id": 4,
    "parsed_resume": {...resume data...}
  }'
```

## API Endpoints

### CREATE Template (POST)

**Endpoint:** `POST /api/templates`

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```json
{
  "name": "Template Name",
  "description": "Template description",
  "style_config": {
    "font_family": "Arial",
    "header_font_size": 14,
    "body_font_size": 11,
    "line_spacing": 1.15,
    "color_scheme": {
      "primary": "#1F4788",
      "secondary": "#4A90E2",
      "text": "#2C3E50",
      "accent": "#E8B724"
    },
    "margins": {
      "top": 0.75,
      "bottom": 0.75,
      "left": 0.75,
      "right": 0.75
    }
  },
  "sections": ["header", "summary", "experience", "education", "skills"]
}
```

**Response (201 Created):**
```json
{
  "status": 201,
  "data": {
    "id": 4,
    "name": "Template Name",
    "description": "Template description",
    "style_config": {...},
    "sections": [...],
    "created_at": "2025-10-17T01:09:03.949609"
  }
}
```

**Validation Rules:**
- `name`: Required, string, max 100 chars
- `description`: Required, string
- `style_config`: Required object with:
  - `font_family`: Required, string
  - `header_font_size`: Required, number (pt)
  - `body_font_size`: Required, number (pt)
  - `line_spacing`: Required, number (multiplier)
  - `color_scheme`: Required object with primary, secondary, text, accent (hex)
  - `margins`: Required object with top, bottom, left, right (inches)
- `sections`: Required, non-empty array of strings

---

### READ All Templates (GET)

**Endpoint:** `GET /api/templates`

**Authentication:** Optional

**Response (200 OK):**
```json
{
  "status": 200,
  "data": [
    {
      "id": 1,
      "name": "Professional Modern",
      "description": "Clean, modern design...",
      "style_config": {...},
      "sections": ["header", "summary", "experience", "education", "skills"],
      "created_at": "2024-01-01T00:00:00"
    },
    {...more templates...}
  ]
}
```

---

### READ Single Template (GET)

**Endpoint:** `GET /api/templates/<template_id>`

**Authentication:** Optional

**Parameters:**
- `template_id` (path): Template ID number

**Response (200 OK):**
```json
{
  "status": 200,
  "data": {
    "id": 4,
    "name": "My Custom Template",
    "description": "...",
    "style_config": {...},
    "sections": [...],
    "created_at": "2025-10-17T01:09:03.949609"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Template not found",
  "status": 404
}
```

---

### UPDATE Template (PUT)

**Endpoint:** `PUT /api/templates/<template_id>`

**Authentication:** Required (JWT Bearer token)

**Parameters:**
- `template_id` (path): Template ID to update

**Request Body (any/all fields):**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "style_config": {
    "font_family": "Calibri",
    "header_font_size": 16,
    "body_font_size": 11,
    "line_spacing": 1.2,
    "color_scheme": {
      "primary": "#E74C3C",
      "secondary": "#9B59B6",
      "text": "#2C3E50",
      "accent": "#F39C12"
    },
    "margins": {
      "top": 0.7,
      "bottom": 0.7,
      "left": 0.9,
      "right": 0.9
    }
  },
  "sections": ["header", "portfolio", "experience", "education", "skills"]
}
```

**Response (200 OK):**
```json
{
  "status": 200,
  "data": {
    "id": 4,
    "name": "Updated Name",
    "description": "Updated description",
    "style_config": {...},
    "sections": [...],
    "created_at": "2025-10-17T01:09:03.949609",
    "updated_at": "2025-10-17T01:09:13.697862"
  }
}
```

---

### DELETE Template (DELETE)

**Endpoint:** `DELETE /api/templates/<template_id>`

**Authentication:** Required (JWT Bearer token)

**Parameters:**
- `template_id` (path): Template ID to delete

**Response (200 OK):**
```json
{
  "status": 200,
  "message": "Template deleted successfully"
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Template not found",
  "status": 404
}
```

**Note:** Templates are soft-deleted (marked as inactive) and can still be referenced by existing resumes.

---

## Field Reference

### Font Families

**Professional:**
- Arial
- Calibri
- Times New Roman

**Modern:**
- Segoe UI
- Georgia
- Garamond

**Monospace (for code):**
- Courier New
- Inconsolata

### Font Sizes (Points)

| Category | Size Range |
|----------|-----------|
| Headers | 12-18 pt |
| Body | 10-12 pt |
| Subheaders | 11-14 pt |

### Line Spacing Values

| Type | Value |
|------|-------|
| Compact | 1.0 |
| Default | 1.15 |
| Spaced | 1.2-1.3 |
| Double | 1.5-2.0 |

### Color Scheme Guidelines

**Corporate/Professional:**
- Primary: `#1F4788` (dark blue)
- Secondary: `#4A90E2` (light blue)
- Text: `#2C3E50` (dark gray)
- Accent: `#E8B724` (gold)

**Creative/Modern:**
- Primary: `#E74C3C` (red)
- Secondary: `#9B59B6` (purple)
- Text: `#2C3E50` (dark gray)
- Accent: `#F39C12` (orange)

**Executive/Classic:**
- Primary: `#1B4332` (dark green)
- Secondary: `#2D6A4F` (green)
- Text: `#000000` (black)
- Accent: `#B7E4C7` (light green)

**Tech/Startup:**
- Primary: `#0052CC` (blue)
- Secondary: `#0079BF` (light blue)
- Text: `#172B4D` (dark blue-gray)
- Accent: `#00875A` (green)

### Margin Guidelines

| Type | Size |
|------|------|
| Tight | 0.5-0.75" |
| Standard | 0.75-1.0" |
| Spacious | 1.0-1.25" |
| Formal | 1.0-1.5" |

### Standard Section Names

| Section | Usage |
|---------|-------|
| `header` | Name and contact info |
| `summary` | Professional summary |
| `executive_summary` | Executive-level summary |
| `experience` | Work experience |
| `education` | Education and degrees |
| `skills` | Technical skills |
| `certifications` | Certifications/licenses |
| `portfolio` | Portfolio links |
| `projects` | Project descriptions |
| `board_positions` | Board memberships |
| `achievements` | Notable achievements |
| `volunteer` | Volunteer work |
| `languages` | Language proficiencies |
| `publications` | Published works |
| `technical` | Additional technical details |

---

## Error Handling

### 400 Bad Request

**Missing Required Field:**
```json
{
  "error": "Missing required field: name",
  "status": 400
}
```

**Invalid Request Data:**
```json
{
  "error": "sections must be a list",
  "status": 400
}
```

**Empty Sections:**
```json
{
  "error": "sections list cannot be empty",
  "status": 400
}
```

### 401 Unauthorized

**Missing Token:**
```json
{
  "error": "Authorization token required",
  "status": 401
}
```

**Invalid Token:**
```json
{
  "error": "Invalid or expired token",
  "status": 401
}
```

### 404 Not Found

**Template doesn't exist:**
```json
{
  "error": "Template not found",
  "status": 404
}
```

### 500 Server Error

**Creation failed:**
```json
{
  "error": "Failed to create template",
  "details": "Database error details...",
  "status": 500
}
```

---

## Complete Examples

### Example 1: Creating a Professional Tech Template

```bash
# Step 1: Login
LOGIN=$(curl -s -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "dev@example.com",
    "password": "pass123"
  }')

TOKEN=$(echo $LOGIN | jq -r '.token')

# Step 2: Create template
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Tech Professional",
    "description": "Clean template for tech professionals with modern styling",
    "style_config": {
      "font_family": "Segoe UI",
      "header_font_size": 14,
      "body_font_size": 11,
      "line_spacing": 1.2,
      "color_scheme": {
        "primary": "#0052CC",
        "secondary": "#0079BF",
        "text": "#172B4D",
        "accent": "#00875A"
      },
      "margins": {
        "top": 0.75,
        "bottom": 0.75,
        "left": 0.75,
        "right": 0.75
      }
    },
    "sections": ["header", "summary", "experience", "education", "skills", "projects"]
  }'
```

### Example 2: Updating Template Colors

```bash
curl -X PUT http://localhost:5001/api/templates/4 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "style_config": {
      "font_family": "Segoe UI",
      "header_font_size": 14,
      "body_font_size": 11,
      "line_spacing": 1.2,
      "color_scheme": {
        "primary": "#E74C3C",
        "secondary": "#9B59B6",
        "text": "#2C3E50",
        "accent": "#F39C12"
      },
      "margins": {
        "top": 0.75,
        "bottom": 0.75,
        "left": 0.75,
        "right": 0.75
      }
    }
  }'
```

### Example 3: List All Templates

```bash
curl -X GET http://localhost:5001/api/templates
```

### Example 4: Delete a Template

```bash
curl -X DELETE http://localhost:5001/api/templates/4 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Best Practices

### 1. **Name Your Templates Clearly**
- ✅ "Tech Professional" 
- ✅ "Executive Classic"
- ✅ "Creative Designer - 2024"
- ❌ "Template1"
- ❌ "My Stuff"

### 2. **Provide Detailed Descriptions**
- Include target roles/industries
- Mention key features
- Explain when to use it

### 3. **Test Before Production**
- Create template
- Apply to test resume
- Review output
- Update if needed

### 4. **Color Harmony**
- Use online tools like [coolors.co](https://coolors.co/)
- Ensure good contrast for text readability
- Test on printed resume too

### 5. **Consistent Sections**
- Use standard section names when possible
- Order sections logically
- Include at least: header, experience, education, skills

### 6. **Font Pairing**
- Don't use too many different fonts
- Stick to 1-2 professional font families
- Ensure fonts are widely available

---

## Troubleshooting

### "Authorization token required"
- Ensure you've logged in and obtained a valid JWT
- Check token format: `Bearer YOUR_TOKEN_HERE`
- Verify token hasn't expired

### "Missing required field"
- Check all required fields are present in request
- Ensure values are correct types (numbers, strings, objects)
- Validate JSON formatting

### "sections list cannot be empty"
- Add at least one section
- Valid sections: header, summary, experience, education, skills, etc.

### "Invalid hex color code"
- Use format: `#RRGGBB` (e.g., `#1F4788`)
- Not: `blue`, `rgb()`, `hsl()`, etc.
- Validate at [colorhexa.com](https://www.colorhexa.com/)

### Template not applying to resume
- Verify template ID is correct
- Check template is marked as active
- Ensure resume references correct template_id

---

## Integration with Resume Export

Once you've created a custom template, you can use it when exporting resumes:

### Export to Google Docs with Template

```bash
curl -X POST http://localhost:5001/api/resume/export/gdocs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "resume_id": 1,
    "template_id": 4,
    "document_title": "My_Resume_2024"
  }'
```

Response will include:
- `document_id`: Google Docs document ID
- `shareable_url`: Link to shared document
- `generated_document_id`: Reference in our database

---

## Related Endpoints

- `POST /api/login` - Get JWT token
- `POST /api/register` - Create user account
- `GET /api/templates/seed` - Seed default templates (admin)
- `POST /api/resume/export/gdocs` - Export resume with template
- `GET /api/resumes` - List your resumes

---

## Support

For more information, see:
- [CUSTOM_TEMPLATE_GUIDE.md](./CUSTOM_TEMPLATE_GUIDE.md) - Detailed guide to creating templates
- [TEMPLATE_EXAMPLES.md](./TEMPLATE_EXAMPLES.md) - Real-world examples with code
- [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) - Full API reference
