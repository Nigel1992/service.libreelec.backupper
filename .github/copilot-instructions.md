# LibreELEC Backupper - AI Coding Agent Instructions

## Project Overview
**LibreELEC Backupper** is a Kodi addon (service.libreelec.backupper) for automated backup/restore of LibreELEC system configuration, addons, and settings. It supports multiple remote storage protocols (SMB, NFS, FTP, SFTP, WebDAV).

**Key Version:** 1.4.1.5 | **Target:** Kodi 20+ | **Python:** 3.x with xbmc/xbmcaddon modules

---

## Architecture & Critical Patterns

### Component Structure
- **`addon.py`** - Main addon entry point, handles UI actions (backup_now, restore, test_connection, browse_remote)
- **`service.py`** - Background scheduler service that runs backup tasks automatically on schedule
- **`resources/lib/backup_utils.py`** - Core `BackupManager` class handling backup/restore logic
- **`resources/lib/remote_browser.py`** - `RemoteBrowser` class for testing connections and browsing remote shares
- **`resources/lib/email_utils.py`** - `EmailNotifier` for sending backup status notifications
- **`resources/lib/settings_handler.py`** - Settings action handlers

### Critical Data Flows
1. **Backup Creation:** `addon.py` (user request) → `BackupManager.create_backup()` → creates tar.gz → uploads to remote via xbmcvfs
2. **Connection Testing:** `addon.py` (test_connection) → `RemoteBrowser.test_connection_with_params()` → protocol-specific test method
3. **Restore Operation:** `addon.py` (restore) → `BackupManager.restore_backup()` → downloads from remote → extracts → handles mount operations

### Key Classes & Their Attributes

**RemoteBrowser** (CRITICAL - must always initialize these):
```python
self.remote_type      # int: 0=SMB, 1=NFS, 2=FTP, 3=SFTP, 4=WebDAV
self.remote_path      # str: server/path or server:/path
self.username         # str: credentials (can be empty)
self.password         # str: credentials (can be empty - THIS IS CRITICAL)
self.port            # str: port number (gets default if empty)
self.default_ports   # dict: protocol→default port mapping
```

**BackupManager**:
```python
self.backup_dir      # str: local backup directory path
self.profile_path    # str: Kodi profile path
self.addon           # xbmcaddon.Addon instance
self.remote_browser  # RemoteBrowser instance
```

---

## Essential Patterns & Conventions

### Logging Standards
- **ALWAYS** use verbose logging at DEBUG level for detailed information
- Use the log pattern: `xbmc.log(f"{ADDON_ID}: Message here", xbmc.LOGINFO|LOGDEBUG|LOGERROR)`
- Log at function entry for debugging flows, connection attempts, and before operations that might fail
- CRITICAL: Remote connection test failures must log all connection parameters for troubleshooting

### Attribute Initialization Requirement
**NEVER** assume attributes exist without initializing them. The `RemoteBrowser` class MUST:
1. Initialize all attributes in `__init__` with default values BEFORE calling `reload_settings()`
2. Wrap `reload_settings()` in try-except in `__init__` to catch and log errors
3. In `reload_settings()`, ensure attributes are set even if exceptions occur during settings load

**Example:**
```python
def __init__(self):
    # Initialize with defaults FIRST
    self.password = ""
    self.remote_path = ""
    # Then try to reload
    try:
        self.reload_settings()
    except Exception as e:
        xbmc.log(f"Error: {e}", xbmc.LOGERROR)
```

### Remote Connection Testing
- All test methods (`_test_smb_connection`, `_test_nfs_connection`, etc.) must:
  - Log connection parameters at DEBUG level
  - Wrap operations in try-except with detailed error logging
  - Show detailed error messages to users in textviewer dialogs
  - Handle credentials being optional (no password required scenarios)

### Path Formatting
- **SMB:** `server/share` or `server/share/subpath` (no smb:// prefix in path storage)
- **NFS:** `server:/export/path` (colon is REQUIRED separating server and path)
- **FTP/SFTP:** `server/path`

### Settings Handling
- Always call `xbmc.executebuiltin('UpdateLocalAddons')` after changing settings in code
- Settings are loaded via `ADDON.getSetting('key')` - returns strings, use int() for type conversion
- Use `reload_settings()` in RemoteBrowser to ensure fresh values from Kodi

---

## Common Bug Patterns & Fixes

### Attribute Error: 'RemoteBrowser' object has no attribute 'password'
**Root Cause:** Attributes not initialized in `__init__` before calling `reload_settings()`
**Fix:** Initialize all attributes with empty defaults in `__init__` BEFORE `reload_settings()`

### NFS Mount Failures
**Common Issues:**
- Path format missing colon (needs `server:/path`, not `server/path`)
- Missing `-o nolock` option in mount command for better compatibility
- No temp mount point cleanup between attempts

**Pattern to follow:**
```python
mount_options = ["-t", "nfs", "-o", "soft,timeo=10,retrans=2,nolock"]
subprocess.call(["mount"] + mount_options + [nfs_path, mount_point])
```

### SMB Path Handling
- When browsing, convert back from protocol format to storage format
- Store as `server/share`, not `smb://server/share`
- Convert to full SMB URL only when connecting: `smb://[user:pass@]server/share`

---

## Development Workflow

### Testing Connection Logic
Use the included `test_fix.py` for unit testing RemoteBrowser without Kodi:
```bash
cd /home/nigel/service.libreelec.backupper
python3 test_fix.py
```

### Key Files to Check Before Changes
- **`addon.xml`** - For addon version, dependencies, and settings metadata
- **`resources/settings.xml`** - For available settings names and defaults
- **`changelog.txt`** - For version history and known issues
- **`service.py`** - To understand scheduler timing logic if modifying backup triggers

### Adding New Remote Protocol Support
1. Add protocol option to `addon.xml` settings
2. Add case handler in `test_connection()` method
3. Create `_test_protocol_connection()` method with proper logging
4. Update `reload_settings()` default_ports dict if needed
5. Update error messages to mention the new protocol

---

## Kodi/LibreELEC Specifics

### Important Module Constants
- `xbmc.LOGINFO, LOGDEBUG, LOGERROR, LOGWARNING` - Log levels
- Settings stored in `xbmc.translatePath(ADDON.getAddonInfo('profile'))`
- Paths use `xbmcvfs.translatePath()` for cross-platform compatibility

### Remote Browsing with xbmcvfs
- SMB: `xbmcvfs.listdir("smb://server/share")` returns `(dirs, files)` tuple
- Local operations use standard `os` module
- Network operations use `xbmcvfs` for Kodi-compatible path handling

### Dialog Types in Code
- `xbmcgui.Dialog().ok()` - Simple message dialogs
- `xbmcgui.Dialog().textviewer()` - Scrollable text display (use for connection test results)
- `xbmcgui.DialogProgress()` - Progress dialog with `.create()`, `.update()`, `.close()`

---

## Performance & Reliability Considerations

1. **Connection Tests** - Always provide timeout handling; use low timeouts for remote tests
2. **Large Backups** - Show progress dialogs; allow user cancellation
3. **Path Validation** - Validate paths exist and are accessible before creating backups
4. **Error Recovery** - Clean up temp mount points, temp files on exception
5. **Settings Persistence** - Always reload settings before operations; settings may change in settings UI

---

## DO NOT DO

- ❌ Assume attributes exist without initializing them
- ❌ Use unescaped passwords in logs (log "Set" or "Not Set" instead)
- ❌ Forget to call `xbmc.executebuiltin('UpdateLocalAddons')` after setting changes
- ❌ Mix smb:// protocol prefix in stored paths (store as server/share only)
- ❌ Mount NFS without the `nolock` option
- ❌ Leave temp mount points or test directories without cleanup
- ❌ Show detailed error messages without logging the same details to xbmc.log
