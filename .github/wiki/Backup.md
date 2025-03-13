# Backup Guide

This guide explains how to create and manage backups using LibreELEC Backupper.

## Before You Start

1. **Check Configuration**
   - Verify backup location is set
   - Ensure enough storage space
   - Test remote connection if using network storage

2. **Select Backup Items**
   - Choose which items to backup:
     - Configuration Files
     - Installed Add-ons
     - Add-on User Data
     - Repositories
     - Sources

## Creating a Backup

### Method 1: Quick Backup
1. Open LibreELEC Backupper
2. Click "Backup Now"
3. Wait for completion notification

### Method 2: Custom Backup
1. Open addon settings
2. Adjust backup items
3. Set compression level
4. Click "Backup Now"
5. Monitor progress

## During Backup

The addon will:
1. Check available space
2. Prepare selected items
3. Create backup archive
4. Apply compression
5. Save to destination
6. Show completion notification

## After Backup

1. **Verify Backup**
   - Check backup location
   - Ensure correct file size
   - Note backup name for future reference

2. **Manage Backups**
   - Remove old backups if needed
   - Keep track of what was backed up
   - Consider testing restore process

## Backup Management

### Viewing Backups
1. Open LibreELEC Backupper
2. Select "View Backups"
3. Browse available backups

### Backup Retention
- System automatically manages backups
- Keeps number specified in settings (5-50)
- Oldest backups removed first

## Best Practices

1. **Regular Backups**
   - Back up after major changes
   - Keep multiple versions
   - Use meaningful names

2. **Space Management**
   - Monitor backup sizes
   - Use appropriate compression
   - Clean up old backups

3. **Documentation**
   - Note what was backed up
   - Record any special settings
   - Keep track of successful backups

For restore instructions, see the [Restore Guide](Restore). 