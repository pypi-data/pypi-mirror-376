# 🚀 Email Sending Guide

Complete guide to testing and sending your email campaigns safely and effectively.

## Overview

The Send tab is your mission control for email campaigns. It provides comprehensive tools for testing, validating, and sending personalized emails with built-in safety features to prevent mistakes.

## Safety-First Approach

### Why Safety Matters

Email campaigns can't be "undone" once sent. The Send tab implements multiple safety layers:
- **Mandatory validation** - All issues must be resolved before sending
- **Required dry runs** - Must test before sending real emails
- **Confirmation dialogs** - Multiple confirmations prevent accidents
- **Progress monitoring** - Track sending progress and catch issues early

### Built-in Safety Features

#### Campaign Validation
- ✅ All required files exist and are valid
- ✅ CSV data is properly formatted
- ✅ Email addresses are valid
- ✅ SMTP configuration is working
- ✅ No duplicate recipients

#### Dry Run Requirements
- 🧪 Must perform dry run before sending
- 🧪 Dry run must be "fresh" (reflects current campaign state)
- 🧪 Any campaign changes require new dry run
- 🧪 Visual indicators show dry run status

## Campaign Validation

### Automatic Validation

The system continuously validates your campaign and shows status indicators:

#### Green Status (Ready)
- ✅ **All files present** - recipients.csv, subject.txt, message file
- ✅ **Valid CSV format** - Proper formatting and headers
- ✅ **Email addresses valid** - All emails properly formatted
- ✅ **SMTP configured** - Email server settings tested and working
- ✅ **No duplicates** - Each email address appears only once

#### Red Status (Issues Found)
- ❌ **Missing files** - Required campaign files not found
- ❌ **Invalid CSV** - Formatting errors or missing columns
- ❌ **Bad email addresses** - Invalid or malformed email addresses
- ❌ **SMTP not configured** - Email server settings missing or invalid
- ❌ **Duplicate recipients** - Same email address appears multiple times

#### Yellow Status (Warnings)
- ⚠️ **Large recipient list** - Over 100 recipients (performance warning)
- ⚠️ **Large attachments** - Total attachment size over 10MB
- ⚠️ **Missing personalization** - Variables in templates not found in CSV

### Resolving Validation Issues

#### Missing Files
1. **Check campaign folder** - Ensure all required files exist
2. **Verify file names** - Must be exactly: recipients.csv, subject.txt, msg.txt/msg.docx
3. **Check file permissions** - Ensure files are readable

#### CSV Format Issues
1. **Open in text editor** - Check for formatting problems
2. **Verify headers** - First row must contain column names
3. **Check commas** - Ensure proper comma separation
4. **Remove empty rows** - No blank rows at beginning or end
5. **Save as CSV** - Not Excel format

#### Invalid Email Addresses
1. **Check format** - Must be name@domain.com format
2. **Remove spaces** - No spaces before or after email addresses
3. **Fix typos** - Common issues: missing @, wrong domain extensions
4. **Remove invalid entries** - Delete or fix problematic addresses

#### SMTP Configuration
1. **Go to SMTP tab** - Configure email server settings
2. **Test connection** - Use "Test Connection" button
3. **Check credentials** - Verify username and password
4. **Verify settings** - Server, port, security type must be correct

## Dry Run Testing

### What is a Dry Run?

A dry run generates all the emails that would be sent, but saves them as files instead of actually sending them. This lets you:
- **Preview exact content** for each recipient
- **Verify personalization** works correctly
- **Check attachments** are included properly
- **Test formatting** and layout
- **Catch errors** before real sending

### Performing a Dry Run

#### Step 1: Ensure Campaign is Valid
- All validation indicators must be green
- SMTP configuration must be tested and working

#### Step 2: Start Dry Run
1. Click **"Dry Run"** button in Send tab
2. Choose dry run options:
   - **All recipients** - Generate emails for everyone
   - **First 10 recipients** - Quick test with subset
   - **Custom range** - Specify which recipients to test

#### Step 3: Monitor Progress
- Progress bar shows generation status
- Real-time updates on emails being processed
- Error messages if issues occur

#### Step 4: Review Results
- Dry run creates folder: `campaign/dryrun/YYYY-MM-DD_HH-MM-SS/`
- Each recipient gets individual .eml file
- Open .eml files in email client to preview

### Dry Run Output

#### File Structure
```
campaign/
└── dryrun/
    └── 2025-08-19_14-30-15/
        ├── john.doe@example.com.eml
        ├── jane.smith@company.com.eml
        ├── bob.wilson@firm.com.eml
        └── dry_run_report.txt
```

#### What to Check

**Email Content**
- ✅ **Personalization working** - Names, companies filled in correctly
- ✅ **Subject line correct** - Variables replaced properly
- ✅ **Message formatting** - Text/HTML displays correctly
- ✅ **No missing data** - All variables have values

**Attachments**
- ✅ **Static attachments included** - Files from attachments folder
- ✅ **Generated images attached** - Personalized pictures (if using)
- ✅ **File sizes reasonable** - Not too large for email delivery
- ✅ **All recipients have attachments** - Consistent across all emails

**Technical Details**
- ✅ **Email headers correct** - From, To, Subject properly set
- ✅ **Encoding proper** - Special characters display correctly
- ✅ **MIME structure valid** - Email format is standard-compliant

### Dry Run Reports

#### Report Contents
The dry run report (`dry_run_report.txt`) contains:
- **Summary statistics** - Total emails, success/failure counts
- **Processing time** - How long generation took
- **File sizes** - Individual and total email sizes
- **Error details** - Any issues encountered
- **Recipient list** - All processed recipients

#### Reading the Report
```
Dry Run Report - 2025-08-19 14:30:15
=====================================
Campaign: Holiday Party Invitations
Total Recipients: 25
Successful: 25
Failed: 0
Total Processing Time: 2.3 seconds
Average Email Size: 145 KB
Total Campaign Size: 3.6 MB

Recipient Details:
✅ john.doe@example.com (152 KB)
✅ jane.smith@company.com (138 KB)
✅ bob.wilson@firm.com (149 KB)
...
```

## Sending Your Campaign

### Pre-Send Checklist

Before sending real emails, verify:
- ✅ **Dry run completed successfully** - No errors in test
- ✅ **Content reviewed** - Checked sample .eml files
- ✅ **Recipient list verified** - Correct people, no duplicates
- ✅ **SMTP tested** - Connection working properly
- ✅ **Timing appropriate** - Sending at good time for recipients

### Send Process

#### Step 1: Final Validation
- System performs final validation check
- All previous issues must be resolved
- Fresh dry run must exist (reflects current campaign state)

#### Step 2: Send Confirmation
Multiple confirmation steps prevent accidental sending:

**Campaign Summary**
- Shows recipient count, subject, and key details
- Displays total email size and estimated send time
- Lists any warnings or important notes

**Type Campaign Name**
- Must type exact campaign folder name to confirm
- Prevents accidental sends of wrong campaign
- Text box shows campaign name as placeholder

**Final Confirmation Checkboxes**
- ☑️ "I have reviewed the dry run results"
- ☑️ "I confirm this is the correct campaign to send"
- ☑️ "I understand this action cannot be undone"

#### Step 3: Sending Progress
- Real-time progress bar shows sending status
- Individual recipient status updates
- Success/failure counts
- Estimated time remaining

#### Step 4: Send Completion
- Final report with complete statistics
- List of successful and failed sends
- Send report saved for future reference

### Send Progress Monitoring

#### Real-Time Updates
```
Sending Campaign: Holiday Party Invitations
Progress: [████████████████████████████████] 100%
Sent: 23/25 | Failed: 2/25 | Remaining: 0
Elapsed: 45 seconds | Estimated remaining: 0 seconds

Current: Sending to bob.wilson@firm.com...
Last completed: jane.smith@company.com ✅
```

#### Status Indicators
- ✅ **Success** - Email sent successfully
- ❌ **Failed** - Email failed to send (with reason)
- ⏳ **Sending** - Currently being sent
- ⏸️ **Paused** - Sending paused (can resume)
- ⏹️ **Stopped** - Sending stopped by user

### Handling Send Errors

#### Common Send Errors

**SMTP Authentication Failed**
- **Cause**: Email credentials incorrect or expired
- **Solution**: Re-test SMTP settings, update password if needed

**Recipient Address Rejected**
- **Cause**: Email address invalid or blocked by server
- **Solution**: Verify email address, remove if permanently invalid

**Message Too Large**
- **Cause**: Email exceeds size limits (usually 25MB)
- **Solution**: Reduce attachment sizes or remove large files

**Rate Limit Exceeded**
- **Cause**: Sending too fast for email provider limits
- **Solution**: Reduce sending speed, wait and retry

#### Error Recovery
- **Pause sending** - Stop to investigate issues
- **Fix problems** - Correct SMTP settings or recipient data
- **Resume sending** - Continue from where it stopped
- **Retry failed** - Attempt to resend failed emails

## Send Reports and History

### Send Reports

#### Report Generation
After each send, a detailed report is automatically created:
- **Location**: `campaign/sentreport/YYYY-MM-DD_HH-MM-SS/`
- **Format**: Text file with complete statistics
- **Contents**: Success/failure details for each recipient

#### Report Contents
```
Email Campaign Send Report
=========================
Campaign: Holiday Party Invitations
Send Date: 2025-08-19 14:45:30
Total Recipients: 25
Successfully Sent: 23
Failed to Send: 2
Success Rate: 92%
Total Send Time: 3 minutes 15 seconds

Successful Sends:
✅ john.doe@example.com (14:45:32)
✅ jane.smith@company.com (14:45:35)
✅ alice.johnson@corp.com (14:45:38)
...

Failed Sends:
❌ bad.email@invalid.domain (14:46:12) - Domain not found
❌ full.mailbox@company.com (14:46:45) - Mailbox full
```

### Send History

#### Tracking Previous Sends
- **All sends recorded** - Complete history maintained
- **Report archive** - All send reports saved
- **Campaign versions** - Track changes between sends
- **Performance metrics** - Success rates and timing data

#### Managing Send History
- **View past reports** - Access all previous send reports
- **Compare campaigns** - See performance differences
- **Clean up old reports** - Remove outdated reports to save space
- **Export data** - Save reports for external analysis

## Best Practices

### Timing Your Sends

#### Optimal Send Times
- **Tuesday-Thursday** - Generally best response rates
- **10 AM - 2 PM** - Peak email reading times
- **Avoid Mondays** - People catching up from weekend
- **Avoid Fridays** - People preparing for weekend
- **Consider time zones** - Send when recipients are active

#### Scheduling Considerations
- **Business emails** - Send during business hours
- **Personal emails** - Evening or weekend may be better
- **International recipients** - Consider multiple time zones
- **Holiday awareness** - Avoid major holidays

### Email Deliverability

#### Improving Delivery Rates
- **Clean recipient lists** - Remove bounced/invalid addresses
- **Relevant content** - Send only to interested recipients
- **Professional sender** - Use business email address
- **Avoid spam triggers** - Don't use spam-like subject lines
- **Include unsubscribe** - For marketing emails

#### Monitoring Delivery
- **Check bounce rates** - High bounces hurt reputation
- **Monitor spam complaints** - Remove complainers from lists
- **Track engagement** - Low engagement affects deliverability
- **Use reputable SMTP** - Quality email providers help delivery

### Performance Optimization

#### Faster Sending
- **Smaller recipient lists** - Under 100 for best performance
- **Reduce attachment sizes** - Smaller emails send faster
- **Simple email content** - Plain text sends faster than HTML
- **Reliable SMTP provider** - Quality providers handle volume better

#### Resource Management
- **Close other applications** - Free up system resources
- **Stable internet connection** - Avoid interruptions during sending
- **Sufficient disk space** - For reports and temporary files
- **Monitor system performance** - Watch for memory/CPU issues

## Troubleshooting

### Common Issues

#### Dry Run Fails
- **Check campaign validation** - Resolve all red/yellow issues
- **Verify file permissions** - Ensure files are readable
- **Check disk space** - Need space for generated files
- **Review error messages** - Look for specific failure reasons

#### Sending Stops/Fails
- **SMTP connection lost** - Check internet connection
- **Authentication expired** - Re-test SMTP credentials
- **Rate limits hit** - Wait and retry with slower speed
- **Recipient issues** - Check for invalid email addresses

#### Poor Delivery Rates
- **Check spam folders** - Ask recipients to check spam
- **Verify sender reputation** - Use established email address
- **Review content** - Avoid spam trigger words
- **Check recipient engagement** - Remove unengaged recipients

### Getting Help

#### Diagnostic Information
When reporting issues, include:
- **Error messages** - Exact text of any error messages
- **Send reports** - Contents of failed send reports
- **Campaign details** - Recipient count, attachment sizes
- **System information** - Operating system, internet connection type

#### Support Resources
- **📚 Help System** - Search this help system for solutions
- **❓ FAQ** - Check frequently asked questions
- **🔧 Troubleshooting** - Detailed troubleshooting guides
- **📖 Documentation** - Complete user documentation

---

## Summary

The Send tab provides comprehensive tools for safe, effective email campaign delivery:

1. **Validate** - Ensure campaign is properly configured
2. **Test** - Always perform dry run before sending
3. **Review** - Check dry run results carefully
4. **Send** - Use confirmation process to send safely
5. **Monitor** - Track progress and handle any issues
6. **Report** - Review send reports for insights

**Remember**: The safety features are there to protect you. Always use dry runs, read confirmation dialogs carefully, and start with small test campaigns when trying new features.

---

*Need more help? Use the search function to find specific sending topics or check the troubleshooting section for common issues.*
