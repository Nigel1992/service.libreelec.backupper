# LibreELEC Backupper

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Kodi](https://img.shields.io/badge/kodi-20%20(Nexus)-green.svg)
![LibreELEC](https://img.shields.io/badge/LibreELEC-12.0.2-red.svg)
![License](https://img.shields.io/badge/license-GPL--2.0-orange.svg)

A comprehensive backup solution for LibreELEC with automated scheduling support.

[Features](#features) • [Installation](#installation) • [Warning](#🚨-important-warning---untested-features) • [License](#license)

</div>

---

## 🚨 Important Warning - Untested Features

<table>
<tr>
<td>

**PLEASE READ CAREFULLY**: Many features in this addon are currently marked as **[UNTESTED]** and should be used with caution. These features have been implemented but have not undergone thorough testing in real-world environments.

### ❌ Untested Features:
- FSTAB settings
- Bootloader settings
- Media-related backups (playlists, thumbnails, database)
- User data backups (profiles, game saves, skins, favourites)
- Network settings (WiFi, hosts, Samba, VPN)
- Security settings (passwords, certificates, SSH keys)
- Custom scripts and configurations
- System and crash logs
- Email notifications

### ✅ Safe to Use Features:
- Config.txt backup and restore
- Basic scheduling functionality
- Local backup storage
- Manual backup/restore operations
- Configuration files backup
- Add-ons backup/restore
- Add-on user data backup/restore
- Repository backup/restore
- Sources backup/restore
- Backup verification

### ⚠️ Safety Precautions:
Before using any feature marked as [UNTESTED]:
- Create a full manual backup of your system
- Test the feature on non-critical data first
- Be prepared to manually restore your system if needed
- Report any issues on GitHub

</td>
</tr>
</table>

## ✨ Features

### 💾 Backup Components
<table>
<tr>
<td>

- **System**
  - Config.txt and configuration files
  - Add-ons and their user data
- **Media**
  - Sources and playlists
  - Thumbnails and artwork
- **User Data**
  - Profiles and game saves
  - Skin settings and favorites

</td>
<td>

### 🛠️ Core Features
- ⏰ Automated backups (hourly/daily/weekly)
- 📂 Custom backup location support
- 🔄 Backup rotation with retention
- 🔍 Easy restore functionality
- 📊 Progress notifications

</td>
</tr>
</table>

## 📥 Installation

1. Download the addon zip file
2. In Kodi, go to Add-ons > Install from zip file
3. Navigate to the downloaded zip file and select it
4. The addon will be installed and start automatically

## 📋 Requirements

- LibreELEC 12.0.2 or later
- Kodi 20 (Nexus)
- Sufficient storage space for backups
- Network connection for remote backups

## 📜 License

This addon is licensed under the GPL-2.0-or-later license.

## 👥 Credits

- Icon by [Smashicon](https://flaticon.com/4275334)
- Fanart: [Low Poly Mountain](https://wallpaperswide.com/low_poly_mountain_2-wallpapers.html) by Design+Code

## 📝 Changelog

### v1.0.0 (2024-03-09)
- 🎉 Initial release
- ✨ Full backup and restore functionality
- ⚡ Automated scheduling support
- 🔧 Compatible with LibreELEC 12.0.2 and Kodi 20 (Nexus)

### v1.0.1 (2024-03-10)
- ✅ Added repository-specific backup functionality
- ✅ Added backup verification feature
- ✅ Improved sources backup handling
- 🔧 Fixed backup naming to reflect selected items
- 📝 Updated documentation for tested features 