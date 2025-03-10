# LibreELEC Config Backupper

A LibreELEC addon that automatically backs up your system configuration and add-ons.

## Features

- Automatic backups at configurable intervals (hourly, daily, or weekly)
- Comprehensive backup options:
  - Configuration Files (config.txt, guisettings.xml, advancedsettings.xml, keyboard.xml)
  - Installed Add-ons
  - Add-on User Data and Settings
  - Repositories
  - Sources
  - Profiles
  - Game Saves
  - Playlists
  - Thumbnails/Fanart
  - Skins and Skin Settings
- Smart backup verification
- Progress notifications with real-time status
- Memory-efficient operation with automatic cleanup
- Configurable backup location
- View and restore previous backups
- Configurable maximum number of backups to keep

## Tested Features

### Fully Tested:
- Config.txt backup and restore
- Add-ons backup/restore
- Add-on user data backup/restore
- Repository backup/restore
- Sources backup/restore
- Basic scheduling functionality
- Local backup storage
- Manual backup/restore operations
- Backup verification
- Progress notifications
- Memory management and cleanup

### Partially Tested:
- Media-related backups (playlists, thumbnails)
- User data backups (profiles, game saves, skins)
- Custom configurations

## Installation

1. Download the addon zip file
2. In Kodi, go to Add-ons > Install from zip file
3. Navigate to the downloaded zip file and select it
4. The addon will be installed and will start automatically

## Usage

### Automatic Backups

The addon will automatically create backups based on the configured interval. By default, backups are created daily and stored in the `/storage/backup` directory.

### Manual Backups

To create a manual backup:
1. Go to Add-ons > Program add-ons > LibreELEC Config Backupper
2. Open the addon settings
3. Select which items to backup (Config Files, Add-ons, User Data, etc.)
4. Click on "Backup Now"

### Backup Process

During backup:
1. Real-time progress notifications show what's being backed up
2. Space requirements are automatically checked
3. Files are verified for integrity (if verification is enabled)
4. System resources are automatically cleaned up after backup

### Restoring Backups

To restore a previous backup:
1. Go to Add-ons > Program add-ons > LibreELEC Config Backupper
2. Click on the addon to open it
3. Select the backup you want to restore from the list
4. Confirm the restore operation

**Note:** Restoring a backup will overwrite your current configuration files. You may need to restart your system for changes to take effect.

## Settings

### Backup Options
- Select which items to backup:
  - Configuration Files
  - Installed Add-ons
  - Add-on User Data
  - Repositories
  - Sources
  - And more...

### Scheduling
- **Backup Interval**: How often to create automatic backups (Hourly, Daily, Weekly)
- **Backup Time**: What time to perform scheduled backups
- **Maximum Backups to Keep**: The maximum number of backup files to keep

### Notifications
- **Show Notifications**: Enable/disable backup notifications
- **Detailed Notifications**: Show detailed progress during backup
- **Verify Backup**: Enable/disable backup verification

## Backup Location

All backups are stored in the `/storage/backup` directory by default, but this can be changed in the settings. The backup directory is created automatically if it doesn't exist.

## Performance

The addon includes several optimizations:
- Efficient memory usage with automatic cleanup
- Skip problematic files (sockets, lock files)
- Handle large files and directories
- Persistent progress notifications
- Automatic resource cleanup after operations

## License

This addon is licensed under the GPL-2.0-or-later license. 