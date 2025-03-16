# Configuration Guide

This guide explains all available configuration options in LibreELEC Backupper.

## General Settings

### Backup Location
- **Location Type**: Choose between Local or Remote storage
  - **Local**: Saves backups to a folder on your LibreELEC system
  - **Remote**: Saves backups to a network location

### Remote Storage Options
If using remote storage:
- **Storage Type**: Choose from
  - SMB (Windows shares)
  - NFS
  - FTP
  - SFTP
  - WebDAV
- **Remote Path**: Enter the path to your backup folder
- **Username**: Your remote storage username
- **Password**: Your remote storage password
- **Port**: Custom port if needed (leave as 0 for default)
- **Test Connection**: Verify your remote storage settings

### Scheduling Options
- **Enable Scheduling**: Turn automated backups on/off
- **Backup Frequency**:
  - Daily: Run backup every day
  - Weekly: Choose a specific day of the week
  - Monthly: Choose a specific day of the month
- **Backup Time**: Set the time for scheduled backups (24-hour format)
- **Retention Count**: Number of backups to keep for scheduled backups
- **Debug Mode**: Allow multiple backups per day (advanced users)

### Notifications
- **Show Notifications**: Enable/disable backup notifications
- **Detailed Notifications**: Show additional information like file sizes and progress
- **Countdown Notifications**: Show countdown for scheduled backups
- **Upload Status**: Display persistent notifications during file uploads
- **Completion Alerts**: Notify when backups finish or fail

### Backup Management
- **Maximum Backups**: Keep between 5-50 backups (older ones are automatically deleted)
- **Compression Level**:
  - None: No compression (fastest, largest files)
  - Fast: Basic compression
  - Normal: Balanced compression
  - Maximum: Best compression (slowest, smallest files)
- **Backup Naming**:
  - Date and Time: Automatic names based on timestamp
  - Custom Name: Your own backup names
  - Date + Custom: Combines both options

## Backup Items

You can choose which items to include in your backups:

### Essential System Items
- **Configuration Files**: System and addon configuration
- **Installed Add-ons**: Your Kodi addons
- **Add-on User Data**: Personal settings and data
- **Repositories**: Addon sources
- **Sources**: Media source locations

## Actions

Available actions in the addon:
- **Backup Now**: Start an immediate backup
- **Restore Backup**: Restore from a previous backup
- **View Backups**: Browse your existing backups

## Best Practices

1. **Storage Space**
   - Monitor available space regularly
   - Use compression for large backups
   - Adjust maximum backups based on space

2. **Remote Storage**
   - Test connection before first backup
   - Use secure protocols (SFTP) when possible
   - Verify credentials and permissions

3. **Backup Strategy**
   - Set up automated backups for regular protection
   - Choose appropriate scheduling frequency
   - Test restore process occasionally
   - Keep at least 2-3 known good backups
   - Monitor backup logs periodically

For backup and restore instructions, see:
- [Backup Guide](Backup)
- [Restore Guide](Restore) 