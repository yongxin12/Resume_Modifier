# Custom Resume Template Creation Guide

## Overview
This guide explains how to convert your existing formatted resume from Google Drive into a reusable template that can be applied to all your resumes.

## Template Structure

The Resume Editor stores templates with two core components:

### 1. **Style Configuration (`style_config`)**
Defines the visual styling and layout rules for the resume.

```json
{
  "font_family": "Arial",
  "header_font_size": 16,
  "body_font_size": 11,
  "line_spacing": 1.2,
  "color_scheme": {
    "primary": "#2E86AB",
    "secondary": "#A23B72",
    "text": "#333333",
    "accent": "#F18F01"
  },
  "margins": {
    "top": 0.8,
    "bottom": 0.8,
    "left": 0.8,
    "right": 0.8
  }
}
```

**Required Fields:**
- `font_family` (string): Primary font family (e.g., "Arial", "Calibri", "Times New Roman")
- `header_font_size` (number): Font size for section headers in points
- `body_font_size` (number): Font size for body text in points
- `line_spacing` (number): Line spacing multiplier (e.g., 1.2 for 120%)
- `color_scheme` (object):
  - `primary` (hex color): Main color for headers/emphasis
  - `secondary` (hex color): Secondary accent color
  - `text` (hex color): Main text color
  - `accent` (hex color): Additional accent for highlights
- `margins` (object): Page margins in inches
  - `top`, `bottom`, `left`, `right` (numbers)

### 2. **Sections (`sections`)**
An ordered list of resume sections to include.

```json
["header", "summary", "experience", "education", "skills", "certifications"]
```

**Standard Section Names:**
- `header` - Name and contact information
- `summary` - Professional summary
- `executive_summary` - Executive-level summary (for senior roles)
- `experience` - Work experience
- `education` - Education and degrees
- `skills` - Technical and professional skills
- `certifications` - Certifications and licenses
- `portfolio` - Portfolio links and projects
- `projects` - Detailed project descriptions
- `board_positions` - Board membership and positions
- `achievements` - Notable achievements and awards
- `volunteer` - Volunteer work
- `languages` - Language proficiencies
- `publications` - Published works

## Current Built-in Templates

The system includes three default templates you can use as reference:

### 1. Professional Modern
**Best for:** Corporate, finance, tech roles
```json
{
  "name": "Professional Modern",
  "description": "Clean, modern design with blue accents suitable for corporate environments",
  "style_config": {
    "font_family": "Arial",
    "header_font_size": 16,
    "body_font_size": 11,
    "line_spacing": 1.2,
    "color_scheme": {
      "primary": "#2E86AB",
      "secondary": "#A23B72",
      "text": "#333333",
      "accent": "#F18F01"
    },
    "margins": {"top": 0.8, "bottom": 0.8, "left": 0.8, "right": 0.8}
  },
  "sections": ["header", "summary", "experience", "education", "skills", "certifications"]
}
```

### 2. Creative Designer
**Best for:** Design, marketing, creative roles
```json
{
  "name": "Creative Designer",
  "description": "Eye-catching design with creative elements, perfect for design and creative roles",
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
    "margins": {"top": 0.7, "bottom": 0.7, "left": 0.9, "right": 0.9}
  },
  "sections": ["header", "summary", "portfolio", "experience", "education", "skills", "projects"]
}
```

### 3. Executive Classic
**Best for:** Executive, leadership, senior roles
```json
{
  "name": "Executive Classic",
  "description": "Sophisticated and traditional design for senior-level positions",
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
    "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}
  },
  "sections": ["header", "executive_summary", "experience", "education", "board_positions", "achievements"]
}
```

## How to Create Your Custom Template

### Step 1: Analyze Your Current Resume

Extract the following information from your formatted Google Drive resume:

1. **Font Details:**
   - Primary font family used
   - Header text size (in points)
   - Body text size (in points)
   - Line spacing

2. **Color Scheme:**
   - Primary color (hex code) - used for headers
   - Secondary color (hex code) - accent/secondary headers
   - Text color (hex code) - main body text
   - Accent color (hex code) - highlights

3. **Spacing:**
   - Top, bottom, left, right margins (in inches)
   - Line spacing multiplier

4. **Sections:**
   - List all section headers in order (summary, experience, education, skills, etc.)

### Step 2: Create the Template JSON

Create a JSON file with your extracted information:

```json
{
  "name": "Your Template Name",
  "description": "Description of your template and best use case",
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

### Step 3: Submit Your Template

**Option A: Via API (Recommended)**

Use the create template endpoint:
```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Your Template Name",
    "description": "Your template description",
    "style_config": {...},
    "sections": [...]
  }'
```

**Option B: Direct Database Insertion**

If you have database access:
```sql
INSERT INTO resume_templates (name, description, style_config, sections, is_active, created_at, updated_at)
VALUES (
  'Your Template Name',
  'Your template description',
  '{"font_family": "Arial", ...}',
  '["header", "summary", ...]',
  true,
  NOW(),
  NOW()
);
```

## Tips for Template Creation

### Font Selection
- **Professional roles:** Arial, Calibri, Times New Roman
- **Creative roles:** Segoe UI, Georgia, Garamond
- **Tech roles:** Courier New, Inconsolata (monospace for coding)

### Color Combinations (Hex Codes)

**Corporate/Professional:**
- Primary: `#1F4788` (dark blue)
- Text: `#2C3E50` (dark gray-blue)
- Accent: `#E8B724` (gold)

**Creative/Modern:**
- Primary: `#E74C3C` (red)
- Text: `#2C3E50` (dark gray-blue)
- Accent: `#F39C12` (orange)

**Executive/Classic:**
- Primary: `#1B4332` (dark green)
- Text: `#000000` (black)
- Accent: `#B7E4C7` (light green)

### Section Organization Best Practices

1. **Always include:** header, summary/executive_summary, experience, education, skills
2. **Optional sections based on role:**
   - Creative roles: Add "portfolio" and "projects"
   - Executive roles: Add "board_positions" and "achievements"
   - Academic: Add "publications" and "languages"
3. **Section order matters:** Sections are rendered in the order listed

### Font Size Guidelines

- **Header font:** 14-18pt (larger for creative roles)
- **Body font:** 10-12pt
- **Typical combinations:**
  - Professional: 14pt headers, 11pt body
  - Creative: 18pt headers, 11pt body
  - Executive: 14pt headers, 10pt body

### Margin Guidelines

- **Standard:** 0.75"-1.0" all sides
- **Narrow:** 0.5"-0.75" (fits more content)
- **Wide:** 1.0"-1.25" (more breathing room)

### Line Spacing Guidelines

- **Compact:** 1.0-1.1 (more content per page)
- **Standard:** 1.15-1.2 (most professional)
- **Spacious:** 1.3-1.5 (for creative designs)

## Example: Converting a Google Drive Resume to Template

### Your Current Resume Layout:
```
Header: Arial 14pt, color #1F4788
Margins: 0.75" all around
Line spacing: 1.15
Colors: Dark blue headers, gray text, orange accents

Sections in order:
1. Name & Contact (header)
2. Professional Summary (summary)
3. Work Experience (experience)
4. Education (education)
5. Technical Skills (skills)
```

### Resulting Template JSON:
```json
{
  "name": "My Professional Template",
  "description": "Clean and modern template with dark blue headers, perfect for tech and corporate roles",
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

## API Endpoints for Template Management

### Get All Templates
```bash
GET /api/templates
```

### Get Specific Template
```bash
GET /api/templates/{template_id}
```

### Create New Template
```bash
POST /api/templates
```
**Required fields:** name, description, style_config, sections

### Update Template
```bash
PUT /api/templates/{template_id}
```

### Delete Template
```bash
DELETE /api/templates/{template_id}
```

## Frequently Asked Questions

**Q: Can I use custom fonts?**
A: Yes, any standard font name works. The system will use it when rendering documents. However, ensure the font is available on the system where the resume will be used.

**Q: What hex color format should I use?**
A: Use 6-digit hex codes with # prefix, e.g., `#2E86AB`. You can use tools like [colorhexa.com](https://www.colorhexa.com/) or [colorpicker.com](https://www.colorpicker.com/) to find hex values.

**Q: Can I modify a template after creating it?**
A: Yes, use the PUT endpoint with the template ID to update any fields except the template ID itself.

**Q: What happens if I delete a template?**
A: Templates are soft-deleted (marked as inactive) and can still be used for existing resumes, but won't appear in new template selections.

**Q: Can I have multiple custom templates?**
A: Yes, you can create as many templates as you need. Each user can create their own custom templates.

**Q: How do I find the hex color codes from my Google Drive resume?**
A: 
1. Right-click on colored text → Inspect (in Chrome DevTools)
2. Look for `color:` property to find the hex code
3. Alternatively, use browser color picker extensions

## Next Steps

1. **Analyze your current resume** and extract styling information
2. **Create your template JSON** using the structure provided
3. **Test your template** by applying it to a resume
4. **Iterate and refine** as needed

Once you've created your custom template, all future resumes can use it, ensuring consistent formatting across your resume library!
