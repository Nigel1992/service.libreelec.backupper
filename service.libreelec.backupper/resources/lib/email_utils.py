import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import xbmc
import xbmcaddon
from datetime import datetime

ADDON = xbmcaddon.Addon()

# Simple HTML Email Template without CSS
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body bgcolor="#f5f5f5" style="margin: 0; padding: 20px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff" style="border: 1px solid #e0e0e0;">
                    <tr>
                        <td style="padding: 30px;">
                            {content}
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top: 30px; border-top: 1px solid #e0e0e0;">
                                <tr>
                                    <td align="center" style="padding-top: 20px; color: #666666; font-size: 14px;">
                                        <p>This is an automated message from LibreELEC Backupper</p>
                                        <p>Generated on {timestamp}</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

class EmailNotifier:
    def __init__(self):
        self.reload_settings()

    def reload_settings(self):
        """Reload settings from Kodi"""
        global ADDON
        ADDON = xbmcaddon.Addon()
        
        self.enabled = ADDON.getSettingBool('enable_email')
        self.smtp_server = ADDON.getSettingString('smtp_server')
        try:
            self.smtp_port = ADDON.getSettingInt('smtp_port')
        except:
            self.smtp_port = 587
        self.smtp_username = ADDON.getSettingString('smtp_username')
        self.smtp_password = ADDON.getSettingString('smtp_password')
        self.smtp_from = ADDON.getSettingString('smtp_from')
        self.smtp_to = ADDON.getSettingString('smtp_to')
        self.use_tls = ADDON.getSettingBool('smtp_use_tls')
        
        xbmc.log(f"Email settings - Server: {self.smtp_server}, Port: {self.smtp_port}, From: {self.smtp_from}, To: {self.smtp_to}, TLS: {self.use_tls}", xbmc.LOGINFO)

    def send_email(self, subject, body):
        """Send an email using the configured SMTP settings"""
        self.reload_settings()
        
        if not self.enabled:
            xbmc.log("Email notifications are disabled", xbmc.LOGINFO)
            return True, "Email notifications are disabled"

        if not all([self.smtp_server, self.smtp_from, self.smtp_to]):
            error_msg = "Missing required email settings"
            xbmc.log(error_msg, xbmc.LOGERROR)
            return False, error_msg

        try:
            xbmc.log(f"Creating email message - Subject: {subject}", xbmc.LOGINFO)
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"LibreELEC Backupper: {subject}"
            msg['From'] = self.smtp_from
            msg['To'] = self.smtp_to

            # Create plain text version
            text = body.replace('<br>', '\n').replace('</p>', '\n\n')
            text = ''.join([i if ord(i) < 128 else ' ' for i in text])
            text = ' '.join(text.split())
            msg.attach(MIMEText(text, 'plain'))

            # Create HTML version
            html_content = EMAIL_TEMPLATE.format(
                content=body,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            msg.attach(MIMEText(html_content, 'html'))

            xbmc.log(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}", xbmc.LOGINFO)
            if self.use_tls:
                xbmc.log("Using TLS connection", xbmc.LOGINFO)
                context = ssl.create_default_context()
                smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
                smtp.starttls(context=context)
            else:
                xbmc.log("Using non-TLS connection", xbmc.LOGINFO)
                smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)

            if self.smtp_username and self.smtp_password:
                xbmc.log(f"Logging in with username: {self.smtp_username}", xbmc.LOGINFO)
                smtp.login(self.smtp_username, self.smtp_password)

            smtp.send_message(msg)
            smtp.quit()

            xbmc.log(f"Email sent successfully: {subject}", xbmc.LOGINFO)
            return True, "Email sent successfully"

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            xbmc.log(error_msg, xbmc.LOGERROR)
            if hasattr(e, 'smtp_error'):
                xbmc.log(f"SMTP Error: {e.smtp_error}", xbmc.LOGERROR)
            if hasattr(e, 'smtp_code'):
                xbmc.log(f"SMTP Code: {e.smtp_code}", xbmc.LOGERROR)
            if hasattr(e, 'strerror'):
                xbmc.log(f"Error Details: {e.strerror}", xbmc.LOGERROR)
            return False, error_msg

    def test_email(self):
        """Send a test email to verify settings"""
        xbmc.log("Sending test email", xbmc.LOGINFO)
        subject = "Test Email"
        body = """
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td align="center" style="padding-bottom: 20px; border-bottom: 2px solid #e0e0e0;">
                    <h1 style="color: #2196F3; margin: 0; font-size: 24px;">LibreELEC Backupper Test Email</h1>
                    <p style="color: #666666; margin: 10px 0 0;">Email Notification System Test</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 20px;">
                    <div style="text-align: center; padding: 15px; margin: 20px 0; background-color: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9;">
                        ✅ Your email settings are configured correctly!
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0;">
                        <h2 style="color: #1976D2; margin: 0 0 15px; font-size: 18px;">Email Configuration Details</h2>
                        <table width="100%" cellpadding="8" cellspacing="0" border="0" style="border-collapse: collapse;">
                            <tr>
                                <td width="40%" style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>SMTP Server</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{server}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Port</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{port}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Security</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{security}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>From</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{from_addr}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>To</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{to_addr}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://github.com/Nigel1992/service.libreelec.backupper" style="display: inline-block; padding: 10px 20px; background-color: #2196F3; color: #ffffff; text-decoration: none; margin-top: 20px;">
                            View Documentation
                        </a>
                    </div>
                </td>
            </tr>
        </table>
        """.format(
            server=self.smtp_server,
            port=self.smtp_port,
            security="TLS" if self.use_tls else "None",
            from_addr=self.smtp_from,
            to_addr=self.smtp_to
        )

        return self.send_email(subject, body)

    def notify_backup_started(self, backup_type="manual"):
        """Send email notification when backup starts"""
        if not self.enabled:
            return

        subject = "Backup Started"
        body = """
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td align="center" style="padding-bottom: 20px; border-bottom: 2px solid #e0e0e0;">
                    <h1 style="color: #2196F3; margin: 0; font-size: 24px;">Backup Process Started</h1>
                    <p style="color: #666666; margin: 10px 0 0;">A new backup operation has been initiated</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 20px;">
                    <div style="text-align: center; padding: 15px; margin: 20px 0; background-color: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb;">
                        ⚙️ {backup_type} backup is now in progress...
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0;">
                        <h2 style="color: #1976D2; margin: 0 0 15px; font-size: 18px;">Backup Information</h2>
                        <table width="100%" cellpadding="8" cellspacing="0" border="0" style="border-collapse: collapse;">
                            <tr>
                                <td width="40%" style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Type</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{backup_type}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Start Time</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{start_time}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>System</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">LibreELEC</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="text-align: center;">You will receive another email when the backup is complete.</p>
                </td>
            </tr>
        </table>
        """.format(
            backup_type=backup_type.title(),
            start_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        self.send_email(subject, body)

    def notify_backup_complete(self, backup_type="manual", backup_info=None):
        """Send email notification when backup completes successfully"""
        if not self.enabled:
            return

        subject = "Backup Completed Successfully"
        body = """
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td align="center" style="padding-bottom: 20px; border-bottom: 2px solid #e0e0e0;">
                    <h1 style="color: #2196F3; margin: 0; font-size: 24px;">Backup Completed Successfully</h1>
                    <p style="color: #666666; margin: 10px 0 0;">Your {backup_type} backup has finished</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 20px;">
                    <div style="text-align: center; padding: 15px; margin: 20px 0; background-color: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9;">
                        ✅ Backup completed successfully!
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0;">
                        <h2 style="color: #1976D2; margin: 0 0 15px; font-size: 18px;">Backup Details</h2>
                        <table width="100%" cellpadding="8" cellspacing="0" border="0" style="border-collapse: collapse;">
                            <tr>
                                <td width="40%" style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Backup Name</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{name}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Size</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{size}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Location</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{location}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Items Backed Up</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{items}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Completion Time</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{completion_time}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="text-align: center;">Your LibreELEC system has been successfully backed up and is ready for restoration if needed.</p>
                </td>
            </tr>
        </table>
        """.format(
            backup_type=backup_type.title(),
            name=backup_info.get('name', 'N/A'),
            size=backup_info.get('size', 'N/A'),
            location=backup_info.get('location', 'N/A'),
            items=backup_info.get('items', 'N/A'),
            completion_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        self.send_email(subject, body)

    def notify_backup_failed(self, backup_type="manual", error_message=None):
        """Send email notification when backup fails"""
        if not self.enabled:
            return

        subject = "Backup Failed"
        body = """
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td align="center" style="padding-bottom: 20px; border-bottom: 2px solid #e0e0e0;">
                    <h1 style="color: #2196F3; margin: 0; font-size: 24px;">Backup Failed</h1>
                    <p style="color: #666666; margin: 10px 0 0;">Your {backup_type} backup encountered an error</p>
                </td>
            </tr>
            <tr>
                <td style="padding: 20px;">
                    <div style="text-align: center; padding: 15px; margin: 20px 0; background-color: #ffebee; color: #c62828; border: 1px solid #ffcdd2;">
                        ❌ Backup operation failed!
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0;">
                        <h2 style="color: #1976D2; margin: 0 0 15px; font-size: 18px;">Error Details</h2>
                        <table width="100%" cellpadding="8" cellspacing="0" border="0" style="border-collapse: collapse;">
                            <tr>
                                <td width="40%" style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Backup Type</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{backup_type}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Time of Failure</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{failure_time}</td>
                            </tr>
                            <tr>
                                <td style="border-bottom: 1px solid #e0e0e0; color: #666666;"><strong>Error Message</strong></td>
                                <td style="border-bottom: 1px solid #e0e0e0;">{error_message}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p style="text-align: center;">
                        Please check your LibreELEC system logs for more information.
                        <br><br>
                        <a href="https://github.com/Nigel1992/service.libreelec.backupper/wiki/Troubleshooting" style="display: inline-block; padding: 10px 20px; background-color: #2196F3; color: #ffffff; text-decoration: none;">
                            Troubleshooting Guide
                        </a>
                    </p>
                </td>
            </tr>
        </table>
        """.format(
            backup_type=backup_type.title(),
            failure_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            error_message=error_message or "Unknown error"
        )

        self.send_email(subject, body) 