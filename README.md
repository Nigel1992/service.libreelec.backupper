# LibreELEC Backupper

<div align="center">

![LibreELEC Backupper Logo](https://github.com/Nigel1992/service.libreelec.backupper/blob/main/service.libreelec.backupper/resources/icon.png)

*Your reliable backup solution for LibreELEC*

[![License: GPL-2.0](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)
[![Version: 1.1.0](https://img.shields.io/badge/Version-1.1.0-green.svg)](service.libreelec.backupper/addon.xml)
[![Platform: LibreELEC](https://img.shields.io/badge/Platform-LibreELEC-red.svg)](https://libreelec.tv/)

</div>

## 🎯 What's New in 1.1.0 (March 13, 2025)

We've simplified the addon to focus on core functionality and reliability:

- **Beautiful New UI** with enhanced notifications and progress reporting
- **Real-time File Size Display** in notifications with addon icon
- **Improved Progress Tracking** during backup/restore operations
- **Test Connection Feature** to verify your remote storage settings
- **Simplified Backup Options** focusing on essential items only

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
   Add-ons > Install from zip file > Download and select service.libreelec.backupper-1.1.0.zip
   ```
   > Note: Repository installation will be available soon!

2. **Configure Settings**
   - Choose backup location (Local or Remote)
   - Set compression level
   - Configure notifications
   - Set maximum backups to keep

3. **Start Backing Up**
   - Click "Backup Now"
   - Watch the progress
   - Done!

## 📚 Available Options Explained

### General Settings
- **Backup Location Type**: Choose between Local or Remote storage
- **Remote Storage Options**: 
  - Supports SMB, NFS, FTP, SFTP, and WebDAV
  - Test connection feature
  - Username/password authentication
  - Custom port configuration
- **Notifications**:
  - Enable/disable notifications
  - Choose detailed or simple notifications
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
- **Backup Now**: Start an immediate backup
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
  <i>Simple, Reliable Backups</i>
</div>
