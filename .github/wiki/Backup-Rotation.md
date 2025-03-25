# Backup Rotation

The backup rotation feature helps manage your backup files by automatically maintaining a specified number of backups while removing older ones based on your chosen strategy.

## ⚠️ Important Warning

When enabled, the backup rotation feature will **automatically delete** ZIP files in your chosen backup folder that exceed your specified maximum number of backups. Please ensure you:
- Use a dedicated folder for your backups
- Do not store other ZIP files in the backup folder
- Set an appropriate maximum number of backups to retain

## How It Works

The backup rotation feature provides three strategies for managing your backups:

1. **Keep Newest** (Default): Retains the most recent backups up to your specified maximum, deleting the oldest ones.
2. **Keep Oldest**: Preserves the oldest backups up to your specified maximum, removing newer ones that exceed the limit.
3. **Keep Both Ends**: Maintains an equal number of oldest and newest backups, removing files from the middle of the date range.

## Configuration

1. In the addon settings, navigate to the "Backup Settings" section
2. Set your preferred "Maximum Number of Backups" (5-50, default is 10)
3. Choose your "Backup Rotation Strategy"
4. Ensure you have a dedicated backup folder selected

## Best Practices

1. **Dedicated Folder**: Always use a dedicated folder for your backups to prevent accidental deletion of other files
2. **Regular Monitoring**: Check your backup folder periodically to ensure rotation is working as expected
3. **Adequate Storage**: Choose a maximum backup number that your storage can comfortably accommodate
4. **Important Backups**: Manually copy critical backups to a separate location if you need to preserve them indefinitely

## Example Setup

```
Backup Location: /storage/backups/libreelec/
Maximum Backups: 10
Strategy: Keep Newest

Result: The system will maintain your 10 most recent backups in the folder,
automatically removing older ones when new backups are created.
```

## Safety Tips

1. Test the rotation feature with a small number of backups first
2. Keep critical backups in a separate folder not managed by rotation
3. Monitor available storage space regularly
4. Review the backup logs to track rotation activities

## Related Settings

- **Maximum Number of Backups**: Controls how many backups to retain
- **Backup Rotation Strategy**: Determines which backups to keep/delete
- **Backup Location**: Specifies where backups are stored and managed

For more information about general backup settings, see the [Configuration](Configuration) page. 