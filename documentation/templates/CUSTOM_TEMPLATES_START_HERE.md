# 🚀 Custom Resume Templates - START HERE

## What Is This?

You can now convert your beautifully formatted Google Drive resume into a **reusable template** that applies to all your resumes!

## Quick Demo (2 minutes)

```bash
# 1. Login and get token
TOKEN=$(curl -s -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass"}' | jq -r '.token')

# 2. Create your template
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "My Professional Template",
    "description": "My custom resume template",
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
      "margins": {"top": 0.75, "bottom": 0.75, "left": 0.75, "right": 0.75}
    },
    "sections": ["header", "summary", "experience", "education", "skills"]
  }'

# 3. Save the template ID from response
# 4. Use it when exporting resumes!
```

## 📚 Documentation

Choose your path based on how much time you have:

### ⏱️ I have 5 minutes
→ Read **[TEMPLATE_QUICKREF.md](./docs/TEMPLATE_QUICKREF.md)**
- One-page reference card
- Copy-paste examples
- Common colors

### ⏱️ I have 10 minutes  
→ Read **[README.md](./docs/README.md)** in docs folder
- Complete feature overview
- All endpoints explained
- Troubleshooting

### ⏱️ I have 15 minutes
→ Read **[CUSTOM_TEMPLATE_GUIDE.md](./docs/CUSTOM_TEMPLATE_GUIDE.md)**
- How to extract formatting
- Complete structure guide
- Best practices
- FAQ

### ⏱️ I want examples
→ Check **[TEMPLATE_EXAMPLES.md](./docs/TEMPLATE_EXAMPLES.md)**
- 5 real-world templates
- Professional, creative, tech
- Full JSON examples

### ⏱️ I need API reference
→ See **[CUSTOM_TEMPLATE_API.md](./docs/CUSTOM_TEMPLATE_API.md)**
- All endpoints documented
- Request/response formats
- Error handling

## 🎯 3-Step Process

### Step 1: Extract Your Resume
Open your Google Drive resume and note:
```
Font:          Arial
Header Size:   14 pt
Body Size:     11 pt
Spacing:       1.15
Primary Color: #1F4788
Margins:       0.75" all around
Sections:      header, summary, experience, education, skills
```

### Step 2: Login & Create Template
```bash
# Login (save the token!)
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Create template (use the token from above)
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN_HERE" \
  -d '{ ...template JSON... }'
```

Get the template ID from response: `"id": 4`

### Step 3: Use Your Template
When exporting resumes, reference your template:
```bash
curl -X POST http://localhost:5001/api/resume/export/gdocs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"resume_id": 1, "template_id": 4, "document_title": "My_Resume"}'
```

## 📖 All Available Endpoints

```
POST   /api/templates           - Create new template
GET    /api/templates           - List all templates
GET    /api/templates/<id>      - Get specific template
PUT    /api/templates/<id>      - Update template
DELETE /api/templates/<id>      - Delete template
```

## 🎨 Quick Templates

### Professional (Corporate)
```json
{
  "font_family": "Arial",
  "header_font_size": 14,
  "color_scheme": {
    "primary": "#1F4788",
    "secondary": "#4A90E2",
    "text": "#2C3E50",
    "accent": "#E8B724"
  }
}
```

### Creative (Design)
```json
{
  "font_family": "Calibri",
  "header_font_size": 18,
  "color_scheme": {
    "primary": "#E74C3C",
    "secondary": "#9B59B6",
    "text": "#2C3E50",
    "accent": "#F39C12"
  }
}
```

### Tech (Startup)
```json
{
  "font_family": "Segoe UI",
  "header_font_size": 16,
  "color_scheme": {
    "primary": "#0052CC",
    "secondary": "#0079BF",
    "text": "#172B4D",
    "accent": "#00875A"
  }
}
```

### Executive (Senior)
```json
{
  "font_family": "Times New Roman",
  "header_font_size": 14,
  "color_scheme": {
    "primary": "#1B4332",
    "secondary": "#2D6A4F",
    "text": "#000000",
    "accent": "#B7E4C7"
  }
}
```

## ✅ What You Can Do

- ✅ Create unlimited templates
- ✅ Customize fonts, colors, spacing
- ✅ Define resume sections
- ✅ Apply to multiple resumes
- ✅ Update templates anytime
- ✅ Delete unused templates
- ✅ View all templates

## 🆘 Common Questions

**Q: How do I get hex color codes?**
A: Right-click text in Google Docs → Inspect → find color property, or use online tools like colorhexa.com

**Q: Can I use any font?**
A: Yes! Arial, Calibri, Georgia, Segoe UI, Times New Roman - any standard font works

**Q: How many templates can I create?**
A: Unlimited! Create as many as you need

**Q: Can I share templates?**
A: Yes! Share the template ID with teammates

**Q: Do I need to update templates?**
A: Only if you want to change the design

**Q: What if I delete a template?**
A: It's soft-deleted. Existing resumes still work, but won't appear in new selections

## 📋 Files Overview

| File | Purpose | Time |
|------|---------|------|
| **This file** | Quick intro and next steps | 2 min |
| [README.md](./docs/README.md) | Complete feature overview | 10 min |
| [TEMPLATE_QUICKREF.md](./docs/TEMPLATE_QUICKREF.md) | One-page reference | 5 min |
| [CUSTOM_TEMPLATE_GUIDE.md](./docs/CUSTOM_TEMPLATE_GUIDE.md) | Detailed guide | 15 min |
| [TEMPLATE_EXAMPLES.md](./docs/TEMPLATE_EXAMPLES.md) | Real examples | 15 min |
| [CUSTOM_TEMPLATE_API.md](./docs/CUSTOM_TEMPLATE_API.md) | API reference | 20 min |
| [TEMPLATE_SUMMARY.md](./docs/TEMPLATE_SUMMARY.md) | Feature summary | 10 min |

## 🚀 Ready to Start?

1. Choose a documentation file above based on your time
2. Extract details from your Google Drive resume
3. Create your first template using the API
4. Apply it to a resume
5. Enjoy consistent formatting!

## 💡 Pro Tip

Start with **[TEMPLATE_QUICKREF.md](./docs/TEMPLATE_QUICKREF.md)** - it has everything you need in 5 minutes!

---

**Questions?** Check [README.md](./docs/README.md) for the full guide.

**Ready to create?** Head to [TEMPLATE_QUICKREF.md](./docs/TEMPLATE_QUICKREF.md) →

Happy templating! 🎉
