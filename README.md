[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/Nigel1992)

# LibreELEC Backupper 🔄

<div align="center">

![Version](https://img.shields.io/badge/version-1.5.0-blue.svg)
![License](https://img.shields.io/badge/license-GPL--2.0-green.svg)
![Kodi](https://img.shields.io/badge/kodi-20%2B-purple.svg)
![LibreELEC](https://img.shields.io/badge/LibreELEC-10.0%2B-orange.svg)

*A powerful and user-friendly backup solution for your LibreELEC system*

[Installation](#-installation) • 
[Features](#-features) • 
[Configuration](#-configuration) • 
[Support](#-support) • 
[Documentation](#-documentation) •
[Forum](https://forum.libreelec.tv/thread/29619-addon-libreelec-backup-automated-system-backup-solution/)

</div>

## 🌟 Features

### Core Features
- **Smart Backup Rotation** - Intelligent management of backup files with configurable retention policies
- **Multiple Storage Options** - Local storage or remote locations (SMB, NFS, FTP, SFTP, WebDAV)
- **Automated Scheduling** - Set up daily, weekly, or monthly backups
- **Email Notifications** - Get detailed backup status notifications
- **Flexible Configuration** - Choose exactly what to backup
- **Beautiful UI** - Modern and intuitive interface
- **Real-time Progress** - Live tracking of backup operations
- **Secure Storage** - Support for encrypted remote connections

### What Can Be Backed Up
- 📁 System Configuration Files
- 🔌 Installed Add-ons
- 🎮 Add-on User Data and Settings
- 📦 Repositories
- 🔗 Media Sources

## 📦 Latest Updates

### Version 1.5.0 (April 12, 2026)
- Compared to 1.4.1.7
- Added fully custom GUI windows for dashboard, settings, backup browser, and dialogs
- Added concise per-setting help text in custom settings details panel
- Added optional backup summary popup setting after successful backup
- Added remote storage usage details in dashboard status when available
- Improved dashboard layout separation between guidance and system status
- Improved settings navigation reliability (single-step category movement, stable Up/Down behavior)
- Improved Remote Settings Test Connection output with cleaner, structured protocol reports
- Changed addon popups to consistently use custom GUI dialogs (with native fallback)
- Fixed duplicate settings popup trigger on Enter
- Fixed Credits entries to remain information-only and non-editable
- Improved WebDAV storage quota detection with additional fallback methods

### Version 1.4.1.1 (March 29, 2025)
- Fixed datetime parsing issue in scheduler
- Improved error handling for schedule time parsing

### Version 1.4.1 (March 29, 2025)
- Enhanced main menu UI with last backup and next scheduled backup information
- Improved menu layout with visual separation between actions and information

### Version 1.4.0 (March 25, 2025)
- Added backup rotation feature with configurable retention policies
- Added dedicated wiki documentation for backup rotation
- Improved settings organization with subcategories

## 💻 Installation

### Method 1: Install via Repository (Recommended)
1. Download the [Nigel1992 Kodi Repository](https://github.com/Nigel1992/kodi-repository)
2. In Kodi, go to Add-ons → Install from zip file
3. Select the downloaded repository zip file
4. Go to Add-ons → Install from repository → Nigel1992 Repository → Program add-ons
5. Select and install LibreELEC Backupper

### Method 2: Direct Installation
1. Download the latest release from our [Releases Page](https://github.com/Nigel1992/service.libreelec.backupper/releases)
2. In Kodi, go to Add-ons → Install from zip file
3. Select the downloaded zip file
4. Configure your backup settings
5. You're ready to go!

## ⚙️ Configuration

### General Settings
- Choose backup location (local/remote)
- Configure remote storage details
- Set compression level
- Enable/configure backup rotation

### Backup Rotation
The backup rotation feature helps manage your backup files automatically. [Learn More](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Backup-Rotation)

### Scheduling Options
- Set backup frequency (Daily/Weekly/Monthly)
- Choose preferred backup time
- Configure retention settings
- Enable reminder notifications

## 📱 Remote Storage Support

- **SMB/CIFS** - Windows network shares
- **NFS** - Network File System
- **FTP** - File Transfer Protocol
- **SFTP** - Secure File Transfer Protocol
- **WebDAV** - Web-based Distributed Authoring and Versioning

## 🆕 What's New in 1.5.0

- New fully custom dashboard/settings/backup browser experience (1080i + 720p)
- Better navigation and usability across settings tabs and lists
- Clear per-setting help text and read-only handling for Credits entries
- Optional backup summary popup with matching custom GUI style
- Unified popup/message/confirm/textviewer handling through custom GUI wrappers
- Cleaner Test Connection output for SMB/NFS/FTP/SFTP/WebDAV with concise diagnostics
- Enhanced remote storage status reporting including WebDAV quota fallbacks

[View Full Changelog](CHANGELOG.md)

## 📋 System Requirements

- LibreELEC 10.0 or newer
- Kodi 20 (Nexus) or newer
- Available storage space for backups
- Network connection for remote storage (optional)

## 📚 Documentation

- [Installation Guide](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Installation)
- [Configuration Guide](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Configuration)
- [Backup Guide](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Backup)
- [Restore Guide](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Restore)
- [FAQ](https://github.com/Nigel1992/service.libreelec.backupper/wiki/FAQ)

## 🤝 Support

Need help? We've got you covered:

- 📖 Check our [Wiki](https://github.com/Nigel1992/service.libreelec.backupper/wiki)
- ❓ Review the [FAQ](https://github.com/Nigel1992/service.libreelec.backupper/wiki/FAQ)
- 🐛 Report issues on [GitHub](https://github.com/Nigel1992/service.libreelec.backupper/issues)
- 💬 Join discussions in the [LibreELEC Forum](https://forum.libreelec.tv/)

## 👥 Credits

- Icon by [Smashicon](https://flaticon.com/4275334)
- Fanart: Low Poly Mountain by [Design+Code](https://wallpaperswide.com/low_poly_mountain_2-wallpapers.html)

## 📜 License

This project is licensed under the [GPL-2.0](LICENSE) license.

### Resources
- [LibreELEC Website](https://libreelec.tv)
- [Kodi Website](https://kodi.tv)
- [Nigel1992 Kodi Repository](https://github.com/Nigel1992/kodi-repository)

---
<div align="center">
Made with ❤️ by Nigel1992
</div>

## 💖 Support the Project

All donations go towards your chosen charity. You can pick any charity you'd like, and 5% is retained due to Ko-Fi fees. As a thank you, your name will be listed as a supporter/donor in a GitHub project. Feel free to email me at thedjskywalker@gmail.com for proof! :)

[![Ko-Fi](https://img.shields.io/badge/Ko--Fi-Support%20me-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/nigel1992)
[![PayPal](https://img.shields.io/badge/PayPal-Donate-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://www.paypal.com/donate/?hosted_button_id=KYV9ARF99ZSCE)

---

