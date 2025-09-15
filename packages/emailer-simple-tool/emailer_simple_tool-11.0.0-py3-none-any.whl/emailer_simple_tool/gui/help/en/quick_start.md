# 🚀 Quick Start Guide (5 minutes)

Get up and running with Emailer Simple Tool in just 5 minutes!

## Step 1: Choose Your Interface

Emailer Simple Tool offers two interfaces:
- **🎨 Graphical Interface (GUI)** - Perfect for beginners, point-and-click
- **⌨️ Command Line Interface (CLI)** - For advanced users and automation

Since you're reading this, you're already using the GUI! 

## Step 2: Create Your First Campaign

### What You Need
- **Email list** - A CSV file with recipient information
- **Email message** - What you want to send
- **SMTP settings** - Your email server configuration

### Campaign Folder Structure
```
My Campaign/
├── recipients.csv          # Required: Your email list
├── subject.txt            # Required: Email subject
├── msg.txt or msg.docx    # Required: Email message
├── attachments/           # Optional: Files to attach
└── picture-generator/     # Optional: Personalized images
```

## Step 3: Set Up Your Campaign

### 📁 Campaign Tab
1. Click **"Browse"** to select or create a campaign folder
2. The wizard will guide you through creating the required files
3. Edit your recipient list, subject, and message

### Example Recipients File (recipients.csv)
```csv
id,email,name,company
001,john@example.com,John Doe,ACME Corp
002,jane@example.com,Jane Smith,Tech Solutions
```

### Example Message (msg.txt)
```
Dear {{name}},

Welcome to our service! We're excited to have {{company}} as a partner.

Best regards,
The Team
```

## Step 4: Configure Email Settings

### 📧 SMTP Tab
1. Enter your email server settings
2. **For Gmail users:**
   - Server: smtp.gmail.com
   - Port: 587
   - Use an App Password (not your regular password)
3. **Test Connection** to verify settings

### Getting Gmail App Password
1. Enable 2-factor authentication
2. Go to Google Account → Security → App passwords
3. Generate password for "Mail"
4. Use this password in SMTP settings

## Step 5: Test Before Sending

### 🚀 Send Tab
1. Click **"Dry Run"** to test your campaign
2. Review the generated email files
3. Check that personalization works correctly
4. Verify attachments and formatting

**Always test first!** Dry runs show you exactly what will be sent.

## Step 6: Send Your Campaign

### Final Send
1. After successful dry run, click **"Send Campaign"**
2. Confirm you want to send
3. Monitor the progress
4. Review the send report

## 🎨 Optional: Add Personalized Images

### 🖼️ Pictures Tab
1. Create a picture project
2. Add text elements with recipient data
3. Generate personalized images
4. Images automatically attach to emails

## 💡 Pro Tips

### Safety First
- **Always dry run first** - See exactly what will be sent
- **Start small** - Test with a few recipients initially
- **Check spam folders** - Recipients should check spam/junk

### Performance
- **Keep lists under 100** recipients for best performance
- **Use simple images** for faster generation
- **Test SMTP settings** before large campaigns

### Troubleshooting
- **Connection issues?** Check SMTP settings and firewall
- **Missing personalization?** Verify CSV column names match {{variables}}
- **Images not working?** Check picture project settings

## 🆘 Need More Help?

- **📁 Campaign Setup** - Detailed campaign creation guide
- **📧 Email Configuration** - Complete SMTP setup instructions
- **🖼️ Picture Generator** - Advanced image personalization
- **❓ FAQ** - Common questions and solutions

## 🎉 You're Ready!

That's it! You now know the basics of creating and sending personalized email campaigns with Emailer Simple Tool.

**Remember:** Always test with dry runs before sending to ensure everything works perfectly.

---

*Happy emailing! 📧*
