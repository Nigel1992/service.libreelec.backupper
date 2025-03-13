# Troubleshooting Guide

This guide helps resolve common issues with LibreELEC Backupper.

## Connection Issues

### Remote Storage Problems
1. **Can't Connect to Remote Storage**
   - Verify network connection
   - Check credentials
   - Confirm server is online
   - Test with correct port

2. **SMB Connection Fails**
   - Check share permissions
   - Verify Windows networking
   - Try IP instead of hostname
   - Check SMB version compatibility

3. **FTP/SFTP Issues**
   - Verify port numbers
   - Check firewall settings
   - Confirm credentials
   - Test with passive mode

## Storage Issues

### Space Problems
1. **Not Enough Space**
   - Clean old backups
   - Use higher compression
   - Free up system storage
   - Check available space

2. **Can't Write to Location**
   - Check permissions
   - Verify path exists
   - Test write access
   - Check disk health

## Backup Issues

### Creation Problems
1. **Backup Fails to Start**
   - Check addon permissions
   - Verify settings
   - Restart Kodi
   - Check system resources

2. **Backup Incomplete**
   - Check available space
   - Verify network stability
   - Monitor system logs
   - Try smaller backup set

## Restore Issues

### Restore Problems
1. **Can't Find Backup**
   - Check backup location
   - Verify file exists
   - Check file permissions
   - Try alternative location

2. **Restore Fails**
   - Check backup integrity
   - Verify system space
   - Review error logs
   - Try alternative backup

## System Issues

### Performance
1. **Slow Backup/Restore**
   - Check system load
   - Verify network speed
   - Adjust compression
   - Close other applications

2. **System Unresponsive**
   - Monitor resource usage
   - Check log files
   - Restart if necessary
   - Reduce backup size

## Error Messages

### Common Errors
1. **"Access Denied"**
   - Check permissions
   - Verify credentials
   - Test with different user
   - Check SELinux/AppArmor

2. **"Network Unreachable"**
   - Check connectivity
   - Verify DNS settings
   - Test with IP address
   - Check VPN if used

## Recovery Steps

### When All Else Fails
1. **Reset Addon Settings**
   - Clear addon data
   - Reconfigure settings
   - Test with minimal config
   - Gradually add features

2. **Manual Recovery**
   - Access backup files directly
   - Copy files manually
   - Check file permissions
   - Document changes

## Getting Help

If issues persist:
1. Check [GitHub Issues](https://github.com/Nigel1992/service.libreelec.backupper/issues)
2. Post on [LibreELEC Forum](https://forum.libreelec.tv/)
3. Include:
   - Error messages
   - System logs
   - Steps to reproduce
   - System configuration 