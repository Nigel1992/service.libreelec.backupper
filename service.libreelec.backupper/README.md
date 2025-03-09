# LibreELEC Config Backupper

A LibreELEC addon that automatically backs up the config.txt file located at /flash/config.txt.

## Features

- Automatic backups of config.txt at configurable intervals (hourly, daily, or weekly)
- Backups are stored in /storage/backup directory
- Manual backup option
- View and restore previous backups
- Configurable maximum number of backups to keep
- Optional notifications when backups are created

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

## Installation

1. Download the addon zip file
2. In Kodi, go to Add-ons > Install from zip file
3. Navigate to the downloaded zip file and select it
4. The addon will be installed and will start automatically

## Usage

### Automatic Backups

The addon will automatically create backups of your config.txt file based on the configured interval. By default, backups are created daily and stored in the `/storage/backup` directory.

### Manual Backups

To create a manual backup:
1. Go to Add-ons > Program add-ons > LibreELEC Config Backupper
2. Open the addon settings
3. Click on "Backup Now"

### Restoring Backups

To restore a previous backup:
1. Go to Add-ons > Program add-ons > LibreELEC Config Backupper
2. Click on the addon to open it
3. Select the backup you want to restore from the list
4. Confirm the restore operation

**Note:** Restoring a backup will overwrite your current config.txt file. You may need to restart your system for changes to take effect.

## Settings

- **Backup Interval**: How often to create automatic backups (Hourly, Daily, Weekly)
- **Maximum Backups to Keep**: The maximum number of backup files to keep (older backups will be deleted)
- **Show Notifications**: Whether to show notifications when backups are created

## Backup Location

All backups are stored in the `/storage/backup` directory on your LibreELEC system. This directory is created automatically if it doesn't exist.

## License

This addon is licensed under the GPL-2.0-or-later license. 