# ❓ Frequently Asked Questions (FAQ)

## General Questions

### Q: What is Emailer Simple Tool?
**A:** It's a user-friendly application that helps you send personalized emails to multiple people at once. Instead of manually typing each person's name and details, the program does it automatically using data from a CSV file.

### Q: Do I need to be technical to use this?
**A:** No! It's designed for regular computer users. If you can use Excel and email, you can use this tool. The GUI interface makes everything point-and-click simple.

### Q: Is it safe to use?
**A:** Yes. Your email passwords are encrypted and stored only on your computer. No information is sent to external servers except for sending your emails through your email provider.

### Q: How many emails can I send?
**A:** The tool is designed for up to 100 recipients per campaign for optimal performance. For larger lists, consider breaking them into smaller groups.

## Setup Questions

### Q: What email providers work with this?
**A:** Most email providers work, including:
- Gmail (most common)
- Outlook/Hotmail  
- Yahoo Mail
- Corporate email systems
- Most other SMTP-enabled email services

### Q: Why can't I use my regular email password?
**A:** Many email providers (like Gmail) require "App Passwords" for security. This is a special password just for applications like this one, separate from your regular login password.

### Q: How do I get an App Password for Gmail?
**A:** 
1. Go to your Google Account settings
2. Enable 2-factor authentication first (required)
3. Go to Security → App passwords
4. Generate a new app password for "Mail"
5. Use this password instead of your regular one

### Q: What if I don't know my SMTP settings?
**A:** Common settings:
- **Gmail**: smtp.gmail.com, port 587
- **Outlook**: smtp-mail.outlook.com, port 587  
- **Yahoo**: smtp.mail.yahoo.com, port 587
- For others, search online for "[your email provider] SMTP settings"

## File Questions

### Q: What is a CSV file?
**A:** It's a simple text file that stores data in columns, like a basic Excel spreadsheet. You can create it by saving an Excel file as "CSV" format.

### Q: Can I use Excel instead of CSV?
**A:** You need to save your Excel file as CSV format. Excel files (.xlsx) won't work directly, but the conversion is simple: File → Save As → CSV format.

### Q: What columns do I need in my CSV file?
**A:** You must have an "email" column. Other columns depend on your message template. If your message uses `{{name}}`, you need a "name" column. If it uses `{{company}}`, you need a "company" column.

### Q: Can I use formatted text in my emails?
**A:** Yes! You can use:
- **Plain text** (.txt files) for simple messages
- **Rich text** (.docx files) for formatted messages with fonts, colors, and styles

## Sending Questions

### Q: What is a "dry run"?
**A:** A dry run creates sample email files without actually sending them. It lets you preview exactly what will be sent to each recipient before you commit to sending real emails.

### Q: Should I always do a dry run first?
**A:** **Absolutely!** Always test with a dry run to make sure:
- Personalization works correctly
- Attachments are included
- Formatting looks right
- No errors in your data

### Q: What if my emails go to spam?
**A:** This can happen with any bulk email. Tips to avoid spam:
- Use a reputable email provider
- Don't use spam-like words in subject lines
- Keep your recipient list clean and relevant
- Ask recipients to check their spam folders initially

### Q: Can I send emails with attachments?
**A:** Yes! Put files in the "attachments" folder of your campaign, and they'll be attached to all emails automatically.

## Picture Generator Questions

### Q: What is the Picture Generator?
**A:** It creates personalized images for each recipient using their data. For example, you could create name badges, certificates, or invitations with each person's name and details.

### Q: Do I need to use pictures?
**A:** No, pictures are completely optional. You can send text-only emails without any images.

### Q: What image formats are supported?
**A:** The tool generates PNG images, which work well for email attachments and display properly in most email clients.

## Troubleshooting

### Q: I get "Connection failed" when testing SMTP
**A:** Check:
- SMTP server address and port are correct
- Username and password are correct (use App Password for Gmail)
- Your internet connection is working
- Your firewall isn't blocking the connection
- Try port 587 with TLS encryption

### Q: My personalization isn't working
**A:** Check:
- CSV column names exactly match your `{{variables}}` (case-sensitive)
- No extra spaces in column names
- CSV file is properly formatted
- Variables in your message template use correct spelling

### Q: The application won't start
**A:** Make sure:
- Python 3.8 or higher is installed
- You installed with GUI support: `pip install emailer-simple-tool[gui]`
- Try reinstalling: `pip uninstall emailer-simple-tool` then `pip install emailer-simple-tool[gui]`

### Q: Images aren't generating properly
**A:** Check:
- Picture project settings are configured correctly
- Text elements have valid data sources
- Image dimensions are reasonable (not too large)
- Fonts are available on your system

## Performance Questions

### Q: How fast does it send emails?
**A:** The tool can process about 478 emails per second, but actual sending speed depends on your email provider's limits and your internet connection.

### Q: How fast does it generate pictures?
**A:** About 180 images per second on typical hardware. Complex images with many elements may take longer.

### Q: My campaign is running slowly
**A:** Try:
- Reducing the number of recipients (keep under 100)
- Simplifying picture projects (fewer text elements)
- Using smaller image dimensions
- Checking your internet connection speed

## Error Messages

### Q: "SMTP Authentication failed"
**A:** Your email credentials are incorrect. Double-check:
- Username (usually your full email address)
- Password (use App Password for Gmail, not regular password)
- Server settings are correct for your provider

### Q: "File not found" errors
**A:** Make sure:
- All required files exist (recipients.csv, subject.txt, msg.txt)
- File names are spelled correctly
- Files are in the correct campaign folder
- You have permission to read the files

### Q: "Invalid CSV format"
**A:** Your CSV file has formatting issues:
- Make sure it's saved as CSV format (not Excel)
- Check for missing commas or extra quotes
- Ensure the first row contains column headers
- Verify no empty rows at the beginning

## Getting More Help

### Q: Where can I find more detailed help?
**A:** Use the other sections in this help system:
- **📁 Campaign Setup** - Detailed campaign creation
- **📧 Email Configuration** - Complete SMTP setup
- **🖼️ Picture Generator** - Advanced image features
- **🚀 Quick Start** - 5-minute setup guide

### Q: The help doesn't answer my question
**A:** Try:
- Searching in the help system (use the search box)
- Checking the troubleshooting section
- Looking at the complete documentation files
- Testing with a simple campaign first to isolate the issue

---

**Still need help?** Most issues can be resolved by starting with a simple test campaign and gradually adding complexity once the basics work.

*Happy emailing!* 📧
