# LibreELEC Config Backupper

A Kodi add-on for LibreELEC that allows you to backup and restore your system configuration, add-ons, and user data.

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
- **Backup Naming**: Date and Time, Custom Name, or Date + Custom

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

- Icon by Smashicon @ flaticon.com/4275334
- Fanart: Low Poly Mountain by Design+Code @ wallpaperswide.com/low_poly_mountain_2-wallpapers.html 