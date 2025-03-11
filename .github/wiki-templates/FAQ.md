# ❓ Frequently Asked Questions (FAQ)

## General Questions

### What is LibreELEC Backupper?
LibreELEC Backupper is an addon that provides automated backup functionality for your LibreELEC system configuration, add-ons, and user data.

### Which LibreELEC versions are supported?
The addon is compatible with LibreELEC 12.0+ and Kodi 20 (Nexus).

### Is it safe to use?
Yes, the addon is designed with safety in mind. It performs verification checks before and after backups, and includes error recovery mechanisms.

## Backup Questions

### Where are my backups stored?
By default, backups are stored in `/storage/backup`. You can change this location in the addon settings.

### How often should I create backups?
We recommend:
- Daily backups for systems with frequent changes
- Weekly backups for stable systems
- Monthly backups for minimal-change setups

### What gets backed up?
The addon can backup:
- System configuration files
- Add-on settings and data
- User preferences
- Custom keymaps
- Sources and playlists
- User profiles

### How much space do backups require?
Space requirements vary based on:
- Number of installed add-ons
- Amount of user data
- Backup retention settings
- Media file inclusion settings

## Configuration Questions

### How do I change backup settings?
1. Go to Add-ons → Program add-ons
2. Find LibreELEC Backupper
3. Select Configure
4. Modify desired settings

### Can I schedule automatic backups?
Yes, you can schedule:
- Hourly backups
- Daily backups
- Weekly backups
Set your preferred schedule in the addon settings.

### How many backups are kept?
By default, the addon keeps 10 most recent backups. You can adjust this in settings.

## Troubleshooting

### Backup Failed - What Should I Do?
1. Check available storage space
2. Verify write permissions
3. Review error messages in Kodi log
4. Try reducing backup scope
5. Contact support if issues persist

### System Slow After Backup?
- Enable automatic cleanup in settings
- Reduce backup retention count
- Exclude unnecessary files
- Schedule backups during off-peak hours

### Missing Files in Backup?
- Check file permissions
- Verify backup location is accessible
- Ensure sufficient storage space
- Review backup scope settings

## Support

### Where can I get help?
- [Report issues on GitHub](https://github.com/Nigel1992/service.libreelec.backupper/issues)
- [Request features](https://github.com/Nigel1992/service.libreelec.backupper/issues)
- [Join discussions](https://github.com/Nigel1992/service.libreelec.backupper/discussions)
- Review documentation in [Wiki](https://github.com/Nigel1992/service.libreelec.backupper/wiki)

### How can I contribute?
- Submit bug reports
- Suggest new features
- Contribute code improvements
- Help improve documentation

## Advanced Usage

### Can I customize what gets backed up?
Yes, you can:
- Select specific configuration files
- Choose which add-ons to include
- Filter user data
- Exclude specific directories

### Is there a command-line interface?
Yes, advanced users can:
- Trigger backups via CLI
- Automate with custom scripts
- Integrate with system tools
- Schedule custom backup tasks 