# 🖼️ Picture Generator Guide

Complete guide to creating personalized images for your email campaigns.

## What is the Picture Generator?

The Picture Generator creates personalized images for each recipient in your campaign. You can add text elements that automatically use data from your recipients CSV file to create unique images for each person.

**Examples:**
- Name badges with each person's name and company
- Certificates with recipient names and details
- Event invitations with personalized information
- Marketing materials with custom text per recipient

## Getting Started

### 1. Access Picture Generator

1. Go to **🖼️ Pictures** tab in Emailer Simple Tool
2. Make sure you have a campaign loaded first
3. The Picture Generator will be available for your campaign

### 2. Understanding Projects

#### What is a Picture Project?
A project defines:
- **Canvas size** (image dimensions)
- **Background** (color or image)
- **Text elements** with personalization
- **Styling** (fonts, colors, positioning)

#### Project Structure
```
campaign-folder/
└── picture-generator/
    └── your-project-name/
        ├── project.json          # Project settings
        ├── background.png        # Background image (optional)
        └── generated/           # Output images (created automatically)
```

## Creating Your First Project

### Step 1: Create New Project

1. Click **"Create New Project"** button
2. Enter a descriptive project name (e.g., "Name Badges", "Certificates")
3. Choose canvas dimensions:
   - **Small**: 400x300 pixels (email-friendly)
   - **Medium**: 800x600 pixels (standard)
   - **Large**: 1200x900 pixels (high quality)
   - **Custom**: Enter your own dimensions

### Step 2: Set Background

#### Solid Color Background
1. Choose **"Solid Color"**
2. Click color picker to select background color
3. Popular choices: White (#FFFFFF), Light Blue (#E3F2FD), Light Gray (#F5F5F5)

#### Image Background
1. Choose **"Background Image"**
2. Click **"Browse"** to select image file
3. Supported formats: PNG, JPG, GIF
4. Image will be resized to fit canvas

#### Background Tips
- **Keep it simple** - busy backgrounds make text hard to read
- **Use light colors** for dark text, dark colors for light text
- **Consider email display** - some email clients may not show images
- **Test different sizes** to ensure readability

### Step 3: Add Text Elements

#### Creating Text Elements
1. Click **"Add Text Element"** button
2. Configure the text properties:
   - **Text Content**: What to display
   - **Data Source**: Which CSV column to use
   - **Position**: Where on the image
   - **Styling**: Font, size, color, etc.

#### Text Content Options

**Static Text**
- Fixed text that appears on all images
- Example: "Welcome to our event"
- Use for titles, labels, common information

**Dynamic Text (Personalized)**
- Uses data from your recipients CSV
- Format: `{{column_name}}`
- Example: `{{name}}`, `{{company}}, `{{position}}`
- Each image gets different content based on recipient data

**Mixed Text**
- Combines static and dynamic text
- Example: "Hello {{name}}, welcome to {{company}}'s event!"
- Very flexible for personalized messages

### Step 4: Position and Style Text

#### Positioning
- **X Position**: Horizontal placement (0 = left edge)
- **Y Position**: Vertical placement (0 = top edge)
- **Alignment**: Left, Center, Right
- **Rotation**: Angle in degrees (0-360)

#### Font Styling
- **Font Family**: Choose from available system fonts
- **Font Size**: Size in pixels (12-200 typical range)
- **Font Weight**: Normal, Bold
- **Font Style**: Normal, Italic
- **Color**: Text color (click to choose)

#### Advanced Styling
- **Outline**: Add border around text
- **Shadow**: Add drop shadow effect
- **Transparency**: Make text semi-transparent

## Working with Data

### CSV Integration

#### Available Data
The Picture Generator can use any column from your recipients.csv file:
- `{{name}}` - Recipient's name
- `{{email}}` - Email address
- `{{company}}` - Company name
- `{{position}}` - Job title
- `{{custom_field}}` - Any custom column you create

#### Data Validation
- **Missing data** - Shows placeholder text if CSV field is empty
- **Long text** - Automatically handles text that might be too long
- **Special characters** - Properly handles accents, symbols, etc.

### Text Formatting Tips

#### Readable Text
- **Font size**: Minimum 16px for email readability
- **Contrast**: Dark text on light background (or vice versa)
- **Font choice**: Use clear, readable fonts (Arial, Helvetica, etc.)
- **Spacing**: Leave enough space around text elements

#### Professional Appearance
- **Consistent alignment** - Align related elements
- **Appropriate sizing** - Important text larger, details smaller
- **Color scheme** - Use 2-3 colors maximum
- **White space** - Don't overcrowd the image

## Advanced Features

### Multiple Text Elements

#### Layering
- Add multiple text elements to one image
- Elements are layered in creation order
- Later elements appear on top of earlier ones

#### Example Layout
```
┌─────────────────────────────┐
│        EVENT NAME           │  ← Static text, large font
│                             │
│    Hello {{name}}!          │  ← Personalized greeting
│                             │
│   Company: {{company}}      │  ← Company info
│   Position: {{position}}    │  ← Job title
│                             │
│    December 15, 2025        │  ← Static date info
└─────────────────────────────┘
```

### Text Rotation

#### When to Use Rotation
- **Decorative elements** - Angled titles or watermarks
- **Space optimization** - Fit more text in tight spaces
- **Design variety** - Create more interesting layouts

#### Rotation Tips
- **Small angles** (5-15 degrees) often look more natural
- **45-degree angles** work well for diagonal elements
- **90-degree rotation** for vertical text
- **Test readability** - rotated text can be harder to read

### Color and Styling

#### Color Schemes
- **Monochrome**: Different shades of one color
- **Complementary**: Colors opposite on color wheel
- **Corporate**: Use your company's brand colors
- **High contrast**: Ensure text is always readable

#### Professional Styling
- **Consistent fonts** - Use 1-2 font families maximum
- **Hierarchy** - Important text larger/bolder
- **Alignment** - Keep elements visually organized
- **Balance** - Distribute elements evenly

## Testing and Preview

### Preview System

#### Real-Time Preview
- See changes immediately as you edit
- Preview shows actual recipient data
- Switch between different recipients to test variations

#### Preview Controls
- **Recipient selector** - Choose which recipient to preview
- **Zoom controls** - Zoom in/out for detail work
- **Refresh** - Update preview after changes

### Testing Process

#### Before Generation
1. **Check all text elements** display correctly
2. **Test with different recipients** to see data variations
3. **Verify positioning** and alignment
4. **Check readability** at actual size
5. **Test with longest/shortest names** to check fit

#### Generation Testing
1. **Generate a few test images** first
2. **Check output quality** and file sizes
3. **Verify all recipients** get unique images
4. **Test in email client** to see how images display

## Image Generation

### Generation Process

#### How It Works
1. **Load project settings** and recipient data
2. **Create base image** with background
3. **Add text elements** for each recipient
4. **Apply styling** and positioning
5. **Save individual images** for each recipient

#### Output Details
- **Format**: PNG (best quality for text)
- **Naming**: Uses recipient ID or email for unique filenames
- **Location**: `campaign/picture-generator/project-name/generated/`
- **Automatic attachment**: Images automatically attach to emails

### Generation Options

#### Batch Generation
- **Generate all** - Create images for all recipients at once
- **Generate selected** - Create images for specific recipients
- **Regenerate** - Recreate images after changes

#### Quality Settings
- **Standard quality** - Good for email, smaller file sizes
- **High quality** - Better for printing, larger file sizes
- **Custom DPI** - Specify resolution for special needs

## Performance and Optimization

### Performance Tips

#### Fast Generation
- **Smaller canvas sizes** generate faster
- **Fewer text elements** process quicker
- **Simple backgrounds** (solid colors) are fastest
- **Standard fonts** render faster than custom fonts

#### File Size Optimization
- **Appropriate dimensions** - Don't make images larger than needed
- **Simple designs** create smaller files
- **Limit colors** - Fewer colors = smaller PNG files
- **Consider JPEG** for photo backgrounds (smaller files)

### Recommended Specifications

#### Email-Friendly Images
- **Dimensions**: 400x300 to 800x600 pixels
- **File size**: Under 100KB per image
- **Format**: PNG for text, JPEG for photos
- **Total campaign**: Keep under 10MB total attachment size

#### Print-Quality Images
- **Dimensions**: 1200x900 pixels or higher
- **Resolution**: 300 DPI for printing
- **Format**: PNG for best quality
- **File size**: Larger files acceptable for print use

## Troubleshooting

### Common Issues

#### Text Not Appearing
- **Check data source** - Does CSV column exist?
- **Verify spelling** - Column names are case-sensitive
- **Check positioning** - Is text outside canvas area?
- **Font issues** - Is selected font available on system?

#### Poor Image Quality
- **Increase canvas size** for better resolution
- **Use appropriate fonts** - Some fonts render better than others
- **Check color contrast** - Ensure text is visible against background
- **Avoid very small text** - Minimum 12px for readability

#### Generation Errors
- **Check CSV data** - Ensure no corrupted or missing data
- **Verify project settings** - All required fields configured?
- **Font availability** - Are selected fonts installed?
- **Disk space** - Enough space for generated images?

#### Performance Issues
- **Reduce canvas size** if generation is slow
- **Simplify design** - Fewer elements generate faster
- **Close other applications** to free up memory
- **Generate in smaller batches** for large recipient lists

### Error Messages

#### "Font not found"
- **Solution**: Choose a different font that's installed on your system
- **Common fonts**: Arial, Helvetica, Times New Roman are usually available

#### "CSV column not found"
- **Solution**: Check that `{{column_name}}` exactly matches CSV header
- **Case sensitive**: `{{Name}}` ≠ `{{name}}`

#### "Image generation failed"
- **Solution**: Check project settings, try simpler design first
- **Check logs**: Look for specific error details in application logs

## Best Practices

### Design Guidelines

#### Professional Results
- **Keep it simple** - Clean, uncluttered designs work best
- **Consistent branding** - Use your organization's colors and fonts
- **Readable text** - Ensure good contrast and appropriate sizing
- **Test thoroughly** - Preview with various recipient data

#### Email Compatibility
- **Reasonable file sizes** - Keep images under 100KB each
- **Standard dimensions** - Avoid extremely wide or tall images
- **Alt text consideration** - Images may not display in all email clients
- **Fallback plan** - Ensure email content works without images

### Workflow Efficiency

#### Project Organization
- **Descriptive names** - Use clear project names
- **Template projects** - Save successful designs as templates
- **Version control** - Keep backups of working projects
- **Documentation** - Note design decisions for future reference

#### Batch Processing
- **Test small first** - Generate 5-10 images to test before full batch
- **Monitor progress** - Watch for errors during generation
- **Quality check** - Review sample outputs before sending campaign
- **Backup originals** - Keep project files safe for future use

---

## Next Steps

Once your images are generated:

1. **🚀 Test with Dry Run** - Verify images attach correctly to emails
2. **📧 Send Campaign** - Images will automatically attach to personalized emails
3. **📊 Monitor Results** - Check that recipients receive images properly

**Remember**: Always test image generation and email delivery with a small group before sending to your full recipient list!

---

*Need more help? Check the FAQ section or search for specific picture generation topics.*
