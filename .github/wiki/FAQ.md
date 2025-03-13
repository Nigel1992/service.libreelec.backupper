# Frequently Asked Questions (FAQ)

## General Questions

### Q: What is LibreELEC Backupper?
A: LibreELEC Backupper is an addon for Kodi that helps you backup and restore essential parts of your LibreELEC system, including configurations, addons, and user data.

### Q: Which LibreELEC versions are supported?
A: LibreELEC Backupper supports LibreELEC 10.0 and newer versions, running Kodi 19 (Matrix) or newer.

### Q: Where can I get the latest version?
A: Download the latest version from our [GitHub Releases page](https://github.com/Nigel1992/service.libreelec.backupper/releases).

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