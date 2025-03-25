# LibreELEC Backupper

A Kodi addon for LibreELEC that provides automated backup and restore functionality for your system settings, configurations, and addons.

## Features

- **Automated Backups**: Schedule automatic backups at your preferred time
- **Multiple Storage Options**: Save backups locally or to remote locations (SMB, NFS, FTP, SFTP, WebDAV)
- **Smart Backup Rotation**: Automatically manage your backup files with configurable retention policies
- **Email Notifications**: Receive detailed backup status notifications via email
- **Flexible Configuration**: Choose what to backup (configurations, addons, repositories, etc.)
- **Backup Reminders**: Get notifications before scheduled backups
- **Compression Options**: Choose from different compression levels
- **Remote Browser**: Easy navigation of remote backup locations
- **Connection Testing**: Verify your remote storage settings
- **Beautiful UI**: Modern and user-friendly interface

## Installation

1. Download the latest release
2. Install through Kodi's addon manager
3. Configure your backup settings
4. Enjoy automated backups!

## Configuration

### General Settings
- Choose backup location (local or remote)
- Configure remote storage details
- Set compression level
- Enable/configure backup rotation

### Backup Rotation
The backup rotation feature helps manage your backup files by automatically maintaining a specified number of backups. [See Wiki](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Backup-Rotation) for detailed information.

### Email Notifications
- Configure SMTP settings
- Choose notification events
- Customize email templates

### Scheduling
- Set backup time
- Enable reminder notifications
- Choose reminder intervals

## Support

For help and discussions, visit the [LibreELEC Forum](https://forum.libreelec.tv/).

## Credits

- Icon by Smashicon @ flaticon.com/4275334
- Fanart: Low Poly Mountain by Design+Code @ wallpaperswide.com

## License

GPL-2.0-or-later

## Version History

### v1.4.0 (2025-03-25)
- Added backup rotation feature with configurable retention policies
- Added dedicated wiki documentation for backup rotation
- Improved settings organization with subcategories
- Enhanced warning system for potentially destructive features
- Added visual separators in settings for better organization

### v1.3.1.2 (2025-03-24)
- Improved dialog formatting and organization
- Fixed addon.xml schema validation error

### v1.3.1.1 (2025-03-22)
- Fixed WebDAV connection handling
- Improved error messages for failed connections

### v1.3.1 (2025-03-21)
- Added WebDAV support for remote backups
- Enhanced remote connection error handling
- Improved backup progress reporting

[See full version history](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Version-History)

## NOTE: The restore functionality is still being worked on !

## 🎯 What's New in 1.3.0 (March 20, 2025)

- Added email notifications for backup events
- Added SMTP configuration in settings
- Added test email functionality
- Enhanced email notification system with beautiful HTML templates
- Improved email compatibility across different email clients
- Fixed email settings not applying immediately
- Added detailed backup information in email notifications
- Improved error handling and logging for email notifications

[View full changelog](CHANGELOG.md)

## 🎯 What's New in 1.2.1.1 (March 18, 2025)
- Fixed incorrect reminder notification messages
- Fixed string IDs for backup time notifications

## 🎯 What's New in 1.2.1 (March 18, 2025)
- Added backup reminder notifications (1 hour, 30 min, 10 min, 1 min before backup)
- Improved settings organization with logical grouping
- Added author information in credits section
- Removed DEBUG multiple backups option

## 🚀 Available Backup Items

The addon focuses on backing up the most important parts of your LibreELEC system:

- **Configuration Files** - System and addon configuration files
- **Installed Add-ons** - Your installed Kodi addons
- **Add-on User Data and Settings** - Personal settings and data for your addons
- **Repositories** - Your addon repositories
- **Sources** - Media source locations and settings

## 📋 System Requirements

- LibreELEC 10.0+
- Kodi 19 (Matrix) or newer
- Available storage space

## 🔧 Quick Start

1. **Install the Addon**
   ```
   Add-ons > Install from zip file > Download and select service.libreelec.backupper-1.2.0.zip
   ```
   > Note: Repository installation will be available soon!

2. **Configure Settings**
   - Choose backup location (Local or Remote)
   - Set compression level
   - Configure notifications
   - Set maximum backups to keep
   - Configure backup schedule (NEW!)

3. **Start Backing Up**
   - Click "Backup Now" for immediate backup
   - Or wait for scheduled backup
   - Watch the real-time progress
   - Done!

## 📚 Available Options Explained

### General Settings
- **Backup Location Type**: Choose between Local or Remote storage
- **Remote Storage Options**: 
  - Supports SMB, NFS, FTP, SFTP, and WebDAV
  - Test connection feature
  - Username/password authentication
  - Custom port configuration
- **Scheduling Options** (NEW!):
  - Enable/disable automated backups
  - Choose frequency (Daily/Weekly/Monthly)
  - Set preferred backup time
  - Configure retention count
  - Debug mode for multiple daily backups
- **Notifications**:
  - Enable/disable notifications
  - Real-time progress updates
  - File size tracking
  - Countdown for scheduled backups
  - Persistent upload status
- **Backup Management**:
  - Set maximum number of backups (5-50)
  - Choose compression level (None/Fast/Normal/Maximum)
  - Customize backup naming (Date/Custom/Both)

### Backup Items
Each item can be toggled individually:
- **Configuration Files**: System-wide configuration
- **Installed Add-ons**: Your Kodi addons
- **Add-on User Data**: Personal settings and data
- **Repositories**: Addon sources
- **Sources**: Media locations

### Actions
- **Backup Now**: Start an immediate backup with progress tracking
- **Restore Backup**: Restore from a previous backup
- **View Backups**: Browse existing backups

## 🔍 Troubleshooting

Common solutions for:
- **Connection Issues**
  - Check remote server settings
  - Verify network connectivity
  - Test connection before backup
- **Space Problems**
  - Ensure sufficient storage
  - Check compression settings
  - Manage backup retention
- **Permission Errors**
  - Verify credentials
  - Check folder permissions
  - Ensure write access

Need more help? Check our [Forum](https://forum.libreelec.tv/) or [GitHub Issues](https://github.com/Nigel1992/service.libreelec.backupper/issues).

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repo
2. Create your feature branch
3. Commit changes
4. Push to your branch
5. Open a Pull Request

## 📜 License

GPL-2.0 License - see [LICENSE](LICENSE)

## 📬 Contact & Support

- **Author:** Nigel1992
- **GitHub:** [Nigel1992](https://github.com/Nigel1992)
- **Project:** [service.libreelec.backupper](https://github.com/Nigel1992/service.libreelec.backupper)

---

<div align="center">
  <b>Protect Your LibreELEC System Today!</b><br>
  <i>Simple, Reliable Backups with Real-time Progress</i>
</div>
