# LibreELEC Backupper v1.4.1.5 - Test Release (2026-01-05)

## Fixed Issues

### NFS Remote Backup Issues
- **Fixed NFS browsing**: Improved user feedback and validation when setting NFS paths
- **Enhanced error handling**: Better validation of NFS path formats with clear error messages
- **Improved connection testing**: More detailed NFS connection test results

### SMB Remote Backup Issues
- **Fixed SMB path handling**: Corrected path format conversion from Kodi's browser to internal storage
- **Fixed backup creation**: SMB backups now properly create files instead of failing silently
- **Improved URL construction**: Proper SMB URL formatting for all operations

### Local Backup Issues
- **Enhanced path validation**: Local backup paths containing invalid characters (like ':') are now properly detected and reset
- **Better NFS mount support**: Improved handling of local paths pointing to NFS mounts

### User Interface Issues
- **Fixed View Backups**: Now shows a proper list of available backups instead of remote browser dialogues
- **Fixed Restore Backup**: Displays backup selection interface with dates and sizes
- **Enhanced backup listing**: Shows backup creation dates, file sizes, and proper selection dialogs

### Remote Protocol Support
- **Complete remote protocol support**: `get_all_backups()` now works with NFS, SMB, FTP, SFTP, and WebDAV
- **Improved error handling**: Better error messages and fallback behavior for all protocols

## Technical Changes

### Core Files Modified
- `resources/lib/backup_utils.py`: Enhanced backup listing, path validation, SMB URL handling
- `resources/lib/remote_browser.py`: Improved NFS browsing, SMB path conversion, user feedback
- `addon.py`: Complete rewrite of backup viewing/restoration interface
- `addon.xml`: Version bump and changelog update

### Key Improvements
1. **Backup Discovery**: All remote protocols now properly list available backups
2. **Path Validation**: Prevents invalid paths from causing silent failures
3. **User Experience**: Clear feedback and proper dialog flows
4. **Error Handling**: Comprehensive error handling for all operations

## Testing

Please test the following scenarios:
1. **NFS Remote Backups**: Browse, test connection, create backups
2. **SMB Remote Backups**: Path setting, backup creation, file listing
3. **Local Backups**: Path validation, NFS mount compatibility
4. **View/Restore Operations**: Proper backup listing and selection
5. **Settings**: Remote type switching and path validation

## Known Issues
- WebDAV timestamp sorting may not work perfectly
- FTP/SFTP may have limited timestamp information in backup lists

## Installation
Install as a standard Kodi addon zip file.

---
*This is a test release. Please report any issues found during testing.*
