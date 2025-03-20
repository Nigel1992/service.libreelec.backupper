# LibreELEC Config Backupper

A Kodi add-on for LibreELEC that allows you to backup and restore your system configuration, add-ons, and user data.

## �� What's New in 1.2.2 (March 19, 2025)
- Added email notifications for backup events
- Added SMTP configuration in settings
- Added test email functionality
- Added detailed backup information in email notifications

## 🎯 What's New in 1.2.1.1 (March 18, 2025)
- Fixed incorrect reminder notification messages
- Fixed string IDs for backup time notifications

## 🎯 What's New in 1.2.1 (March 18, 2025)
- Added backup reminder notifications (1 hour, 30 min, 10 min, 1 min before backup)
- Improved settings organization with logical grouping
- Added author information in credits section
- Removed DEBUG multiple backups option

## 🎯 What's New in 1.2.0 (March 16, 2025)
We've added powerful scheduling features and improved the overall experience:

NEW FEATURES
- Automated Backups with flexible scheduling options
- Debug Mode allowing multiple backups per day
- Countdown Notifications for scheduled backups
- Persistent Upload Notifications for better tracking

IMPROVEMENTS
- Enhanced Scheduling Logic for reliable automated backups
- Improved Notification System with proper icon display
- Better Error Handling and detailed logging
- Detailed Backup Status tracking and reporting

FIXES
- Fixed notification icon display issues
- Fixed syntax error in backup utilities
- Fixed multiple backup runs on same day
- Fixed scheduler timing precision

## Features

- Backup and restore system configurations
- Backup and restore add-ons and repositories
- Backup and restore user data
- Remote backup support (SMB, NFS, FTP, SFTP, WebDAV)
- Browse remote locations using Kodi's built-in file browser
- Test connection to remote locations
- Compression options
- Backup rotation (keep X most recent backups)
- Detailed progress notifications
- Backup verification
- Automated backup scheduling
- Configurable reminder notifications

## Installation

1. Download the latest release
2. Install the add-on in Kodi (Settings > Add-ons > Install from zip file)
3. Configure the add-on settings

## Configuration

### General Settings

- **Location Type**: Local or Remote
- **Backup Location**: Path to store backups (local or remote)
- **Remote Type**: SMB, NFS, FTP, SFTP, or WebDAV
- **Remote Path**: Path on the remote server
- **Browse Remote Location**: Button to browse and select remote locations using Kodi's file browser
- **Username**: Username for remote authentication
- **Password**: Password for remote authentication
- **Port**: Custom port for remote connection
- **Test Connection**: Button to test the connection to the remote location
- **Show Notifications**: Enable/disable notifications
- **Detailed Notifications**: Show detailed progress
- **Maximum Backups**: Number of backups to keep
- **Compression Level**: None, Fast, Normal, Maximum

### Scheduler Settings

- **Enable Scheduler**: Turn automated backups on/off
- **Backup Frequency**: Daily, Weekly, or Monthly
- **Backup Time**: When to run the backup
- **Day of Week**: For weekly backups
- **Day of Month**: For monthly backups
- **Run Missed Backups**: Automatically run missed backups
- **Enable Reminders**: Get notifications before scheduled backups
- **Reminder Times**: Choose from 1 hour, 30 min, 10 min, and 1 min before backup

### Backup Items

Select which items to include in the backup:

- **System**: Configuration files, fstab, bootloader
- **Add-ons**: Installed add-ons, user data, repositories
- **Media**: Sources, playlists, thumbnails, database
- **User Data**: Profiles, game saves, skins, favorites, keyboard

## Remote Storage Setup

### SMB (Windows Share)

1. Set the location type to "Remote"
2. Set the remote type to "SMB"
3. Click "Browse Remote Location" to open Kodi's file browser
4. Navigate to and select the desired SMB share
5. The path, username, and password will be automatically extracted from the selected location
6. Alternatively, manually enter the server and share in the remote path (e.g., "server/share")
7. Click "Test Connection" to verify the connection works properly

### NFS

1. Set the location type to "Remote"
2. Set the remote type to "NFS"
3. Enter the server and export path in the remote path (e.g., "server/export/path")
4. Enter username and password if required
5. Specify a custom port if not using the default (2049)
6. Click "Test Connection" to verify the connection works properly

### FTP

1. Set the location type to "Remote"
2. Set the remote type to "FTP"
3. Enter the server and directory in the remote path (e.g., "server/directory")
4. Enter username and password
5. Specify a custom port if not using the default (21)
6. Click "Test Connection" to verify the connection works properly

### SFTP (SSH)

1. Set the location type to "Remote"
2. Set the remote type to "SFTP"
3. Enter the server and directory in the remote path (e.g., "server/directory")
4. Enter username and password
5. Specify a custom port if not using the default (22)
6. Click "Test Connection" to verify the connection works properly

Note: SFTP requires the paramiko module which may not be available on all systems.

### WebDAV

1. Set the location type to "Remote"
2. Set the remote type to "WebDAV"
3. Click "Browse Remote Location" to open Kodi's file browser
4. Navigate to and select the desired WebDAV location
5. The path, username, password, and port will be automatically extracted from the selected location
6. Alternatively, manually enter the server and directory in the remote path (e.g., "server/directory")
7. Click "Test Connection" to verify the connection works properly

Note: Both HTTP and HTTPS WebDAV servers are supported.

## Usage

### Manual Backup

1. Open the add-on
2. Select "Make Backup"
3. Wait for the backup to complete

### Restore Backup

1. Open the add-on
2. Select "Restore Backup"
3. Choose the backup to restore
4. Confirm the restoration
5. Restart Kodi when prompted

## Dependencies

- script.module.paramiko (optional, for SFTP support)
- script.module.requests (required for WebDAV support)

## License

This add-on is licensed under the GNU General Public License v3.0.

## Credits

- Created by Nigel1992
- Icon by Smashicon @ flaticon.com/4275334
- Fanart: Low Poly Mountain by Design+Code @ wallpaperswide.com/low_poly_mountain_2-wallpapers.html 