# Backup Guide

This guide explains how to perform backups using LibreELEC Backupper.

## Backup Methods

### Manual Backup
1. Open the addon
2. Click "Backup Now"
3. Monitor progress through notifications
4. Wait for completion confirmation

### Scheduled Backup (New!)
1. Enable scheduling in settings
2. Choose frequency:
   - Daily: Runs every day at specified time
   - Weekly: Runs on chosen day of week
   - Monthly: Runs on chosen day of month
3. Set backup time (24-hour format)
4. Configure retention count
5. Optional: Enable debug mode for multiple daily backups

## Monitoring Backups

### Real-time Progress
- Watch file count and size progress
- View current file being processed
- See estimated time remaining

### Notifications
- Countdown alerts for scheduled backups
- Persistent upload status during transfers
- Completion notifications
- Error alerts if issues occur

## Backup Management

### Storage Options
- Local storage on LibreELEC system
- Remote storage (SMB, NFS, FTP, SFTP, WebDAV)
- Compression levels for space saving

### Retention Settings
- Set maximum number of backups
- Configure scheduled backup retention
- Automatic cleanup of old backups

## Best Practices

1. **Schedule Selection**
   - Choose appropriate frequency for your needs
   - Set convenient backup times
   - Consider system usage patterns

2. **Storage Management**
   - Monitor available space
   - Use appropriate compression
   - Set reasonable retention limits

3. **Verification**
   - Check backup logs regularly
   - Verify backup contents periodically
   - Test restore process occasionally

## Troubleshooting

If you encounter issues:
- Check [Troubleshooting Guide](Troubleshooting)
- Review system logs
- Verify storage permissions
- Test network connectivity for remote storage

For restore instructions, see the [Restore Guide](Restore). 