# Frequently Asked Questions (FAQ)

## General Questions

### Q: What is LibreELEC Backupper?
A: LibreELEC Backupper is an addon for Kodi that helps you backup and restore essential parts of your LibreELEC system, including configurations, addons, and user data.

### Q: Which LibreELEC versions are supported?
A: LibreELEC Backupper supports LibreELEC 10.0 and newer versions, running Kodi 19 (Matrix) or newer.

### Q: Where can I get the latest version?
A: Download the latest version from our [GitHub Releases page](https://github.com/Nigel1992/service.libreelec.backupper/releases).

### What's new in version 1.2.0?
Version 1.2.0 introduces automated backup scheduling, allowing you to set up daily, weekly, or monthly backups. It also includes debug mode for multiple daily backups, countdown notifications, and improved status tracking.

## Installation

### Q: How do I install the addon?
A: Download the zip file and install through Kodi's "Install from zip file" option. See our [Installation Guide](Installation) for detailed steps.

### Q: Will it be available in a repository?
A: Yes, repository installation will be available soon. For now, please use the zip file installation method.

## Backup Questions

### Q: What items can I backup?
A: You can backup:
- Configuration Files
- Installed Add-ons
- Add-on User Data and Settings
- Repositories
- Sources

### Q: Where are backups stored?
A: You can store backups either locally on your LibreELEC system or remotely using various protocols (SMB, NFS, FTP, SFTP, WebDAV).

### Q: How much space do backups need?
A: Space requirements vary based on:
- Number of installed addons
- Amount of user data
- Compression level used
- Number of backups kept

### Q: How are old backups managed?
A: The addon automatically manages backups based on your settings, keeping between 5-50 backups and removing the oldest ones when needed.

## Remote Storage

### Q: Which remote storage types are supported?
A: We support:
- SMB (Windows shares)
- NFS
- FTP
- SFTP
- WebDAV

### Q: How do I test remote storage?
A: Use the "Test Connection" feature in the addon settings after configuring your remote storage details.

## Scheduling Questions

### How do I set up automated backups?
Go to the addon settings, enable scheduling, choose your preferred frequency (daily/weekly/monthly), set the backup time, and configure retention settings.

### Can I run multiple backups per day?
Yes, with the new debug mode enabled, you can run multiple backups per day. This is useful for testing or when you need more frequent backups.

### What happens if my system is off during a scheduled backup?
The backup will run at the next system startup if the scheduled time was missed. You can configure notifications to be informed about missed backups.

### How do I change the backup schedule?
You can modify the schedule anytime in the addon settings. Changes take effect immediately, and the next backup time will be recalculated.

### Can I temporarily disable scheduled backups?
Yes, you can disable scheduling in the addon settings without losing your schedule configuration. Re-enable it when you want to resume automated backups.

## Storage and Performance

### Q: How much space do backups need?
A: Space requirements vary based on:
- Number of installed addons
- Amount of user data
- Compression level used
- Number of backups kept

## Troubleshooting

### Q: What if backup fails?
A: Check:
1. Available space
2. Network connection (for remote storage)
3. Permissions
4. See [Troubleshooting Guide](Troubleshooting) for more details

### Q: What if restore fails?
A: Try:
1. Using a different backup
2. Checking error messages
3. Verifying system space
4. See [Restore Guide](Restore) for more help

### Q: Where are the log files?
A: Log files are stored in Kodi's standard log location. Access them through Kodi's log viewer or file system.

## Support

### Q: How do I get help?
A: You can:
1. Check our [Documentation](Home)
2. Visit our [GitHub Issues](https://github.com/Nigel1992/service.libreelec.backupper/issues)
3. Post on the [LibreELEC Forum](https://forum.libreelec.tv/)

### Q: How do I report bugs?
A: Open an issue on our [GitHub Issues page](https://github.com/Nigel1992/service.libreelec.backupper/issues) with:
- Detailed description
- Steps to reproduce
- System information
- Log files if available

## Feature Requests

### Can I request new features?
Yes! Visit our [GitHub Issues](https://github.com/Nigel1992/service.libreelec.backupper/issues) page to submit feature requests or report bugs.

### What features are planned for future releases?
We're constantly improving the addon based on user feedback. Some planned features include:
- More scheduling options
- Advanced retention policies
- Cloud storage support
- Backup encryption

For more detailed information, check our:
- [Configuration Guide](Configuration)
- [Backup Guide](Backup)
- [Restore Guide](Restore) 