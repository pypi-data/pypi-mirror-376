# ℹ️ About Emailer Simple Tool

## What is Emailer Simple Tool?

Emailer Simple Tool is a professional email campaign management application designed to make personalized email sending simple and accessible for everyone.

## 🎯 Perfect For

- **Event Invitations** with personal details
- **Newsletters** with recipient names
- **Business Communications** to multiple clients
- **Marketing Campaigns** with personalized images
- **Any email** requiring personal information for each recipient

## ✨ Key Features

### 🎨 Dual Interface
- **Graphical Interface (GUI)** - Point-and-click for beginners
- **Command Line Interface (CLI)** - Automation for advanced users

### 📧 Email Personalization
- Use CSV data to customize emails with `{{variables}}`
- Support for complex personalization patterns
- Automatic validation of data and templates

### 🖼️ Picture Generation
- Create personalized images with text and graphics
- Wizard-guided project creation
- Professional image fusion capabilities

### 📎 Rich Content Support
- **Plain Text** messages (.txt files)
- **Rich Text** support with .docx files (fonts, colors, formatting)
- **Static Attachments** - Add files to all emails
- **Dynamic Images** - Personalized pictures per recipient

### 🛡️ Safety & Security
- **Dry Run Testing** - Preview emails before sending
- **Encrypted Credentials** - Secure SMTP password storage
- **Local Processing** - All data stays on your computer
- **Comprehensive Validation** - Prevent common mistakes

### 🌍 Multi-Language Support
- **English** and **French** interfaces
- **Dynamic Language Switching** - Change language without restart
- **Localized Documentation** - Help in your preferred language

## 📊 Performance

- **Picture Generation**: 180 images/second
- **Email Processing**: 478 emails/second
- **Recommended**: Up to 100 recipients per campaign for optimal performance

## 🖥️ System Requirements

### Minimum Requirements
- **Python 3.8** or higher
- **512MB RAM** available
- **100MB storage** space
- **Internet connection** for sending emails

### Supported Platforms
- **Windows** 10/11
- **macOS** 10.14 or later
- **Linux** (Ubuntu, Debian, CentOS, etc.)

### Supported Email Providers
- **Gmail** (with App Passwords)
- **Outlook/Hotmail**
- **Yahoo Mail**
- **Corporate Exchange** servers
- **Any SMTP-enabled** email service

## 🏗️ Technical Architecture

### Core Components
- **Campaign Manager** - Handles campaign creation and validation
- **Email Sender** - Manages SMTP connections and email delivery
- **Picture Generator** - Creates personalized images with text fusion
- **Template Processor** - Handles email personalization with CSV data

### File Structure
```
Campaign Folder/
├── recipients.csv          # Email list with personalization data
├── subject.txt            # Email subject template
├── msg.txt or msg.docx    # Email message template
├── attachments/           # Static files to attach
├── picture-generator/     # Personalized image projects
├── dryrun/               # Test email outputs
└── logs/                 # Application logs
```

## 🔒 Security & Privacy

### Data Protection
- **Local Processing** - All data processed on your computer
- **No Cloud Storage** - No data sent to external servers
- **Encrypted Credentials** - SMTP passwords encrypted locally
- **Secure Transmission** - Emails sent via secure SMTP connections

### What We Don't Collect
- **No Personal Data** collection
- **No Usage Analytics** sent externally
- **No Email Content** stored or transmitted to third parties
- **No Recipient Lists** shared or stored externally

## 📜 Version Information

### Current Version
**Version 10.0.8** - Released August 18, 2025

### Recent Updates
- **Windows Text Rotation Fix** - Resolved clipping issues for rotated text
- **Enhanced Picture Generation** - Improved PIL-based text rotation
- **Cross-Platform Compatibility** - Better Windows, macOS, Linux support

### Version History
- **v10.x** - GUI implementation with picture generation
- **v9.x** - Send tab and campaign management
- **v8.x** - Picture generator with text fusion
- **v7.x** - Enhanced GUI and validation
- **v6.x** - Initial GUI implementation
- **v5.x** - CLI foundation and core features

## 🤝 Support & Community

### Getting Help
- **📚 Integrated Help** - This help system (you're using it now!)
- **📖 Documentation** - Complete user guides in English and French
- **❓ FAQ** - Common questions and solutions
- **🔧 Troubleshooting** - Step-by-step problem resolution

### Feedback & Contributions
We welcome feedback and suggestions for improving Emailer Simple Tool!

## 📄 License & Legal

### Open Source
Emailer Simple Tool is developed as open source software, making it free to use for personal and commercial purposes.

### Third-Party Components
- **PySide6** - GUI framework (Qt for Python)
- **Pillow (PIL)** - Image processing library
- **cryptography** - Secure credential storage
- **python-docx** - Microsoft Word document processing

## 🚀 Future Development

### Planned Features
- **Enhanced Help System** - Interactive tutorials and guides
- **Advanced Picture Templates** - More image customization options
- **Improved Performance** - Faster processing for large campaigns
- **Additional Languages** - More interface language options

### Development Philosophy
- **User-Friendly** - Designed for non-technical users
- **Secure by Default** - Privacy and security built-in
- **Cross-Platform** - Works everywhere Python runs
- **Extensible** - Easy to add new features and capabilities

---

## 🎉 Thank You!

Thank you for using Emailer Simple Tool! We hope it makes your email campaigns more effective and enjoyable to create.

**Happy Emailing!** 📧

---

*Emailer Simple Tool - Making personalized email campaigns simple and accessible.*
