# LibreELEC Backupper

A comprehensive backup solution for LibreELEC with automated scheduling support.

## ⚠️ Important Warning - Untested Features

**PLEASE READ CAREFULLY**: Many features in this addon are currently marked as **[UNTESTED]** and should be used with caution. These features have been implemented but have not undergone thorough testing in real-world environments.

### Untested Features Include:
- Configuration Files (except config.txt)
- FSTAB settings
- Bootloader settings
- Add-ons backup/restore
- Add-on user data backup/restore
- Media-related backups (sources, playlists, thumbnails, database)
- User data backups (profiles, game saves, skins, favourites)
- Network settings (WiFi, hosts, Samba, VPN)
- Security settings (passwords, certificates, SSH keys)
- Custom scripts and configurations
- System and crash logs
- Email notifications

### Safe to Use Features:
- Config.txt backup and restore
- Basic scheduling functionality
- Local backup storage
- Manual backup/restore operations

**Before using any feature marked as [UNTESTED]:**
- Create a full manual backup of your system
- Test the feature on non-critical data first
- Be prepared to manually restore your system if needed
- Report any issues on GitHub

## Features

Backup options include:
• System: config.txt and configuration files
• Add-ons: installed add-ons and their user data
• Media: sources, playlists, and thumbnails
• User Data: profiles, game saves, and skin settings

Additional features:
- Automated backups (hourly/daily/weekly)
- Custom backup location support
- Backup rotation with configurable retention
- Easy restore functionality
- Progress notifications

## Installation

1. Download the addon zip file
2. In Kodi, go to Add-ons > Install from zip file
3. Navigate to the downloaded zip file and select it
4. The addon will be installed and will start automatically

## License

This addon is licensed under the GPL-2.0-or-later license.

## Credits

- Icon by Smashicon @ flaticon.com/4275334
- Fanart: Low Poly Mountain by Design+Code @ wallpaperswide.com/low_poly_mountain_2-wallpapers.html

## Changelog

### v1.0.0 (2024-03-09)
- Initial release
- Full backup and restore functionality
- Automated scheduling support
- Compatible with LibreELEC 11.0 and Kodi 20 (Nexus) 