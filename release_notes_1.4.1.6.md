# LibreELEC Backupper v1.4.1.6 - Test Release (2026-01-09)

## Fixed Issues

- **Test Connection crash**: `RemoteBrowser` now initializes the password field before any test runs, fixing the `"RemoteBrowser" object had no attribute "password"` error seen in v1.4.1.5
- **Remote backups**: `BackupManager` once again loads `remote_password` from settings so SMB/NFS/FTP/SFTP/WebDAV connections use the saved credentials instead of failing
- **Packaging**: Rebuilt the addon zip with the correct `service.libreelec.backupper/` folder structure for clean installs and upgrades
- **Verbose logging**: Added structured DEBUG logs across backup creation, restore, remote connections, and browse/test flows to aid troubleshooting

## Testing Checklist

1. Test Connection for SMB and NFS should open without AttributeErrors
2. Remote backups (SMB, NFS, SFTP/FTP, WebDAV) should authenticate using the stored password
3. Install the zip via Kodi Add-on Manager to confirm the structure is accepted

## Notes

- This is a **test release** aimed specifically at resolving the password handling regression introduced in 1.4.1.5
- Please share Kodi debug logs if any remote protocol still fails to connect or list backups
