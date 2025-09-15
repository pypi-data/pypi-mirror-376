# 📧 Email Configuration (SMTP Setup)

Complete guide to configuring your email server settings for sending campaigns.

## What is SMTP?

SMTP (Simple Mail Transfer Protocol) is the standard way to send emails. To send emails through Emailer Simple Tool, you need to configure it with your email provider's SMTP settings.

## Quick Setup by Provider

### 📧 Gmail (Most Common)

#### Settings
- **SMTP Server**: `smtp.gmail.com`
- **Port**: `587`
- **Security**: TLS/STARTTLS
- **Username**: Your full Gmail address (e.g., `yourname@gmail.com`)
- **Password**: App Password (NOT your regular Gmail password)

#### Getting Gmail App Password
1. **Enable 2-Factor Authentication** (required first)
   - Go to Google Account → Security
   - Turn on 2-Step Verification
2. **Generate App Password**
   - Go to Security → App passwords
   - Select "Mail" as the app
   - Copy the 16-character password
3. **Use App Password** in Emailer Simple Tool (not your regular password)

#### Common Gmail Issues
- **"Authentication failed"** → Use App Password, not regular password
- **"Less secure apps"** → Use App Password instead
- **"Connection refused"** → Check port 587 and TLS enabled

### 📧 Outlook/Hotmail

#### Settings
- **SMTP Server**: `smtp-mail.outlook.com`
- **Port**: `587`
- **Security**: TLS/STARTTLS
- **Username**: Your full Outlook address
- **Password**: Your regular Outlook password

#### Outlook Tips
- Usually works with regular password (no app password needed)
- If issues, try enabling "Less secure app access" in account settings
- For Office 365 business accounts, check with IT department

### 📧 Yahoo Mail

#### Settings
- **SMTP Server**: `smtp.mail.yahoo.com`
- **Port**: `587` or `465`
- **Security**: TLS/STARTTLS (port 587) or SSL (port 465)
- **Username**: Your full Yahoo address
- **Password**: App Password (recommended)

#### Getting Yahoo App Password
1. Go to Yahoo Account Security
2. Generate app password for "Mail"
3. Use generated password in Emailer Simple Tool

### 📧 Other Providers

#### Common Settings Pattern
Most email providers follow similar patterns:
- **Server**: `smtp.yourdomain.com` or `mail.yourdomain.com`
- **Port**: `587` (TLS) or `465` (SSL) or `25` (unsecured)
- **Security**: TLS/STARTTLS preferred

#### Finding Your Settings
1. **Search online**: "[your provider] SMTP settings"
2. **Check provider documentation**
3. **Contact your email provider** or IT department
4. **Try common patterns** with your domain

## Step-by-Step Configuration

### 1. Open SMTP Tab

In Emailer Simple Tool:
1. Go to **📧 SMTP** tab
2. You'll see the SMTP configuration form

### 2. Enter Server Settings

#### SMTP Server
- Enter your provider's SMTP server address
- Examples: `smtp.gmail.com`, `smtp-mail.outlook.com`
- No `http://` or `https://` prefix needed

#### Port
- **587** - Most common, uses TLS encryption
- **465** - SSL encryption (older standard)
- **25** - Unencrypted (not recommended)

#### Security
- **TLS/STARTTLS** - Recommended, works with port 587
- **SSL** - Older standard, works with port 465
- **None** - Unencrypted, not recommended

### 3. Enter Credentials

#### Username
- Usually your full email address
- Some providers may use just the username part
- Case-sensitive for some providers

#### Password
- **Gmail**: Use App Password (16 characters)
- **Outlook**: Usually regular password
- **Yahoo**: App Password recommended
- **Others**: Check provider requirements

### 4. Test Connection

#### Always Test First
1. Click **"Test Connection"** button
2. Wait for connection result
3. Fix any issues before proceeding

#### Success Indicators
- ✅ "Connection successful"
- ✅ "Authentication successful"
- ✅ "Ready to send emails"

#### Error Messages
- ❌ "Connection failed" → Check server and port
- ❌ "Authentication failed" → Check username/password
- ❌ "SSL/TLS error" → Check security settings

## Troubleshooting Common Issues

### Connection Failed

#### Check Network
- **Internet connection** working?
- **Firewall** blocking connection?
- **VPN** interfering with connection?

#### Verify Settings
- **Server address** spelled correctly?
- **Port number** correct for your provider?
- **Security type** matches provider requirements?

### Authentication Failed

#### Password Issues
- **Gmail**: Using App Password (not regular password)?
- **Special characters** in password causing issues?
- **Copy/paste** password to avoid typos?

#### Username Issues
- **Full email address** vs just username?
- **Case sensitivity** - try lowercase?
- **Extra spaces** before or after username?

### SSL/TLS Errors

#### Security Settings
- **Port 587** → Use TLS/STARTTLS
- **Port 465** → Use SSL
- **Port 25** → Use None (if allowed)

#### Provider Requirements
- Some providers **require** specific security types
- Check provider documentation for requirements
- Try different security/port combinations

### Provider-Specific Issues

#### Gmail Problems
- **2-Factor Authentication** enabled?
- **App Password** generated and used?
- **"Less secure apps"** disabled (use App Password instead)?

#### Corporate Email Issues
- **IT policies** may block external SMTP access
- **VPN required** for external access?
- **Special authentication** methods required?
- Contact your IT department for assistance

## Advanced Configuration

### Custom SMTP Providers

#### Corporate Exchange Servers
- Server usually: `mail.yourcompany.com`
- May require domain authentication: `DOMAIN\username`
- Check with IT department for exact settings

#### Third-Party Email Services
- **SendGrid**, **Mailgun**, **Amazon SES**, etc.
- Each has specific SMTP settings
- Usually require API keys or special authentication
- Check service documentation for SMTP configuration

### Security Considerations

#### Password Security
- **App Passwords** are safer than regular passwords
- **Different password** for each application
- **Revoke access** easily if needed

#### Connection Security
- **Always use TLS/SSL** when available
- **Avoid unencrypted** connections (port 25)
- **Check certificate warnings** if they appear

## Testing Your Configuration

### Test Email Process

#### Before Sending Campaigns
1. **Configure SMTP settings**
2. **Test connection** successfully
3. **Create simple test campaign** (1-2 recipients)
4. **Dry run first** to verify email generation
5. **Send test campaign** to yourself
6. **Check received email** for formatting and content

#### What to Verify
- **Email arrives** in inbox (not spam)
- **Formatting preserved** (if using .docx)
- **Attachments included** (if any)
- **Personalization working** correctly
- **Images display** properly (if using picture generator)

### Performance Testing

#### Connection Speed
- **Test with small campaigns** first
- **Monitor sending speed** and success rate
- **Check for rate limits** from your provider

#### Provider Limits
- **Gmail**: ~100 emails/day for free accounts
- **Outlook**: ~300 emails/day for free accounts
- **Corporate**: Check with IT for limits
- **Paid services**: Usually higher limits

## Best Practices

### Email Deliverability

#### Avoid Spam Filters
- **Use reputable email provider** (Gmail, Outlook, etc.)
- **Authenticate properly** with correct credentials
- **Avoid spam trigger words** in subject lines
- **Keep recipient lists clean** and relevant

#### Professional Sending
- **Use business email address** when possible
- **Include unsubscribe information** for marketing emails
- **Respect recipient preferences**
- **Monitor bounce rates** and remove bad addresses

### Security Best Practices

#### Credential Management
- **Use App Passwords** when available
- **Don't share credentials** with others
- **Change passwords regularly**
- **Revoke unused app passwords**

#### Safe Testing
- **Always test with yourself first**
- **Use dry runs** before real sending
- **Start with small recipient lists**
- **Verify content** before sending

## Troubleshooting Checklist

When SMTP isn't working, check these items in order:

### ✅ Basic Checks
- [ ] Internet connection working
- [ ] SMTP server address correct
- [ ] Port number correct
- [ ] Security type matches port

### ✅ Authentication Checks
- [ ] Username is full email address
- [ ] Password is correct (App Password for Gmail)
- [ ] No extra spaces in credentials
- [ ] Case sensitivity considered

### ✅ Provider-Specific Checks
- [ ] 2-Factor authentication enabled (Gmail)
- [ ] App Password generated (Gmail/Yahoo)
- [ ] Less secure apps disabled (use App Password)
- [ ] Corporate policies allow SMTP (business accounts)

### ✅ Network Checks
- [ ] Firewall not blocking connection
- [ ] VPN not interfering
- [ ] Antivirus not blocking
- [ ] Try different network if possible

### ✅ Advanced Checks
- [ ] Try different port/security combinations
- [ ] Test with email client (Outlook, Thunderbird)
- [ ] Check provider status page
- [ ] Contact provider support if needed

---

## Next Steps

Once SMTP is configured successfully:

1. **📁 Create Campaign** - Set up your email campaign
2. **🚀 Test with Dry Run** - Always test before sending
3. **📧 Send Campaign** - Send your personalized emails
4. **📊 Review Results** - Check send reports and delivery

**Remember**: Always test your SMTP configuration with a small test campaign before sending to your full recipient list!

---

*Need more help? Check the FAQ section or use the search function to find specific SMTP troubleshooting information.*
