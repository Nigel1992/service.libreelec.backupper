# Initial Release of LibreELEC Backupper v1.0.0
Full backup and restore functionality with automated scheduling support. Compatible with LibreELEC 12.0.2 and Kodi 20 (Nexus). See README.md for complete features and documentation.

Release version 1.1.0 includes:

- Simplified backup items focusing on essential components
- Improved WebDAV connection handling to prevent '429 Too Many Requests' errors by:
  - Adding connection pooling
  - Implementing retry logic with exponential backoff
  - Maintaining persistent sessions
  - Proper resource cleanup
- Comprehensive wiki documentation
- Various bug fixes and improvements

# Version 1.1.0

Changes:
- Fixed settings labels for Configuration Files and Test Connection
- Improved backup process with proper compression level handling
- Removed schedule-related code and settings
- Made ZIP creation mandatory for all backups
- Fixed GitHub Actions workflow to properly check addon
- Fixed issue with large temporary files (100+ GB) in userdata directory by implementing proper cleanup
- Made backup/restore notifications stay on screen until operation completes

⚠️ CRITICAL WARNING ⚠️
The restore functionality may cause Kodi to crash when restoring backups that contain items requiring read/write access (such as add-on user data and settings). This is a known issue that will be fixed in an upcoming release.

Safety Precautions:
1. ALWAYS test restore functionality in a safe environment first
2. Be cautious when selecting items to backup/restore that require read/write access
3. If possible, avoid restoring add-on user data and settings until this issue is fixed
4. Make sure to have a separate backup of your system before attempting any restore operations

This issue primarily affects:
- Add-on User Data and Settings
- Other items requiring read/write access during restore

A fix is being developed and will be included in the next release.
