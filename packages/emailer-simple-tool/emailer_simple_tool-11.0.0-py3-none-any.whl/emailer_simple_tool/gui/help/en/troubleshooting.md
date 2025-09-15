# 🔧 Troubleshooting Guide

Comprehensive troubleshooting guide for common issues and their solutions.

## Quick Diagnosis

### Application Won't Start

#### Symptoms
- Application doesn't launch when clicked
- Error messages about missing modules
- Command not found errors

#### Solutions

**Check Python Installation**
```bash
python3 --version
# Should show Python 3.8 or higher
```

**Reinstall Emailer Simple Tool**
```bash
pip uninstall emailer-simple-tool
pip install emailer-simple-tool[gui]
```

**Check Installation**
```bash
emailer-simple-tool --version
# Should show current version number
```

**Common Fixes**
- **Windows**: Ensure Python is in PATH during installation
- **macOS**: Use `python3` instead of `python`
- **Linux**: Install `python3-pip` if missing

### GUI Won't Open

#### Symptoms
- CLI works but GUI doesn't launch
- Error about PySide6 or Qt
- Display-related errors

#### Solutions

**Install GUI Dependencies**
```bash
pip install emailer-simple-tool[gui]
```

**Check Display (Linux)**
```bash
echo $DISPLAY
# Should show something like :0 or :1
```

**Try Alternative Launch**
```bash
python3 -m emailer_simple_tool.gui
```

**Common Issues**
- **Missing GUI package**: Install with `[gui]` option
- **Linux without display**: Use CLI instead or enable X11 forwarding
- **macOS permissions**: Allow application in Security preferences

## Campaign Issues

### Campaign Won't Load

#### Symptoms
- "Campaign not found" errors
- Files appear to exist but aren't recognized
- Validation always shows red status

#### Diagnosis Steps

**Check File Names**
Required files must be named exactly:
- `recipients.csv` (not Recipients.csv or recipients.CSV)
- `subject.txt` (not subject.TXT)
- `msg.txt` or `msg.docx` (not message.txt)

**Check File Permissions**
```bash
ls -la campaign-folder/
# All files should be readable (r-- in permissions)
```

**Verify File Contents**
- **recipients.csv**: Open in text editor, check for proper CSV format
- **subject.txt**: Should contain subject line text
- **msg.txt**: Should contain email message

#### Common Solutions

**File Naming Issues**
1. Rename files to exact required names
2. Check for hidden file extensions (Windows)
3. Ensure no extra spaces in filenames

**Permission Problems**
1. **Windows**: Right-click → Properties → Security → Full Control
2. **macOS/Linux**: `chmod 644 campaign-folder/*`
3. Move campaign to user's home directory

**File Format Issues**
1. **CSV saved as Excel**: Re-save as CSV format
2. **Text encoding**: Save files as UTF-8 encoding
3. **Line endings**: Use appropriate line endings for your OS

### CSV File Problems

#### Invalid CSV Format

**Symptoms**
- "Invalid CSV format" error
- Personalization not working
- Missing recipient data

**Common CSV Issues**

**Missing Headers**
```csv
# Wrong - no header row
john@example.com,John Doe,ACME Corp

# Correct - header row present
email,name,company
john@example.com,John Doe,ACME Corp
```

**Incorrect Separators**
```csv
# Wrong - semicolon separated
email;name;company
john@example.com;John Doe;ACME Corp

# Correct - comma separated
email,name,company
john@example.com,John Doe,ACME Corp
```

**Extra Quotes or Commas**
```csv
# Wrong - extra quotes
"email","name","company"
"john@example.com","John Doe","ACME Corp"

# Correct - no extra quotes needed
email,name,company
john@example.com,John Doe,ACME Corp
```

**Empty Rows**
```csv
# Wrong - empty rows

email,name,company
john@example.com,John Doe,ACME Corp

# Correct - no empty rows
email,name,company
john@example.com,John Doe,ACME Corp
```

#### Fixing CSV Issues

**Use Text Editor**
1. Open CSV in plain text editor (Notepad, TextEdit)
2. Check format visually
3. Fix any obvious issues
4. Save as plain text

**Re-create from Excel**
1. Open data in Excel
2. File → Save As → CSV (Comma delimited)
3. Choose UTF-8 encoding if available
4. Don't use Excel format (.xlsx)

**Validate CSV Online**
- Use online CSV validators to check format
- Copy/paste small samples to test
- Fix issues before using in campaign

### Personalization Not Working

#### Symptoms
- Variables like `{{name}}` appear literally in emails
- Some recipients get blank fields
- Inconsistent personalization results

#### Diagnosis

**Check Variable Names**
```
Template: Hello {{name}}, welcome to {{company}}!
CSV headers: email,name,company
Result: ✅ Variables match headers

Template: Hello {{Name}}, welcome to {{Company}}!
CSV headers: email,name,company  
Result: ❌ Case mismatch (Name vs name)
```

**Check CSV Data**
```csv
email,name,company
john@example.com,John Doe,ACME Corp     ✅ Complete data
jane@example.com,,Tech Solutions        ❌ Missing name
bob@example.com,Bob Wilson,             ❌ Missing company
```

#### Solutions

**Fix Variable Case**
- Make template variables match CSV headers exactly
- Use lowercase in both: `{{name}}` and CSV header `name`
- Check for typos in variable names

**Clean CSV Data**
- Fill in missing data where possible
- Use placeholder text for missing fields
- Remove recipients with critical missing data

**Test with Simple Example**
1. Create minimal CSV with just email and name
2. Use simple template: `Hello {{name}}`
3. Test dry run to verify personalization works
4. Gradually add complexity

## SMTP and Email Issues

### Connection Problems

#### "Connection Failed" Errors

**Check Basic Settings**
- **Server**: Correct SMTP server address
- **Port**: Usually 587 (TLS) or 465 (SSL)
- **Security**: TLS for port 587, SSL for port 465

**Test Network Connection**
```bash
# Test if server is reachable
ping smtp.gmail.com

# Test if port is open (Linux/macOS)
telnet smtp.gmail.com 587
```

**Common Server Settings**
```
Gmail:
- Server: smtp.gmail.com
- Port: 587
- Security: TLS

Outlook:
- Server: smtp-mail.outlook.com  
- Port: 587
- Security: TLS

Yahoo:
- Server: smtp.mail.yahoo.com
- Port: 587 or 465
- Security: TLS or SSL
```

#### Authentication Failed

**Gmail Issues**
- **Use App Password**: Not your regular Gmail password
- **Enable 2FA**: Required before creating App Password
- **Generate New**: Create fresh App Password if old one fails

**Password Problems**
- **Copy/Paste**: Avoid typing passwords manually
- **No Spaces**: Remove any extra spaces before/after password
- **Special Characters**: Some passwords may need escaping

**Username Issues**
- **Full Email**: Use complete email address as username
- **Case Sensitivity**: Some servers are case-sensitive
- **Domain**: Include full domain (user@domain.com)

### Email Delivery Issues

#### Emails Not Arriving

**Check Spam Folders**
- Recipients should check spam/junk folders
- Mark as "Not Spam" to improve future delivery
- Add sender to recipient's address book

**Verify Email Addresses**
- Check for typos in recipient addresses
- Remove obviously invalid addresses
- Test with known good addresses first

**Check Send Reports**
- Review send report for delivery failures
- Look for bounce messages or error codes
- Remove addresses that consistently fail

#### Emails Going to Spam

**Improve Sender Reputation**
- Use established business email address
- Avoid free email services for business sending
- Send from consistent sender address

**Content Improvements**
- Avoid spam trigger words (FREE, URGENT, CLICK NOW)
- Include unsubscribe link for marketing emails
- Use professional, relevant content
- Avoid excessive capitalization or exclamation marks

**Technical Improvements**
- Use reputable SMTP provider
- Authenticate properly with correct credentials
- Keep recipient lists clean and engaged
- Monitor bounce rates and remove bad addresses

## Picture Generator Issues

### Images Not Generating

#### Common Causes

**Font Problems**
- Selected font not available on system
- Font name spelled incorrectly
- System font cache issues

**Data Issues**
- CSV column referenced in image doesn't exist
- Empty data fields causing generation errors
- Special characters in data causing problems

**Project Configuration**
- Invalid canvas dimensions
- Text positioned outside canvas area
- Corrupted project settings

#### Solutions

**Fix Font Issues**
1. Use common system fonts (Arial, Helvetica, Times New Roman)
2. Check available fonts in system
3. Avoid custom or decorative fonts
4. Test with simple font first

**Verify Data**
1. Check CSV has all columns referenced in image
2. Fill in missing data or use placeholders
3. Remove special characters that might cause issues
4. Test with simple data first

**Reset Project**
1. Create new simple project to test
2. Use basic settings (solid background, simple text)
3. Gradually add complexity
4. Save working configurations as templates

### Poor Image Quality

#### Blurry or Pixelated Images

**Increase Resolution**
- Use larger canvas dimensions
- Minimum 400x300 for email use
- 800x600 or larger for better quality
- Consider final use case (email vs print)

**Font Size Issues**
- Use larger font sizes (minimum 16px)
- Avoid very small text that becomes unreadable
- Test at actual display size
- Consider viewing distance

**Background Problems**
- Use high-resolution background images
- Avoid stretching small images
- Consider solid colors for crisp text
- Test background/text contrast

#### Text Positioning Problems

**Text Cut Off**
- Check text position is within canvas bounds
- Account for text height and width
- Leave margins around text elements
- Test with longest expected text

**Overlapping Elements**
- Plan text layout before creating
- Use consistent spacing between elements
- Consider text length variations
- Test with different recipient data

**Rotation Issues**
- Small rotation angles (5-15°) often work better
- Account for rotated text taking more space
- Test readability of rotated text
- Consider if rotation is necessary

## Performance Issues

### Slow Operation

#### Application Running Slowly

**System Resources**
- Close other applications to free memory
- Check available disk space
- Monitor CPU usage during operations
- Restart application if memory usage high

**Large Campaigns**
- Break large recipient lists into smaller batches
- Process under 100 recipients at a time
- Use simpler email templates for large sends
- Generate images in smaller batches

**Network Issues**
- Check internet connection speed
- Use wired connection instead of WiFi if possible
- Avoid peak usage times for email sending
- Consider email provider rate limits

#### Slow Email Sending

**SMTP Provider Limits**
- Gmail: ~100 emails/day for free accounts
- Outlook: ~300 emails/day for free accounts
- Check your provider's specific limits
- Consider upgrading to business account for higher limits

**Attachment Size**
- Reduce total attachment size per email
- Compress large files before attaching
- Use smaller image dimensions
- Remove unnecessary attachments

**Network Optimization**
- Use stable internet connection
- Avoid sending during peak hours
- Consider batch sending over multiple sessions
- Monitor for connection interruptions

### Memory Issues

#### Out of Memory Errors

**Reduce Memory Usage**
- Process smaller batches of recipients
- Close other applications
- Use smaller image dimensions
- Restart application between large operations

**System Requirements**
- Ensure minimum 512MB RAM available
- Check system memory usage
- Consider upgrading system memory
- Use 64-bit Python if available

## Error Messages

### Common Error Messages and Solutions

#### "File not found"
- **Cause**: Required campaign files missing
- **Solution**: Ensure recipients.csv, subject.txt, and msg.txt exist
- **Check**: File names spelled exactly right

#### "Permission denied"
- **Cause**: No access to read/write campaign files
- **Solution**: Check file permissions, move to accessible location
- **Windows**: Run as administrator if needed

#### "Invalid email address"
- **Cause**: Malformed email addresses in CSV
- **Solution**: Check email format, fix typos, remove invalid entries
- **Format**: Must be name@domain.com

#### "SMTP authentication failed"
- **Cause**: Incorrect email credentials
- **Solution**: Verify username/password, use App Password for Gmail
- **Check**: Server settings match provider requirements

#### "Connection timeout"
- **Cause**: Network or server issues
- **Solution**: Check internet connection, try different SMTP server
- **Wait**: Server may be temporarily unavailable

#### "Message too large"
- **Cause**: Email exceeds size limits
- **Solution**: Reduce attachment sizes, use smaller images
- **Limit**: Most providers limit to 25MB per email

### Getting Detailed Error Information

#### Application Logs
- **Location**: `campaign-folder/logs/`
- **Format**: Text files with timestamp
- **Contents**: Detailed error messages and stack traces

#### Send Reports
- **Location**: `campaign-folder/sentreport/`
- **Contents**: Success/failure details for each recipient
- **Use**: Identify patterns in failures

#### Dry Run Reports
- **Location**: `campaign-folder/dryrun/`
- **Contents**: Generation success/failure details
- **Use**: Debug issues before sending

## Getting Help

### Self-Help Resources

#### Built-in Help
- **📚 Help System**: Search this help system for solutions
- **❓ FAQ**: Check frequently asked questions
- **🚀 Quick Start**: Review setup basics
- **📁 Campaign Setup**: Detailed campaign creation guide

#### Testing Approach
1. **Start Simple**: Create minimal test campaign
2. **Add Complexity Gradually**: Add features one at a time
3. **Test Each Step**: Verify each component works before proceeding
4. **Document Solutions**: Note what works for future reference

### Reporting Issues

#### Information to Include
When seeking help, provide:
- **Error Messages**: Exact text of any error messages
- **System Information**: Operating system, Python version
- **Campaign Details**: Number of recipients, file sizes
- **Steps to Reproduce**: What you did before the error occurred
- **Log Files**: Contents of relevant log files

#### Diagnostic Commands
```bash
# System information
python3 --version
emailer-simple-tool --version

# Check installation
pip show emailer-simple-tool

# Test basic functionality
emailer-simple-tool --help
```

---

## Prevention Tips

### Avoiding Common Issues

#### Campaign Setup
- **Use templates**: Start with working examples
- **Test small**: Always test with 2-3 recipients first
- **Validate early**: Check files before creating large campaigns
- **Backup working configs**: Save successful setups

#### Email Sending
- **Always dry run**: Never send without testing first
- **Check SMTP regularly**: Test connection before each campaign
- **Monitor delivery**: Watch for bounce patterns
- **Keep lists clean**: Remove invalid addresses promptly

#### System Maintenance
- **Keep software updated**: Update Emailer Simple Tool regularly
- **Monitor disk space**: Ensure adequate space for operations
- **Regular restarts**: Restart application for large operations
- **Clean old files**: Remove old dry runs and reports periodically

---

**Remember**: Most issues can be resolved by starting with a simple test case and gradually adding complexity. When in doubt, test with a minimal campaign first!

*Still having issues? Use the search function to find specific error messages or check other help sections for detailed guidance.*
