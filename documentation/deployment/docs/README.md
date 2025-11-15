# 📄 Custom Resume Templates - Complete Feature Documentation

## Overview

Your Resume Editor now fully supports creating, managing, and applying **custom resume templates** from your existing formatted Google Drive resumes.

This feature enables you to:
- Convert your beautifully formatted resume into a reusable template
- Maintain consistent styling across all your resumes
- Create role-specific or industry-specific templates
- Share templates with team members
- Apply professional templates to future resumes instantly

---

## 📚 Documentation Files

| File | Purpose | Best For |
|------|---------|----------|
| **[TEMPLATE_QUICKREF.md](./TEMPLATE_QUICKREF.md)** | Quick reference card with copy-paste examples | Getting started fast |
| **[CUSTOM_TEMPLATE_GUIDE.md](./CUSTOM_TEMPLATE_GUIDE.md)** | Complete extraction and creation guide | Understanding templates deeply |
| **[TEMPLATE_EXAMPLES.md](./TEMPLATE_EXAMPLES.md)** | 5 real-world examples with full JSON | Learning by example |
| **[CUSTOM_TEMPLATE_API.md](./CUSTOM_TEMPLATE_API.md)** | Complete API endpoint documentation | Developers/advanced users |
| **[TEMPLATE_SUMMARY.md](./TEMPLATE_SUMMARY.md)** | Executive summary of the feature | Overview and navigation |

---

## 🚀 Quick Start

### Step 1: Get JWT Token (Required)

```bash
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "password"}'
```

**Response contains `token` field** - save this!

### Step 2: Extract Formatting from Your Google Drive Resume

Note these details:
```
Font Family:        Arial
Header Size:        14 pt
Body Size:          11 pt
Line Spacing:       1.15
Primary Color:      #1F4788 (dark blue)
Secondary Color:    #4A90E2 (light blue)
Text Color:         #2C3E50 (gray-blue)
Accent Color:       #E8B724 (gold)
Margins:            0.75" all around
Sections (in order): header, summary, experience, education, skills
```

### Step 3: Create Template

```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "My Professional Template",
    "description": "Clean professional template based on my formatted resume",
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

**Response includes `"id": 4`** - your template ID!

### Step 4: Use Your Template

When creating or exporting resumes, reference your template ID:

```bash
curl -X POST http://localhost:5001/api/resume/export/gdocs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "resume_id": 1,
    "template_id": 4,
    "document_title": "My_Resume"
  }'
```

---

## 🎨 Template Structure

All templates consist of:

### Metadata
- **name**: Template name (required, string)
- **description**: What it's for (required, string)

### Style Configuration
```json
"style_config": {
  "font_family": "Arial",           // Font name
  "header_font_size": 14,           // Points
  "body_font_size": 11,             // Points
  "line_spacing": 1.15,             // Multiplier
  "color_scheme": {
    "primary": "#1F4788",           // Main header color
    "secondary": "#4A90E2",         // Alternative color
    "text": "#2C3E50",              // Body text
    "accent": "#E8B724"             // Highlights
  },
  "margins": {
    "top": 0.75,                    // Inches
    "bottom": 0.75,
    "left": 0.75,
    "right": 0.75
  }
}
```

### Sections
```json
"sections": [
  "header",           // Name and contact
  "summary",          // Professional summary
  "experience",       // Work history
  "education",        // Degrees
  "skills",           // Technical skills
  "certifications"    // Licenses/certs
]
```

---

## 📋 Available Endpoints

### Create Template
```
POST /api/templates
```
- **Required:** JWT token
- **Returns:** Template with ID

### List All Templates
```
GET /api/templates
```
- **Optional:** JWT token (anyone can view)
- **Returns:** Array of all templates

### Get Single Template
```
GET /api/templates/<id>
```
- **Optional:** JWT token
- **Returns:** Specific template

### Update Template
```
PUT /api/templates/<id>
```
- **Required:** JWT token
- **Returns:** Updated template

### Delete Template
```
DELETE /api/templates/<id>
```
- **Required:** JWT token
- **Returns:** Success message

---

## 🎨 Template Recipes

### Professional Corporate
**For:** Finance, law, management
```json
{
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
  "margins": {"top": 0.75, "bottom": 0.75, "left": 0.75, "right": 0.75},
  "sections": ["header", "summary", "experience", "education", "skills"]
}
```

### Creative Design
**For:** Design, marketing, creative roles
```json
{
  "font_family": "Calibri",
  "header_font_size": 18,
  "body_font_size": 11,
  "line_spacing": 1.3,
  "color_scheme": {
    "primary": "#E74C3C",
    "secondary": "#9B59B6",
    "text": "#2C3E50",
    "accent": "#F39C12"
  },
  "margins": {"top": 0.7, "bottom": 0.7, "left": 0.9, "right": 0.9},
  "sections": ["header", "summary", "portfolio", "experience", "education", "skills", "projects"]
}
```

### Tech Startup
**For:** Engineering, tech, startups
```json
{
  "font_family": "Segoe UI",
  "header_font_size": 16,
  "body_font_size": 10,
  "line_spacing": 1.2,
  "color_scheme": {
    "primary": "#0052CC",
    "secondary": "#0079BF",
    "text": "#172B4D",
    "accent": "#00875A"
  },
  "margins": {"top": 0.6, "bottom": 0.6, "left": 0.6, "right": 0.6},
  "sections": ["header", "summary", "experience", "education", "skills", "projects"]
}
```

### Executive Classic
**For:** C-suite, executives, senior roles
```json
{
  "font_family": "Times New Roman",
  "header_font_size": 14,
  "body_font_size": 10,
  "line_spacing": 1.1,
  "color_scheme": {
    "primary": "#1B4332",
    "secondary": "#2D6A4F",
    "text": "#000000",
    "accent": "#B7E4C7"
  },
  "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
  "sections": ["header", "executive_summary", "experience", "education", "board_positions", "achievements"]
}
```

---

## 🔍 How to Extract Your Resume Formatting

### Extract Font
In Google Docs:
1. Select text
2. Look at Format → Font dropdown
3. Note the name (Arial, Calibri, etc.)

### Extract Font Sizes
In Google Docs:
1. Select header text
2. Look at Format → Font size
3. Note the size (e.g., 14pt)
4. Repeat for body text

### Extract Colors
**Method 1: Chrome DevTools**
1. Right-click colored text in Google Docs
2. Click "Inspect"
3. Find `color:` or `fill:` property
4. Copy hex code (e.g., #1F4788)

**Method 2: Color Picker Tool**
1. Install browser extension (ColorZilla, ColorPicker)
2. Click on colored text
3. See hex code appear

**Method 3: Screenshot + Online Tool**
1. Screenshot your resume
2. Go to [colorhexa.com](https://www.colorhexa.com/)
3. Upload image
4. Click on colors to get hex codes

### Extract Margins
In Google Docs:
1. Go to File → Page setup
2. Note margins: top, bottom, left, right (in inches)

### Extract Line Spacing
In Google Docs:
1. Select text
2. Go to Format → Line spacing
3. Note value (1.0, 1.15, 1.2, 1.3, 2.0, etc.)

### List Sections
1. Read through resume from top to bottom
2. Write down each section header
3. Use standard names: header, summary, experience, education, skills, certifications, etc.

---

## ✅ Validation Rules

### All Required
- `name`: Non-empty string
- `description`: Non-empty string  
- `style_config`: Object with all sub-fields
- `sections`: Non-empty array

### Font Family
Any standard font name: Arial, Calibri, Times New Roman, Segoe UI, Georgia, etc.

### Font Sizes
Numbers only (no "pt" or "px"): 10, 11, 12, 14, 16, 18

### Line Spacing
Numbers only: 1.0, 1.15, 1.2, 1.3, 1.5, 2.0

### Colors
Hex format only: #RRGGBB (e.g., #1F4788)
- NOT: blue, rgb(), hsl()
- NOT: #RGB (must be 6 digits)

### Margins
Numbers only in inches: 0.5, 0.75, 1.0, 1.25, 1.5

### Sections
- Must be array: `["header", "summary", ...]`
- Must have at least 1 item
- Use standard names when possible

---

## 🐛 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "Authorization token required" | Login first, get token from response |
| "Missing required field: name" | Add all 4 required fields: name, description, style_config, sections |
| "Invalid hex color code" | Use format #RRGGBB, e.g., #1F4788 |
| "sections list cannot be empty" | Add at least one section to array |
| "Template not found" | Check template ID is correct |
| "Token expired" | Login again to get fresh token |
| "sections must be a list" | Use square brackets: ["header", "summary"] |

---

## 📊 Built-in Templates

System includes 3 default templates:

### 1. Professional Modern (ID: 1)
- For corporate, finance, management
- Blue color scheme
- Standard section layout

### 2. Creative Designer (ID: 2)  
- For design, marketing, creative
- Red/purple color scheme
- Includes portfolio section

### 3. Executive Classic (ID: 3)
- For executives, senior roles
- Green color scheme
- Formal layout

**View all:** `GET /api/templates`

---

## 💡 Best Practices

### 1. Naming
✅ "Professional Modern Custom"  
✅ "Tech Startup 2024"  
❌ "Template1"  
❌ "My Stuff"

### 2. Color Choice
- Use online tool [coolors.co](https://coolors.co/)
- Ensure good contrast (4.5:1 minimum)
- Stick to 3-4 colors max

### 3. Font Selection
- Professional: Arial, Calibri, Times New Roman
- Modern: Segoe UI, Georgia
- Use same font throughout body text

### 4. Font Sizing
- Headers: 14-16pt
- Body: 10-11pt
- Ratio: header ÷ body ≈ 1.3-1.5

### 5. Margins
- Tight: 0.5-0.75" (fits content)
- Standard: 0.75-1.0" (most common)
- Spacious: 1.0-1.25" (premium)

### 6. Testing
1. Create template
2. Apply to test resume
3. Review output
4. Update if needed
5. Deploy to other resumes

---

## 📖 Documentation by Use Case

### "I want to create a template from my resume"
→ Start with [TEMPLATE_QUICKREF.md](./TEMPLATE_QUICKREF.md)

### "I need detailed instructions"
→ Read [CUSTOM_TEMPLATE_GUIDE.md](./CUSTOM_TEMPLATE_GUIDE.md)

### "Show me examples"
→ See [TEMPLATE_EXAMPLES.md](./TEMPLATE_EXAMPLES.md)

### "I need API documentation"
→ Check [CUSTOM_TEMPLATE_API.md](./CUSTOM_TEMPLATE_API.md)

### "Give me the overview"
→ Read [TEMPLATE_SUMMARY.md](./TEMPLATE_SUMMARY.md)

---

## 🔗 Integration Points

### Resume Creation
When creating a new resume, reference your template:
```bash
POST /api/resume/create
{
  "title": "My Resume",
  "template_id": 4,
  "parsed_resume": {...}
}
```

### Resume Export
When exporting to Google Docs, apply your template:
```bash
POST /api/resume/export/gdocs
{
  "resume_id": 1,
  "template_id": 4,
  "document_title": "My_Resume"
}
```

### Resume Analysis
Compare resume against job descriptions (template optional):
```bash
POST /api/job_description_upload
{
  "updated_resume": {...},
  "job_description": "..."
}
```

---

## 🎯 Use Cases

| Use Case | Solution |
|----------|----------|
| Consistent personal branding | Create 1 custom template, use for all resumes |
| Industry-specific formatting | Create multiple templates for different industries |
| Different roles | Create templates for senior vs. junior positions |
| Team consistency | Create company template, share ID with team |
| Client proposals | Create client-branded template |
| Portfolio version | Create portfolio-focused template variant |

---

## 📈 Feature Status

✅ **Implemented & Working:**
- Create custom templates
- View all templates
- View specific template
- Update template properties
- Delete templates
- Full API documentation
- Example templates
- Validation and error handling

🔄 **Future Enhancements:**
- Template preview generation
- Template sharing between users
- Template versioning
- Analytics on template usage
- Template recommendations

---

## 🆘 Support & Troubleshooting

### Quick Help
See [TEMPLATE_QUICKREF.md](./TEMPLATE_QUICKREF.md) for common questions

### Detailed Help  
Check [CUSTOM_TEMPLATE_GUIDE.md](./CUSTOM_TEMPLATE_GUIDE.md) FAQ section

### API Issues
Review [CUSTOM_TEMPLATE_API.md](./CUSTOM_TEMPLATE_API.md) error handling

### Examples
View [TEMPLATE_EXAMPLES.md](./TEMPLATE_EXAMPLES.md) for working code

---

## 🎉 Get Started!

1. Read [TEMPLATE_QUICKREF.md](./TEMPLATE_QUICKREF.md) (5 min)
2. Extract your resume details (10 min)
3. Create your first template (5 min)
4. Apply to your resume (2 min)
5. **Enjoy consistent styling!** ✨

**Next Step:** Open [TEMPLATE_QUICKREF.md](./TEMPLATE_QUICKREF.md) →

---

## 📞 Questions?

- **How do I extract colors?** → See CUSTOM_TEMPLATE_GUIDE.md § "Tips"
- **Can I use custom fonts?** → Yes! Any standard font works
- **How many templates can I create?** → Unlimited!
- **Can I share templates?** → Yes, share template ID
- **Can I modify after creating?** → Yes, use PUT endpoint

**Happy templating!** 🚀
