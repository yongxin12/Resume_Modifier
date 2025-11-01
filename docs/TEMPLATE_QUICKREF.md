# Custom Template Quick Reference

## Summary

Convert your beautiful Google Drive resume into a reusable template in 3 steps!

## Prerequisites

✅ Logged into Resume Editor  
✅ JWT Token (from login endpoint)  
✅ Your formatted resume analyzed

---

## Step 1: Get JWT Token

```bash
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "password"}'

# Response contains:
# "token": "YOUR_JWT_TOKEN"
```

**Save the token!** Use it in next steps.

---

## Step 2: Analyze Your Resume

Gather from your Google Drive resume:

| Property | Example | Where to Find |
|----------|---------|---------------|
| Font Family | Arial | Format → Font |
| Header Size | 14 pt | Select header → Format → Font size |
| Body Size | 11 pt | Select body → Format → Font size |
| Line Spacing | 1.15 | Format → Line spacing |
| Primary Color | #1F4788 | Right-click text → Inspect → look for color |
| Secondary Color | #4A90E2 | Same as above |
| Text Color | #2C3E50 | Same as above |
| Accent Color | #E8B724 | Same as above |
| Margins | 0.75" | File → Page setup |
| Sections | header, summary, experience, education, skills | List headers in order |

---

## Step 3: Create Template

### Minimal Request

```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN_HERE" \
  -d '{
    "name": "My Template Name",
    "description": "Brief description",
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

### Response

```json
{
  "status": 201,
  "data": {
    "id": 4,
    "name": "My Template Name",
    ...
  }
}
```

**Save the `id`!** Use it when creating resumes.

---

## Common Colors

### Professional
- Primary: `#1F4788` (Dark Blue)
- Text: `#2C3E50` (Gray-Blue)
- Accent: `#E8B724` (Gold)

### Creative
- Primary: `#E74C3C` (Red)
- Secondary: `#9B59B6` (Purple)
- Accent: `#F39C12` (Orange)

### Tech
- Primary: `#0052CC` (Blue)
- Secondary: `#0079BF` (Light Blue)
- Accent: `#00875A` (Green)

### Executive
- Primary: `#1B4332` (Dark Green)
- Text: `#000000` (Black)
- Accent: `#B7E4C7` (Light Green)

---

## Common Font Sizes

| Type | Size |
|------|------|
| Large Headers | 16-18 pt |
| Standard Headers | 14 pt |
| Subheaders | 12 pt |
| Body Text | 11 pt |
| Small Text | 10 pt |

---

## Standard Sections

```json
[
  "header",
  "summary",
  "experience", 
  "education",
  "skills",
  "certifications"
]
```

**Or with portfolio:**
```json
[
  "header",
  "summary",
  "portfolio",
  "experience",
  "education",
  "skills",
  "projects"
]
```

**Or for executives:**
```json
[
  "header",
  "executive_summary",
  "experience",
  "education",
  "board_positions",
  "achievements"
]
```

---

## Other Operations

### View Your Template
```bash
curl -X GET http://localhost:5001/api/templates/4 \
  -H "Authorization: Bearer TOKEN"
```

### List All Templates
```bash
curl -X GET http://localhost:5001/api/templates
```

### Update Template
```bash
curl -X PUT http://localhost:5001/api/templates/4 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"description": "New description"}'
```

### Delete Template
```bash
curl -X DELETE http://localhost:5001/api/templates/4 \
  -H "Authorization: Bearer TOKEN"
```

---

## Validation Rules

### ✅ Valid
- name: Non-empty string
- font_family: "Arial", "Calibri", "Times New Roman", etc.
- sizes: Numbers (10, 11, 14, 16, etc.)
- spacing: Numbers (1.0, 1.15, 1.2, 1.3, etc.)
- colors: Hex format `#RRGGBB` (e.g., `#1F4788`)
- margins: Numbers in inches (0.5, 0.75, 1.0, etc.)
- sections: Array with at least 1 element

### ❌ Invalid
- colors: `blue`, `rgb(31, 71, 136)`, `hsl(...)` 
- sizes: `"14pt"`, `"14px"` (numbers only!)
- margins: `"0.75"` as string (must be number!)
- sections: `[]` empty array
- spacing: `1` without decimal

---

## Error Messages

| Error | Fix |
|-------|-----|
| "Missing required field" | Check all fields are present |
| "sections must be a list" | Use `"sections": [...]` |
| "Invalid hex color code" | Use format `#RRGGBB` |
| "Authorization token required" | Add Authorization header |
| "Template not found" | Check template ID is correct |

---

## Getting Hex Colors

### Method 1: Chrome DevTools
1. Right-click colored text in Google Docs
2. Click "Inspect"
3. Find `color:` property in HTML
4. Copy hex code

### Method 2: Color Picker Tool
1. Install browser extension
2. Click on colored text
3. See hex code

### Method 3: Screenshot Method
1. Screenshot your resume
2. Go to [colorhexa.com](https://www.colorhexa.com/)
3. Upload image
4. Click on colors to get hex codes

---

## Template Naming Tips

Good names:
- "Professional Modern Tech"
- "Creative Designer 2024"  
- "Executive Consulting"
- "Academic Researcher"

Bad names:
- "Template1"
- "My Resume"
- "Draft"
- "New"

---

## Next Steps

1. ✅ Extract details from your resume
2. ✅ Create template using API
3. 📝 Note the template ID
4. 📄 Use it when creating/exporting resumes
5. 🔄 Update if needed
6. 📤 Share with colleagues

---

## Full Documentation

For more details, see:
- [CUSTOM_TEMPLATE_GUIDE.md](./CUSTOM_TEMPLATE_GUIDE.md) - Complete guide
- [TEMPLATE_EXAMPLES.md](./TEMPLATE_EXAMPLES.md) - Real examples
- [CUSTOM_TEMPLATE_API.md](./CUSTOM_TEMPLATE_API.md) - API reference

---

## Support

Need help? Check:
- **API errors?** → See CUSTOM_TEMPLATE_API.md Error Handling section
- **Can't find colors?** → Use color picker online
- **Wrong format?** → Copy-paste from examples above
- **Template not working?** → Verify all required fields

---

**Happy templating!** 🎉
