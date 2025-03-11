# 📥 Installation Guide

## System Requirements

### Minimum Requirements
- LibreELEC 12.0 or higher
- Kodi 20 (Nexus)
- 50MB free storage space for the addon
- Additional space for backups (varies based on configuration)

### Recommended
- 1GB+ free storage space for backups
- Stable network connection for remote backups
- External storage device for backup redundancy

## Installation Methods

### Method 1: Direct Installation
1. Download the latest release from the [Releases page](https://github.com/Nigel1992/service.libreelec.backupper/releases)
2. Open Kodi on your LibreELEC system
3. Navigate to Add-ons → Install from zip file
4. If prompted, enable "Unknown sources" in Settings → System → Add-ons
5. Browse to the downloaded zip file
6. Select the file to begin installation
7. Wait for the "Add-on installed" notification

### Method 2: Repository Installation (Coming Soon)
1. Add the repository source to Kodi
2. Install from the repository
3. Automatic updates will be available

## First-Time Setup

### Initial Configuration
1. Go to Add-ons → Program add-ons
2. Find LibreELEC Backupper
3. Select Configure
4. Set up the following:
   - Backup location
   - Schedule (if desired)
   - Backup retention
   - Notification preferences

### Backup Location Setup
1. Choose a backup location:
   - Default: `/storage/backup`
   - External drive: `/storage/[device_name]/backup`
   - Network share: `smb://[path]/backup`
2. Ensure write permissions
3. Verify sufficient space

### Schedule Configuration
1. Enable scheduling if desired
2. Choose backup frequency:
   - Hourly
   - Daily
   - Weekly
3. Set preferred time
4. Configure retention policy

## Post-Installation Steps

### Verify Installation
1. Check addon status in Kodi
2. Verify settings are saved
3. Test backup location access
4. Run a test backup

### Security Considerations
- Review backup location permissions
- Secure network shares if used
- Consider backup encryption for sensitive data
- Set up backup redundancy if needed

### Troubleshooting
If you encounter issues:
1. Check Kodi log for errors
2. Verify system requirements
3. Test write permissions
4. Consult the [FAQ](FAQ) page
5. Report issues on [GitHub](https://github.com/Nigel1992/service.libreelec.backupper/issues)

## Updating

### Manual Update
1. Download new version
2. Uninstall existing version (settings are preserved)
3. Install new version from zip
4. Verify settings after update

### Automatic Updates (Future)
- Enable automatic updates in Kodi
- Updates will install automatically
- Backup schedule continues uninterrupted

## Next Steps

After installation:
1. Review the [FAQ](FAQ) for common questions
2. Configure backup settings
3. Set up automated schedules
4. Test backup and restore functionality
5. Join the [community discussions](https://github.com/Nigel1992/service.libreelec.backupper/discussions) 