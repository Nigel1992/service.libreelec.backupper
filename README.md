# LibreELEC Backupper

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Kodi Version](https://img.shields.io/badge/kodi-20%20(Nexus)-green.svg)
![License](https://img.shields.io/badge/license-GPL--2.0-orange.svg)

A comprehensive backup solution for LibreELEC with automated scheduling support. This addon provides a complete system backup solution, allowing you to safeguard your LibreELEC configuration, addons, and media data with ease.

## Features

### Backup Components
- **System**
  - config.txt and configuration files
  - Add-ons and their user data
  - System configurations and bootloader
  - Network and security settings

- **Media & User Data**
  - Sources and playlists
  - Thumbnails and artwork
  - User profiles and game saves
  - Skin settings and favorites

- **Network & Security**
  - Network configurations
  - WiFi settings
  - Samba shares
  - VPN configurations
  - SSH keys and certificates

### Key Features
- 🕒 Automated backup scheduling (hourly/daily/weekly/monthly)
- 📂 Custom backup location support
- 🔄 Backup rotation with configurable retention
- 🔒 Encrypted backup option
- 📧 Email notifications
- ✅ Backup verification
- 📊 Progress tracking and detailed logs

## Installation

1. Download the latest release from the [Releases](https://github.com/Nigel1992/service.libreelec.backupper/releases) page
2. In Kodi, go to Add-ons > Install from zip file
3. Navigate to the downloaded zip file and select it
4. The addon will install and appear in your Program Add-ons section

## Usage

### Basic Setup
1. Go to Add-ons > Program Add-ons > LibreELEC Backupper > Configure
2. Set your preferred backup location
3. Select which components you want to back up
4. Configure backup schedule (optional)

### Manual Backup
1. Open the addon
2. Select "Backup Now" from the Actions menu
3. Wait for the backup to complete

### Automated Backups
1. Enable scheduling in the addon settings
2. Choose your preferred backup interval
3. Set the backup time and day (if applicable)
4. The addon will automatically create backups according to your schedule

## Configuration

### General Settings
- Backup Location: Choose where to store your backups
- Notifications: Enable/disable backup notifications
- Compression Level: Choose between None/Fast/Normal/Maximum
- Maximum Backups: Set how many backups to retain

### Schedule Settings
- Enable/disable automated backups
- Set backup interval (Hourly/Daily/Weekly/Monthly)
- Configure backup time and day
- View last and next scheduled backup times

### Advanced Options
- System logs backup
- Crash logs backup
- Email notifications
- Backup verification
- Custom scripts and configurations

## Troubleshooting

### Common Issues
1. **Backup Failed**
   - Check available storage space
   - Verify write permissions
   - Check system logs for details

2. **Scheduled Backup Not Running**
   - Verify schedule settings
   - Check if Kodi was running at scheduled time
   - Review system logs

3. **Permission Issues**
   - Ensure proper permissions on backup directory
   - Check if SELinux is blocking access

## Support

If you encounter any issues or have suggestions:
1. Check the [Issues](https://github.com/Nigel1992/service.libreelec.backupper/issues) page
2. Create a new issue with detailed information about your problem
3. Include relevant log files and system information

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the GPL-2.0 License - see the [LICENSE](LICENSE) file for details.

## Credits

- Icon by Smashicon @ flaticon.com/4275334
- Fanart: Server room image by DCStudio on Freepik
- Thanks to all contributors and the LibreELEC community

## Changelog

### v1.0.0 (2024-03-09)
- Initial release
- Full backup and restore functionality
- Automated scheduling support
- Compatible with LibreELEC 11.0 and Kodi 20 (Nexus) 