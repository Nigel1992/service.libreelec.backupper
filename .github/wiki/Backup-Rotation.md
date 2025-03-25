# Backup Rotation Feature

## Overview
The backup rotation feature helps manage your backup files by automatically maintaining a specified number of backups. However, please note that this feature will delete **any** ZIP files in your backup location, not just those created by the addon.

## ⚠️ Important Warning
- This feature will delete **ALL** ZIP files in your chosen backup location that don't match your rotation strategy
- It does not distinguish between backup files and other ZIP files
- It's strongly recommended to use a dedicated folder for your backups

## How It Works
1. When enabled, the feature will:
   - Keep only the specified number of backups (5-50)
   - Delete other ZIP files based on your chosen strategy:
     - **Keep Newest**: Keeps the most recent backups, deletes older ones
     - **Keep Oldest**: Keeps the oldest backups, deletes newer ones
     - **Keep Both Ends**: Keeps both oldest and newest backups, deletes middle ones

## Best Practices
1. Create a dedicated folder for your backups:
   - Local example: `/storage/backups/libreelec`
   - Remote example: `backups/libreelec` on your NAS/WebDAV/etc.
2. Never store other ZIP files in the backup location
3. Check your rotation strategy and max backups setting before enabling

## Example Setup
1. Create a new folder specifically for backups
2. Set this as your backup location in the addon settings
3. Enable rotation and choose your strategy
4. Set maximum number of backups to keep

## Safety Tips
- Test the rotation feature with unimportant files first
- Keep critical backups in a different location
- Regularly verify your backup files 