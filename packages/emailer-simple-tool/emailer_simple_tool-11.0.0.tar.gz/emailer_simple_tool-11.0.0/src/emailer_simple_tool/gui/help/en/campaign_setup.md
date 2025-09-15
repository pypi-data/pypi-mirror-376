# 📁 Campaign Setup Guide

Complete guide to creating and managing email campaigns with Emailer Simple Tool.

## What is a Campaign?

A campaign is a folder containing all the files needed to send personalized emails:
- **Recipient list** (CSV file with email addresses and data)
- **Email subject** (template with personalization)
- **Email message** (plain text or formatted document)
- **Attachments** (optional files to include)
- **Pictures** (optional personalized images)

## Campaign Folder Structure

```
My Campaign/
├── recipients.csv          # Required: Email list with data
├── subject.txt            # Required: Email subject template
├── msg.txt or msg.docx    # Required: Email message
├── attachments/           # Optional: Files to attach to all emails
├── picture-generator/     # Optional: Personalized image projects
├── dryrun/               # Created: Test email outputs
├── logs/                 # Created: Application logs
└── .emailer-config.json  # Created: Campaign settings
```

## Step 1: Create Campaign Folder

### Using the GUI
1. Go to the **📁 Campaign** tab
2. Click **"Browse"** button
3. Choose **"Create New Campaign"** or select existing folder
4. Follow the campaign creation wizard

### Manual Creation
1. Create a new folder for your campaign
2. Give it a descriptive name (e.g., "Holiday Party Invitations")
3. The wizard will help create the required files

## Step 2: Set Up Recipients List

### Creating recipients.csv

The recipients file contains your email list and personalization data.

#### Required Column
- **email** - The recipient's email address (must be exact column name)

#### Optional Columns
Add any columns you want to use for personalization:
- **name** - Recipient's name
- **company** - Company name
- **position** - Job title
- **city** - Location
- **custom_field** - Any custom data

#### Example recipients.csv
```csv
id,email,name,company,position,city
001,john.doe@example.com,John Doe,ACME Corporation,Manager,New York
002,jane.smith@company.com,Jane Smith,Tech Solutions,Director,San Francisco
003,bob.wilson@firm.com,Bob Wilson,Wilson & Associates,Partner,Chicago
```

### CSV File Tips

#### Formatting Rules
- **First row must be column headers**
- **Use commas to separate columns**
- **No empty rows at the beginning**
- **Save as CSV format** (not Excel .xlsx)

#### Creating in Excel
1. Open Excel and create your data table
2. First row = column headers (email, name, company, etc.)
3. Following rows = recipient data
4. **File → Save As → CSV (Comma delimited)**
5. Choose the campaign folder as save location
6. Name it exactly: **recipients.csv**

#### Data Quality Tips
- **Verify email addresses** are correct
- **Remove duplicates** to avoid sending twice
- **Check spelling** in names and companies
- **Use consistent formatting** (e.g., all names in "First Last" format)

## Step 3: Create Email Subject

### subject.txt File

Create a file named **subject.txt** with your email subject line.

#### Examples
```
Welcome to our event, {{name}}!
```

```
Your {{company}} invitation is ready
```

```
{{name}}, don't miss our special offer
```

#### Subject Line Tips
- **Keep it under 50 characters** for best email client display
- **Avoid spam words** like "FREE", "URGENT", "CLICK NOW"
- **Personalize when possible** using recipient data
- **Be clear and specific** about email content

## Step 4: Create Email Message

You can create either a plain text or formatted message.

### Plain Text Message (msg.txt)

Simple text file with your email content.

#### Example msg.txt
```
Dear {{name}},

We're excited to invite you and {{company}} to our annual conference.

Event Details:
- Date: December 15, 2025
- Time: 9:00 AM - 5:00 PM
- Location: Convention Center, {{city}}

Please RSVP by December 1st.

Best regards,
The Event Team
```

### Formatted Message (msg.docx)

Rich text document with fonts, colors, and formatting.

#### Creating in Microsoft Word
1. Open Microsoft Word
2. Create your email content with formatting
3. Use `{{variable}}` syntax for personalization
4. **File → Save As → Word Document (.docx)**
5. Save in your campaign folder as **msg.docx**

#### Formatting Tips
- **Use readable fonts** (Arial, Calibri, Times New Roman)
- **Keep formatting simple** for better email compatibility
- **Test with different email clients** to ensure compatibility
- **Avoid complex layouts** that might break in email

## Step 5: Personalization Variables

### Variable Syntax

Use `{{column_name}}` to insert data from your CSV file.

#### Examples
- `{{name}}` - Inserts the value from the "name" column
- `{{company}}` - Inserts the value from the "company" column
- `{{email}}` - Inserts the recipient's email address

### Variable Rules

#### Case Sensitive
- `{{name}}` ≠ `{{Name}}` ≠ `{{NAME}}`
- Column names must match exactly

#### Valid Characters
- Letters, numbers, underscores: `{{first_name}}`
- No spaces: `{{first name}}` ❌ `{{first_name}}` ✅
- No special characters: `{{name!}}` ❌ `{{name}}` ✅

#### Error Prevention
- **Spell check** variable names against CSV columns
- **Use consistent naming** (all lowercase recommended)
- **Test with dry run** to verify personalization works

## Step 6: Add Attachments (Optional)

### Static Attachments

Files that will be attached to every email in the campaign.

#### Setting Up Attachments
1. Create **attachments** folder in your campaign directory
2. Copy files you want to attach into this folder
3. All files in this folder will be attached to every email

#### Supported File Types
- **Documents**: PDF, DOC, DOCX, TXT
- **Images**: JPG, PNG, GIF
- **Spreadsheets**: XLS, XLSX, CSV
- **Archives**: ZIP, RAR
- **Most other file types** are supported

#### Attachment Tips
- **Keep total size under 10MB** per email for best delivery
- **Use descriptive filenames** 
- **Compress large files** when possible
- **Test delivery** with attachments using dry run

## Step 7: Campaign Validation

### Automatic Validation

The application automatically checks your campaign for common issues:

#### File Validation
- ✅ Required files exist (recipients.csv, subject.txt, message file)
- ✅ CSV file format is valid
- ✅ Email addresses are properly formatted
- ✅ Variables in templates match CSV columns

#### Data Validation
- ✅ No duplicate email addresses
- ✅ All required columns present
- ✅ No empty email addresses
- ✅ Reasonable recipient count (under 100 recommended)

### Fixing Validation Errors

#### Common Issues and Solutions

**"Missing required file"**
- Ensure recipients.csv, subject.txt, and msg.txt/msg.docx exist
- Check file names are spelled exactly right
- Verify files are in the correct campaign folder

**"Invalid CSV format"**
- Open CSV in text editor to check formatting
- Ensure commas separate columns properly
- Remove any empty rows at the beginning
- Save as CSV format, not Excel format

**"Variable not found in CSV"**
- Check that `{{variable}}` names match CSV column headers exactly
- Verify spelling and case sensitivity
- Remove any extra spaces in column names

**"Invalid email address"**
- Check email addresses for typos
- Ensure proper format: name@domain.com
- Remove any extra spaces or characters

## Step 8: Test Your Campaign

### Always Use Dry Run First

Before sending real emails, always test with a dry run:

1. Go to **🚀 Send** tab
2. Click **"Dry Run"** button
3. Review generated email files
4. Check personalization worked correctly
5. Verify attachments are included

### What Dry Run Shows You

- **Exact email content** for each recipient
- **Personalization results** (variables replaced with actual data)
- **Attachment inclusion** verification
- **Email formatting** preview
- **Potential issues** before real sending

## Campaign Management Tips

### Organization
- **Use descriptive folder names** for campaigns
- **Keep campaigns separate** - one folder per campaign
- **Archive old campaigns** when no longer needed
- **Backup important campaigns** before major changes

### Best Practices
- **Start small** - test with 5-10 recipients first
- **Verify data quality** before creating large campaigns
- **Keep recipient lists updated** and remove bounced emails
- **Follow email best practices** to avoid spam filters

### Performance Optimization
- **Keep recipient lists under 100** for best performance
- **Use simple attachments** (avoid very large files)
- **Optimize images** in picture generator projects
- **Test on different devices** and email clients

## Troubleshooting Campaign Issues

### Campaign Won't Load
- Check folder permissions (you need read/write access)
- Verify required files exist and are named correctly
- Try creating a new simple campaign to test

### Personalization Not Working
- Verify CSV column names match template variables exactly
- Check for extra spaces or special characters
- Test with a simple variable like `{{name}}` first

### Files Not Found
- Ensure all files are in the correct campaign folder
- Check file extensions (.csv, .txt, .docx)
- Verify file names don't have extra spaces or characters

---

## Next Steps

Once your campaign is set up:

1. **📧 Configure SMTP** - Set up your email server settings
2. **🖼️ Add Pictures** (optional) - Create personalized images
3. **🚀 Test and Send** - Dry run, then send your campaign

**Remember**: Always test with dry run before sending real emails!

---

*Need more help? Check the other help sections or use the search function to find specific information.*
