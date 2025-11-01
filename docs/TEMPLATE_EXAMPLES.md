# Custom Template Creation Examples

## Overview
This document provides practical examples for converting your existing Google Drive resume into a custom template.

## Example 1: Professional Modern Template

### Your Google Drive Resume Formatting:
- Font: Arial
- Header Size: 14pt
- Body Size: 11pt  
- Line Spacing: 1.15
- Header Color: Dark Blue (#1F4788)
- Accent Color: Orange (#E8B724)
- Margins: 0.75" all around
- Sections: Header, Summary, Experience, Education, Skills

### API Request to Create Template:

```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Professional Modern Custom",
    "description": "Clean professional template with dark blue headers and orange accents, perfect for corporate roles",
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

### Expected Response:
```json
{
  "status": 201,
  "data": {
    "id": 4,
    "name": "Professional Modern Custom",
    "description": "Clean professional template with dark blue headers and orange accents, perfect for corporate roles",
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
    "sections": ["header", "summary", "experience", "education", "skills"],
    "created_at": "2024-01-15T10:30:45"
  }
}
```

## Example 2: Creative Designer Template

### Your Google Drive Resume Formatting:
- Font: Calibri
- Header Size: 18pt
- Body Size: 11pt
- Line Spacing: 1.3
- Header Color: Red (#E74C3C)
- Secondary Color: Purple (#9B59B6)
- Text Color: Dark Gray (#2C3E50)
- Accent Color: Orange (#F39C12)
- Margins: 0.7" top/bottom, 0.9" left/right
- Sections: Header, Summary, Portfolio, Experience, Education, Skills, Projects

### API Request:

```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Creative Designer Custom",
    "description": "Eye-catching design template with red headers and purple accents, perfect for creative and design roles",
    "style_config": {
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
      "margins": {
        "top": 0.7,
        "bottom": 0.7,
        "left": 0.9,
        "right": 0.9
      }
    },
    "sections": ["header", "summary", "portfolio", "experience", "education", "skills", "projects"]
  }'
```

## Example 3: Executive Classic Template

### Your Google Drive Resume Formatting:
- Font: Times New Roman
- Header Size: 14pt
- Body Size: 10pt
- Line Spacing: 1.1
- Header Color: Dark Green (#1B4332)
- Secondary Color: Green (#2D6A4F)
- Text Color: Black (#000000)
- Accent Color: Light Green (#B7E4C7)
- Margins: 1.0" all around
- Sections: Header, Executive Summary, Experience, Education, Board Positions, Achievements

### API Request:

```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Executive Classic Custom",
    "description": "Sophisticated traditional template with green accents, ideal for executive and senior-level positions",
    "style_config": {
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
      "margins": {
        "top": 1.0,
        "bottom": 1.0,
        "left": 1.0,
        "right": 1.0
      }
    },
    "sections": ["header", "executive_summary", "experience", "education", "board_positions", "achievements"]
  }'
```

## Example 4: Tech Startup Template

### Your Google Drive Resume Formatting:
- Font: Segoe UI (modern)
- Header Size: 16pt
- Body Size: 10pt
- Line Spacing: 1.2
- Header Color: Dark Blue (#0052CC)
- Secondary Color: Light Blue (#0079BF)
- Text Color: Dark Gray (#172B4D)
- Accent Color: Cyan (#00875A)
- Margins: 0.6" all around (compact)
- Sections: Header, Summary, Experience, Education, Skills, Projects, Technical

### API Request:

```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Tech Startup",
    "description": "Modern tech template with compact layout, perfect for software engineers and tech roles",
    "style_config": {
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
      "margins": {
        "top": 0.6,
        "bottom": 0.6,
        "left": 0.6,
        "right": 0.6
      }
    },
    "sections": ["header", "summary", "experience", "education", "skills", "projects", "technical"]
  }'
```

## Example 5: Academic Researcher Template

### Your Google Drive Resume Formatting:
- Font: Georgia (scholarly)
- Header Size: 12pt (conservative)
- Body Size: 10pt
- Line Spacing: 1.0 (compact for academic style)
- Header Color: Navy (#000080)
- Secondary Color: Dark Gray (#404040)
- Text Color: Black (#000000)
- Accent Color: Dark Red (#8B0000)
- Margins: 1.0" all around (formal)
- Sections: Header, Academic Summary, Education, Research Experience, Publications, Presentations, Awards

### API Request:

```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Academic Researcher",
    "description": "Conservative academic template with Georgia font, designed for researchers and academic professionals",
    "style_config": {
      "font_family": "Georgia",
      "header_font_size": 12,
      "body_font_size": 10,
      "line_spacing": 1.0,
      "color_scheme": {
        "primary": "#000080",
        "secondary": "#404040",
        "text": "#000000",
        "accent": "#8B0000"
      },
      "margins": {
        "top": 1.0,
        "bottom": 1.0,
        "left": 1.0,
        "right": 1.0
      }
    },
    "sections": ["header", "summary", "education", "experience", "publications", "presentations", "awards"]
  }'
```

## Step-by-Step: Extract Formatting from Google Docs

### 1. Identify Font Family
- In Google Docs, look at the font dropdown
- Common fonts: Arial, Calibri, Times New Roman, Segoe UI, Georgia

### 2. Extract Font Sizes
- Select header text → note the size from toolbar (e.g., 14pt)
- Select body text → note the size
- Typical headers: 12-18pt
- Typical body: 10-12pt

### 3. Get Line Spacing
- Select text → Format → Line spacing
- Standard: 1.0 (single), 1.15 (default), 1.5 (spaced), 2.0 (double)

### 4. Find Color Codes
Method A (Using Chrome DevTools):
1. Right-click text → Inspect
2. Look for `color:` or `fill:` properties in style
3. Find hex code (e.g., #1F4788)

Method B (Using Browser Color Picker):
1. Install browser extension like ColorPicker
2. Click on colored text to see hex value

Method C (Online Conversion):
1. Take screenshot of resume
2. Use online tool like [colorhexa.com](https://www.colorhexa.com/)
3. Upload image and click on colors

### 5. Measure Margins
- Google Docs → File → Page setup
- Margins are shown in inches
- Note top, bottom, left, right values

### 6. List Sections in Order
- Read through resume from top to bottom
- List each section header
- Ensure they match standard section names

## Using Your Custom Template

### Get Your Template ID
After creation, note the `id` from the response (e.g., 4)

### View Your Template
```bash
curl -X GET http://localhost:5001/api/templates/4 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### List All Templates
```bash
curl -X GET http://localhost:5001/api/templates \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Your Template
```bash
curl -X PUT http://localhost:5001/api/templates/4 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "description": "Updated description for my template",
    "style_config": {
      ...updated style config...
    }
  }'
```

### Delete Your Template
```bash
curl -X DELETE http://localhost:5001/api/templates/4 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Tips for Success

### 1. Test with Existing Template First
- Try applying an existing template to see how it works
- This helps you understand what each style parameter does

### 2. Start Simple
- Begin with basic colors and fonts
- Add complexity gradually

### 3. Color Harmony
- Use online tools like [coolors.co](https://coolors.co/) to find harmonious colors
- Primary: Main header color
- Secondary: Alternative header color
- Text: Body text color
- Accent: Highlights and emphasis

### 4. Font Pairing
- Professional: Arial + Times New Roman
- Modern: Segoe UI + Calibri
- Creative: Calibri + Georgia

### 5. Margin Guidelines
- Tight: 0.5"-0.75" (fits more content)
- Standard: 0.75"-1.0" (balanced)
- Spacious: 1.0"-1.25" (premium feel)

### 6. Line Spacing Guidelines
- Compact: 1.0 (academic/formal)
- Default: 1.15 (most professional)
- Loose: 1.3-1.5 (easier reading)

## Common Mistakes

### ❌ Invalid Hex Color Code
```json
// Wrong
"primary": "blue"  // Must be hex

// Right
"primary": "#0052CC"
```

### ❌ Missing Required Fields
```json
// Wrong
{
  "name": "My Template"
  // Missing: description, style_config, sections
}

// Right
{
  "name": "My Template",
  "description": "...",
  "style_config": {...},
  "sections": [...]
}
```

### ❌ Invalid Font Size
```json
// Wrong
"header_font_size": "14pt"  // Must be number only

// Right
"header_font_size": 14
```

### ❌ Empty Sections List
```json
// Wrong
"sections": []  // Cannot be empty

// Right
"sections": ["header", "summary", "experience"]
```

### ❌ Incorrect Margin Format
```json
// Wrong
"margins": "1.0"  // Must be object

// Right
"margins": {
  "top": 1.0,
  "bottom": 1.0,
  "left": 1.0,
  "right": 1.0
}
```

## Advanced: Custom Section Names

While standard section names are recommended, you can create custom names:

```json
"sections": [
  "header",
  "career_objective",
  "professional_experience",
  "technical_competencies",
  "education_and_training",
  "additional_qualifications"
]
```

Just ensure they're meaningful and consistently named across your organization.

## Next Steps

1. **Analyze your Google Drive resume** using the extraction guide
2. **Create your template** using the API or one of the examples above
3. **Test your template** by applying it to a resume
4. **Refine and iterate** based on the results
5. **Share with team** - other users can also benefit from your custom templates!

For questions or issues, refer to the main [CUSTOM_TEMPLATE_GUIDE.md](./CUSTOM_TEMPLATE_GUIDE.md)
