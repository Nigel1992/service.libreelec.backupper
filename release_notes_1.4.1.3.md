# LibreELEC Backupper v1.4.1.3 - TEST RELEASE

## ⚠️ TEST RELEASE

This is a **TEST RELEASE** to fix multiple remote backup location issues. Please test thoroughly before using in production.

## What's New in 1.4.1.3 (December 30, 2025)

### 🐛 Bug Fixes

#### NFS Connection Issues
- **Fixed NFS path format handling** - NFS now requires proper format: `server:/export/path`
- Added automatic path format conversion and validation
- Improved NFS mount options with soft mount and timeout settings
- Better error messages with format examples

#### SMB Browsing Issues
- **Fixed SMB browsing** - Now properly handles manually entered paths
- Improved SMB URL construction to handle empty username/password
- Better path validation for SMB connections

#### Local Location Issues
- **Fixed local location with NFS path bug** - Prevents network protocols (nfs:, smb:, etc.) in local paths
- Automatically resets invalid local paths to default location
- Added validation to detect and prevent network protocols in local mode

#### SFTP Improvements
- **Enhanced SFTP error messages** - Better handling when paramiko module is not available
- Improved error dialogs with solutions and alternatives
- Still allows manual path entry even if paramiko is unavailable

### 🔧 Technical Improvements

- **Path Format Validation** - Added format hints and validation for all remote protocols
- **Auto-save Settings** - Settings now save immediately when changed (no need to click OK)
- **Better Error Messages** - All error messages now include format examples and troubleshooting tips
- **Improved NFS Mounting** - Uses soft mount with timeout for better error handling

### 📝 Path Format Examples

#### NFS
- Format: `server:/export/path`
- Examples:
  - `192.168.1.100:/mnt/backups`
  - `nas.example.com:/export/share`

#### SMB
- Format: `server/share` or use Browse button
- Examples:
  - `192.168.1.100/backups`
  - `server/share/subfolder`

#### FTP/SFTP
- Format: `server/path`
- Examples:
  - `ftp.example.com/backups`
  - `server.example.com/home/user/backups`

## Issues Fixed

This release addresses multiple issues reported in GitHub:
- Unable to back up to remote NFS location
- SMB browsing not working with manually entered paths
- Local location accepting NFS paths incorrectly
- SFTP paramiko module error messages
- Settings not applying without clicking OK
- Missing path format hints

## Testing Required

Please test the following scenarios:
1. ✅ NFS remote backup with proper format (`server:/export/path`)
2. ✅ SMB remote backup with manually entered path
3. ✅ SMB remote backup using Browse button
4. ✅ Local backup location (should reject network protocols)
5. ✅ SFTP connection (with and without paramiko)
6. ✅ Settings auto-save functionality

## Installation

1. Download the test release
2. Install through Kodi's Add-on Manager
3. Test remote backup connections
4. Report any issues on GitHub

## Known Limitations

- NFS requires the exact format `server:/export/path` (colon is required)
- SFTP requires paramiko module for full functionality
- Some network configurations may require additional firewall rules

## Support

If you encounter any issues, please:
1. Check the [Troubleshooting Guide](https://github.com/Nigel1992/service.libreelec.backupper/wiki/Troubleshooting)
2. Report bugs on our [Issues Page](https://github.com/Nigel1992/service.libreelec.backupper/issues)
3. Include error messages and path formats used

Thank you for testing LibreELEC Backupper!

