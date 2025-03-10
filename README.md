# 🔄 LibreELEC Backupper

<div align="center">

![LibreELEC Logo](https://raw.githubusercontent.com/LibreELEC/LibreELEC.tv/master/distribution/doc/resources/logo.png)

*A powerful backup solution for your LibreELEC system*

[![License: GPL-2.0](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](LICENSE)
[![Platform: LibreELEC](https://img.shields.io/badge/Platform-LibreELEC-green.svg)](https://libreelec.tv)
[![Kodi Add-on](https://img.shields.io/badge/Kodi-Add--on-orange.svg)](https://kodi.tv)

</div>

## 🌟 Features

### 📦 Comprehensive Backup Options
- **System Configuration**
  - `config.txt`
  - `guisettings.xml`
  - `advancedsettings.xml`
  - `keyboard.xml`
  - Custom keymaps
- **Add-ons & Data**
  - Installed Add-ons
  - Add-on User Data
  - Repositories
  - User Settings
- **Media & UI**
  - Sources
  - Playlists
  - Thumbnails/Fanart
  - Skins and Settings
- **User Data**
  - Profiles
  - Game Saves
  - Custom Configurations

### 🛠️ Smart Features
- **Automated Scheduling**
  - Hourly, Daily, or Weekly backups
  - Custom backup time selection
  - Configurable retention policy
- **Intelligent Verification**
  - Backup integrity checking
  - Space requirement verification
  - Automatic error recovery
- **Resource Management**
  - Memory-efficient operation
  - Automatic cleanup
  - Skip problematic files
- **User Interface**
  - Real-time progress notifications
  - Detailed status updates
  - Easy restore interface

## 🚀 Quick Start

### Installation
1. Download the latest release
2. Open Kodi
3. Go to Add-ons → Install from zip file
4. Select the downloaded zip file
5. The addon will install and start automatically

### First Backup
1. Go to Add-ons → Program add-ons → LibreELEC Config Backupper
2. Open Settings
3. Choose what to backup:
   - Configuration Files
   - Add-ons
   - User Data
   - Repositories
   - Sources
4. Click "Backup Now"

## ⚙️ Configuration

### Backup Settings
| Setting | Description | Default |
|---------|-------------|---------|
| Backup Location | Where backups are stored | `/storage/backup` |
| Maximum Backups | Number of backups to keep | 10 |
| Verify Backups | Check backup integrity | Enabled |

### Schedule Settings
| Setting | Description | Options |
|---------|-------------|---------|
| Interval | How often to backup | Hourly/Daily/Weekly |
| Time | When to run backup | HH:MM |
| Auto Clean | Remove old backups | Enabled |

### Notification Settings
| Setting | Description | Options |
|---------|-------------|---------|
| Show Progress | Display backup progress | Enabled |
| Detailed Info | Show detailed status | Optional |
| Verify Messages | Show verification status | Enabled |

## 🔍 Features In-Depth

### Backup Process
1. **Pre-flight Checks**
   - Space verification
   - Permission checks
   - Resource availability

2. **Backup Creation**
   - Real-time progress display
   - Efficient file handling
   - Error recovery

3. **Verification**
   - Integrity checking
   - Manifest validation
   - Space confirmation

4. **Cleanup**
   - Resource release
   - Temporary file removal
   - Memory optimization

### Restore Process
1. Select backup from list
2. Choose items to restore
3. Confirm operation
4. Automatic system update

## 🛡️ Tested Features

### ✅ Fully Tested
- System configuration backup/restore
- Add-on management
- User data handling
- Repository backup
- Source management
- Scheduling system
- Verification process
- Progress notifications
- Resource management

### 🔄 Partially Tested
- Media-related backups
- User profile handling
- Custom configurations

## 📝 License

This project is licensed under the [GPL-2.0](LICENSE) license.

---

<div align="center">

**Made with ❤️ for the LibreELEC Community**

[Report Bug](../../issues) · [Request Feature](../../issues) · [Get Support](../../discussions)

</div>
