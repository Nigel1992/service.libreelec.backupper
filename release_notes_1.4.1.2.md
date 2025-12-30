# LibreELEC Backupper v1.4.1.2

## What's New in 1.4.1.2 (December 30, 2025)

### 🐛 Bug Fixes
- **Fixed restore from backup failing due to read-only file system error**
  - Added automatic mounting/unmounting of addons directory during restore operations
  - Fixed path resolution for addons and repository files during restore
  - Restore now properly handles read-only filesystems on LibreELEC systems
  - Improved error handling for filesystem mount operations

### 🔧 Technical Improvements
- Added `mount_addons_rw()` and `mount_addons_ro()` methods to handle addons directory mounting
- Enhanced `restore_file()` method to detect and handle addons directory restoration
- Fixed path resolution in `restore_backup()` to correctly map addons paths to `kodi_home/addons`
- Improved filesystem mount detection and error reporting

## Issue Fixed
This release fixes GitHub issue #1: "Restore from backup not working due to Read-only file system"

The restore process was failing when trying to restore addons because the addons directory was mounted as read-only. The addon now automatically:
1. Detects when restoring addons
2. Mounts the addons directory as read-write
3. Performs the restore operation
4. Remounts the directory as read-only

## Installation
1. Download the latest release
2. Install through Kodi's Add-on Manager
3. The fix will automatically apply to all restore operations

## Support
If you encounter any issues, please:
1. Check the [Troubleshooting Guide](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Troubleshooting)
2. Report bugs on our [Issues Page](https://github.com/Nigel1992/service.libreelec.backupper/issues)

Thank you for using LibreELEC Backupper!

