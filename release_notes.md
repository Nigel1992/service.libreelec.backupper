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
