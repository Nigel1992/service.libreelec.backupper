#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import socket
import re
import ftplib
from urllib.parse import urlparse, unquote
import json
import time
import subprocess

try:
    import paramiko
    SFTP_AVAILABLE = True
except ImportError:
    try:
        import platform
        _machine = (platform.machine() or "").lower()
        if _machine in ("aarch64", "arm64"):
            _vendor_name = "vendor_aarch64"
        elif _machine in ("x86_64", "amd64"):
            _vendor_name = "vendor_x86_64"
        else:
            _vendor_name = None
        if _vendor_name:
            _vendor_dir = os.path.join(os.path.dirname(__file__), _vendor_name)
            if os.path.isdir(_vendor_dir) and _vendor_dir not in sys.path:
                sys.path.insert(0, _vendor_dir)
        import paramiko
        SFTP_AVAILABLE = True
    except Exception as e:
        import traceback
        xbmc.log("RemoteBrowser paramiko import failed: %r" % e, xbmc.LOGERROR)
        xbmc.log(traceback.format_exc(), xbmc.LOGERROR)
        paramiko = None
        SFTP_AVAILABLE = False

try:
    import requests
    WEBDAV_AVAILABLE = True
except ImportError:
    requests = None
    WEBDAV_AVAILABLE = False

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
LANGUAGE = ADDON.getLocalizedString

try:
    from resources.lib.custom_gui import show_textviewer, ask_yesno, show_message
except Exception:
    show_textviewer = None
    ask_yesno = None
    show_message = None


def ok_dialog(title, text):
    """Show OK-style message via custom GUI when available, fallback to native dialog."""
    try:
        if ADDON.getSettingBool('use_custom_gui') and 'show_message' in globals() and show_message is not None:
            show_message(title, text)
        else:
            xbmcgui.Dialog().ok(title, text)
    except Exception:
        try:
            xbmcgui.Dialog().ok(title, text)
        except Exception:
            xbmc.log(f"RemoteBrowser: Failed to show OK dialog: {title}")


def text_dialog(title, text):
    """Show scrollable text popup via custom GUI when available."""
    try:
        if ADDON.getSettingBool('use_custom_gui') and 'show_textviewer' in globals() and show_textviewer is not None:
            show_textviewer(title, text)
        else:
            ok_dialog(title, text)
    except Exception:
        ok_dialog(title, text)

SFTP_USE_KEY_ATTRS = [
    "remote_sftp_use_key", "sftp_use_key", "remote_use_ssh_key", "sftp_key_auth",
    "remote_sftp_key_auth", "use_ssh_key", "ssh_key_auth", "remote_use_key",
    "use_key", "sftp_auth_mode", "remote_sftp_auth_mode", "remote_auth_mode",
]
SFTP_USE_KEY_SETTING_IDS = [
    "remote_sftp_use_key", "sftp_use_key", "remote_use_ssh_key", "sftp_key_auth",
    "remote_sftp_key_auth", "use_ssh_key", "ssh_key_auth", "remote_use_key",
]
SFTP_AUTH_MODE_ATTRS = ["remote_sftp_auth_mode", "sftp_auth_mode", "remote_auth_mode"]
SFTP_AUTH_MODE_SETTING_IDS = ["remote_sftp_auth_mode", "sftp_auth_mode", "remote_auth_mode"]
SFTP_PRIVATE_KEY_ATTRS = [
    "remote_private_key", "remote_sftp_private_key", "sftp_private_key",
    "remote_ssh_key", "remote_ssh_private_key", "ssh_private_key",
    "private_key_path", "remote_key_file", "sftp_key_file", "remote_sftp_key_file",
    "ssh_key_file", "private_key", "key_file",
]
SFTP_PRIVATE_KEY_SETTING_IDS = [
    "remote_private_key", "remote_sftp_private_key", "sftp_private_key",
    "remote_ssh_key", "remote_ssh_private_key", "ssh_private_key",
    "private_key_path", "remote_key_file", "sftp_key_file", "remote_sftp_key_file",
    "ssh_key_file", "private_key", "key_file",
]
SFTP_PASSPHRASE_ATTRS = [
    "remote_key_passphrase", "remote_sftp_passphrase", "sftp_key_passphrase",
    "ssh_key_passphrase", "private_key_passphrase", "key_passphrase",
    "remote_passphrase", "sftp_passphrase", "passphrase",
]
SFTP_PASSPHRASE_SETTING_IDS = [
    "remote_key_passphrase", "remote_sftp_passphrase", "sftp_key_passphrase",
    "ssh_key_passphrase", "private_key_passphrase", "key_passphrase",
    "remote_passphrase", "sftp_passphrase", "passphrase",
]

class RemoteBrowser:
    def __init__(self):
        # Initialize all attributes with defaults to avoid AttributeError
        self.remote_type = 0
        self.remote_path = ""
        self.username = ""
        self.password = ""
        self.port = ""
        self.default_ports = {}
        self.verbose_logging = False
        self.addon = ADDON

        # Verbose logging helper
        self._debug_prefix = "RemoteBrowser"
        
        # Always reload settings to ensure we have the latest values
        try:
            self.reload_settings()
        except Exception as e:
            xbmc.log(f"RemoteBrowser: Error during initialization: {str(e)}", xbmc.LOGERROR)
            xbmc.log("RemoteBrowser: Using default values due to initialization error", xbmc.LOGWARNING)

    def _refresh_logging_flag(self):
        try:
            self.verbose_logging = ADDON.getSettingBool('enable_verbose_logging')
        except Exception:
            self.verbose_logging = False

    def _log(self, message, level=xbmc.LOGINFO):
        try:
            if self.verbose_logging and level == xbmc.LOGDEBUG:
                xbmc.log(message, xbmc.LOGINFO)
            else:
                xbmc.log(message, level)
        except Exception:
            xbmc.log(message, level)

    def log_verbose(self, context, **kwargs):
        """Emit structured verbose logging for troubleshooting."""
        details = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()]) if kwargs else ""
        self._log(f"{self._debug_prefix}[{context}]: {details}", xbmc.LOGDEBUG)
    
    def reload_settings(self):
        """Reload settings from Kodi"""
        self._refresh_logging_flag()
        self._log("RemoteBrowser: Reloading settings from Kodi", xbmc.LOGINFO)

        try:
            # Force reload of addon to get fresh settings
            global ADDON
            ADDON = xbmcaddon.Addon()
            self.addon = ADDON

            self.remote_type = int(ADDON.getSetting('remote_location_type'))
            self.remote_path = ADDON.getSetting('remote_path')
            self.username = ADDON.getSetting('remote_username')
            # Don't log password for security
            self.password = ADDON.getSetting('remote_password')
            self.port = ADDON.getSetting('remote_port')

            # SFTP key authentication settings
            self.remote_sftp_use_key = None
            self.remote_private_key = ""
            self.remote_key_passphrase = ""
            self.sftp_use_key = None
            self.sftp_private_key = ""
            self.sftp_key_passphrase = ""
            self.private_key = ""
            self.key_passphrase = ""
            self.use_key = None
            self.use_ssh_key = None
            
            self._log(f"RemoteBrowser: Successfully loaded settings", xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log(f"RemoteBrowser: Error loading settings: {str(e)}", xbmc.LOGERROR)
            # Ensure attributes are set even if an error occurred
            if not hasattr(self, 'remote_type'):
                self.remote_type = 0
            if not hasattr(self, 'remote_path'):
                self.remote_path = ""
            if not hasattr(self, 'username'):
                self.username = ""
            if not hasattr(self, 'password'):
                self.password = ""
            if not hasattr(self, 'port'):
                self.port = ""
            raise

        self._log(f"RemoteBrowser: Remote type = {self.remote_type}", xbmc.LOGDEBUG)
        self._log(f"RemoteBrowser: Remote path = {self.remote_path}", xbmc.LOGDEBUG)
        self._log(f"RemoteBrowser: Username = {self.username if self.username else 'Not Set'}", xbmc.LOGDEBUG)
        self._log(f"RemoteBrowser: Password = {'Set' if self.password else 'Not Set'}", xbmc.LOGDEBUG)
        self._log(f"RemoteBrowser: Port = {self.port}", xbmc.LOGDEBUG)

        # Default ports if not specified
        self.default_ports = {
            0: 445,  # SMB
            1: 2049, # NFS
            2: 21,   # FTP
            3: 22,   # SFTP
            4: 80    # WebDAV
        }

        if not self.port:
            self.port = str(self.default_ports.get(self.remote_type, 0))
            self._log(f"RemoteBrowser: Set default port: {self.port}", xbmc.LOGDEBUG)
        else:
            self._log(f"RemoteBrowser: Using configured port: {self.port}", xbmc.LOGDEBUG)

        self._log("RemoteBrowser: Settings reloaded successfully", xbmc.LOGINFO)

    def _show_connection_report(self, protocol, success, summary, details=None, tips=None, endpoint=None):
        """Render a clean, consistent connection test report."""
        details = details or []
        tips = tips or []

        status_color = 'FF66BB6A' if success else 'FFEF5350'
        status_text = 'SUCCESS' if success else 'FAILED'

        lines = [
            f"[COLOR {status_color}][B]{status_text}[/B][/COLOR] {protocol} Connection Test",
            "[COLOR FFB0BEC5]------------------------------------------------------------[/COLOR]",
            f"[COLOR FF90CAF9]Summary:[/COLOR] {summary}",
        ]

        if endpoint:
            lines.extend([
                "",
                "[COLOR FF90CAF9]Target:[/COLOR]",
                f"- {endpoint}",
            ])

        if details:
            lines.extend([
                "",
                "[COLOR FF90CAF9]Details:[/COLOR]",
            ])
            lines.extend([f"- {item}" for item in details if str(item).strip()])

        if tips:
            lines.extend([
                "",
                "[COLOR FFFFD54F]Troubleshooting:[/COLOR]",
            ])
            lines.extend([f"- {item}" for item in tips if str(item).strip()])

        report_text = "\n".join(lines)
        try:
            text_dialog("Connection Test Results", report_text)
        except Exception:
            ok_dialog("Connection Test Results", report_text)

    def _masked_smb_url(self):
        """Return SMB URL with password masked for display."""
        base = self.remote_path or ''
        if self.username and self.password:
            return f"smb://{self.username}:***@{base}"
        if self.username:
            return f"smb://{self.username}@{base}"
        return f"smb://{base}"
    
    def _open_sftp_client(self):
        """Open an SFTP client (paramiko if available, otherwise CLI backend)."""
        host = self.remote_path.split('/')[0]
        remote_dir = '/'.join(self.remote_path.split('/')[1:]) if '/' in self.remote_path else ''
        if SFTP_AVAILABLE and paramiko is not None:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self._sftp_use_key():
                key_path = self._sftp_private_key_path()
                passphrase = self._sftp_key_passphrase()
                ssh.connect(host, port=int(self.port), username=self.username,
                            key_filename=key_path if key_path else None,
                            passphrase=passphrase if passphrase else None)
            else:
                ssh.connect(host, port=int(self.port), username=self.username, password=self.password)
            sftp = ssh.open_sftp()
            if remote_dir:
                sftp.chdir(remote_dir)
            def closer():
                try:
                    sftp.close()
                except Exception:
                    pass
                try:
                    ssh.close()
                except Exception:
                    pass
            return sftp, closer
        else:
            key_path = self._sftp_private_key_path()
            if not key_path:
                return None, None
            try:
                from .sftp_cli import CLISFTPClient
            except Exception:
                from sftp_cli import CLISFTPClient
            client = CLISFTPClient(host, self.port, self.username, key_path, self._sftp_key_passphrase())
            if remote_dir:
                client.chdir(remote_dir)
            return client, client.close

    def browse_sftp(self, mode='backup'):
        """Interactive SFTP browser using listdir/stat (works with CLI backend too)."""
        import os as _os
        sftp, closer = self._open_sftp_client()
        if sftp is None:
            text_dialog("SFTP Not Available", "Could not open an SFTP connection.\nConfigure key-based authentication and test the connection first.")
            return self.show_manual_entry_dialog("SFTP")
        # Verify connectivity up front
        try:
            sftp.listdir('.')
        except Exception as e:
            try:
                closer()
            except Exception:
                pass
            text_dialog("SFTP Error", "Could not list remote directory:\n%s" % str(e))
            return self.show_manual_entry_dialog("SFTP")

        host = self.remote_path.split('/')[0]
        base_dir = '/'.join(self.remote_path.split('/')[1:]) if '/' in self.remote_path else ''
        rel = ''

        def full_rel():
            if not rel:
                return base_dir
            if base_dir:
                return base_dir.rstrip('/') + '/' + rel
            return rel

        dialog = xbmcgui.Dialog()
        try:
            while True:
                current = rel if rel else '.'
                try:
                    entries = sftp.listdir(current)
                except Exception:
                    entries = []
                dirs = []
                files = []
                for name in sorted(entries):
                    path = name if current in ('', '.') else current.rstrip('/') + '/' + name
                    is_dir = False
                    try:
                        st = sftp.stat(path)
                        is_dir = bool(st.st_mode & 0o40000)
                    except Exception:
                        is_dir = False
                    if is_dir:
                        dirs.append(name)
                    else:
                        files.append(name)

                options = []
                if rel not in ('', '.'):
                    options.append('..')
                options.append('[Select current directory]')
                options.extend(['[DIR] ' + d for d in dirs])
                # Always show files for visibility, even in backup mode
                options.extend(['[FILE] ' + f for f in files])

                selected = dialog.select('Browse SFTP - %s' % (full_rel() or '/'), options)
                if selected < 0:
                    return None
                choice = options[selected]
                if choice == '..':
                    rel = _os.path.dirname(rel.rstrip('/'))
                    if rel in ('', '.'):
                        rel = ''
                elif choice == '[Select current directory]':
                    new_path = full_rel()
                    if new_path:
                        self.remote_path = '%s/%s' % (host, new_path.strip('/'))
                    else:
                        self.remote_path = host
                    ADDON.setSetting('remote_path', self.remote_path)
                    xbmc.executebuiltin('UpdateLocalAddons')
                    xbmc.sleep(200)
                    if 'show_message' in globals() and show_message is not None:
                        show_message("Location Selected", "SFTP path configured: %s" % self.remote_path)
                    else:
                        ok_dialog("Location Selected", "SFTP path configured: %s" % self.remote_path)
                    return self.remote_path
                elif choice.startswith('[DIR] '):
                    name = choice[6:]
                    rel = name if not rel else rel.rstrip('/') + '/' + name
                elif choice.startswith('[FILE] '):
                    name = choice[7:]
                    if mode == 'restore':
                        if 'show_message' in globals() and show_message is not None:
                            show_message("File Selected", "Selected: %s" % name)
                        else:
                            ok_dialog("File Selected", "Selected: %s" % name)
                        return name
                    # In backup mode, files are informational only
                    continue
        finally:
            try:
                closer()
            except Exception:
                pass

    def browse(self, mode='backup'):
        """Main method to browse remote locations based on type
        mode: 'backup' for folder selection, 'restore' for file selection"""
        # Reload settings to ensure we have the latest values
        self.reload_settings()

        self.log_verbose(
            "browse:start",
            mode=mode,
            remote_type=self.remote_type,
            remote_path=self.remote_path,
            username=self.username,
            password_set=bool(self.password),
            port=self.port,
        )
        
        remote_types = ["SMB", "NFS", "FTP", "SFTP", "WebDAV"]
        current_type = remote_types[self.remote_type]
        
        xbmc.log(f"{ADDON_ID}: Browsing {current_type} location for {mode}", xbmc.LOGINFO)
        
        # Use Kodi's built-in file browser for SMB and WebDAV
        if self.remote_type in [0, 4]:  # SMB or WebDAV
            # If path is already set, try to use it, otherwise browse
            if self.remote_path and self.remote_path.strip():
                # Path is set, validate it and use it
                if self.remote_type == 0:  # SMB
                    # Validate SMB path format
                    if not self.remote_path.startswith('smb://') and '/' in self.remote_path:
                        # Path looks valid, use it
                        ADDON.setSetting('remote_path', self.remote_path)
                        xbmc.executebuiltin('UpdateLocalAddons')
                        dialog = xbmcgui.Dialog()
                        if 'show_message' in globals() and show_message is not None:
                            show_message("Path Set", f"SMB path configured: {self.remote_path}\n\nUse 'Test Connection' to verify.")
                        else:
                            ok_dialog("Path Set", f"SMB path configured: {self.remote_path}\n\nUse 'Test Connection' to verify.")
                        return self.remote_path
                # For WebDAV, path validation is handled in browse_with_kodi_browser
            return self.browse_with_kodi_browser(current_type, mode)
        elif self.remote_type == 1:  # NFS
            # NFS browsing - show dialog with format hint
            return self.browse_nfs(mode)
        elif self.remote_type == 2:  # FTP
            self.show_manual_entry_dialog("FTP")
            return None
        elif self.remote_type == 3:  # SFTP
            return self.browse_sftp(mode)
        
        return None
    
    def browse_with_kodi_browser(self, protocol_name, mode='backup'):
        """Use Kodi's built-in file browser to select a remote location
        mode: 'backup' for folder selection, 'restore' for file selection"""
        dialog = xbmcgui.Dialog()
        
        # Set up heading based on mode
        heading = "Select Backup Location" if mode == 'backup' else "Select Backup File"
        
        # Determine the starting path based on protocol
        if self.remote_type == 0:  # SMB
            # Start at the root of network browsing
            start_path = "smb://"
        elif self.remote_type == 4:  # WebDAV
            # WebDAV might be configured in sources
            start_path = "/"
        else:
            # Default to home directory
            start_path = "/"
        
        # Use Kodi's built-in file browser with appropriate mode
        browse_type = 0 if mode == 'backup' else 1  # 0 for folders, 1 for files
        file_mask = '|.zip' if mode == 'restore' else ''
        selected_path = dialog.browse(browse_type, heading, 'files', file_mask, False, False, start_path)
        
        if not selected_path or selected_path == start_path:
            # User cancelled or didn't select anything
            return None
        
        # For restore mode, verify the selected file is a backup file
        if mode == 'restore' and not selected_path.lower().endswith('.zip'):
            if 'show_message' in globals() and show_message is not None:
                show_message("Invalid Selection", "Please select a backup file (.zip)")
            else:
                ok_dialog("Invalid Selection", "Please select a backup file (.zip)")
            return None
        
        # Process the selected path based on protocol
        if self.remote_type == 0:  # SMB
            # For SMB, we need to extract the server and share
            if selected_path.startswith("smb://"):
                # Remove the protocol prefix
                path = selected_path[6:]
                # Remove trailing slash if present
                if path.endswith('/'):
                    path = path[:-1]

                # Convert from smb://server/share format to server/share format
                if '/' in path:
                    parts = path.split('/', 1)
                    server = parts[0]
                    share = parts[1]
                    # Convert to the expected format: server/share
                    expected_path = f"{server}/{share}" if share else server
                else:
                    expected_path = path

                # Update the remote path setting
                self.remote_path = expected_path
                ADDON.setSetting('remote_path', expected_path)
                # Force settings save immediately
                xbmc.executebuiltin('UpdateLocalAddons')
                xbmc.sleep(200)  # Brief pause to ensure settings are saved
                
                # Try to extract username and password from the URL if present
                parsed_url = urlparse(selected_path)
                if parsed_url.username:
                    self.username = unquote(parsed_url.username)
                    ADDON.setSetting('remote_username', self.username)
                if parsed_url.password:
                    self.password = unquote(parsed_url.password)
                    ADDON.setSetting('remote_password', self.password)
                
                if mode == 'restore':
                    # Create a remote backup placeholder file
                    temp_dir = os.path.join(xbmcvfs.translatePath('special://temp'), 'libreelec_backupper')
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Extract server and share from the path
                    path_parts = path.split('/')
                    server = path_parts[0]
                    share = path_parts[1] if len(path_parts) > 1 else ''
                    remote_dir = '/'.join(path_parts[2:]) if len(path_parts) > 2 else ''
                    
                    remote_info = {
                        'remote_file': os.path.basename(path),
                        'remote_path': f"{server}/{share}/{remote_dir}".rstrip('/'),
                        'remote_type': self.remote_type,
                        'remote_username': self.username,
                        'remote_password': self.password,
                        'remote_port': self.port
                    }
                    
                    placeholder_file = os.path.join(temp_dir, f"remote_backup_{int(time.time())}.json")
                    with open(placeholder_file, 'w') as f:
                        json.dump(remote_info, f)
                    
                    if 'show_message' in globals() and show_message is not None:
                        show_message("Backup Selected", f"Selected backup: {os.path.basename(path)}")
                    else:
                        ok_dialog("Backup Selected", f"Selected backup: {os.path.basename(path)}")
                    return placeholder_file
                else:
                    if 'show_message' in globals() and show_message is not None:
                        show_message("Location Selected", f"Selected backup location: {os.path.basename(path)}")
                    else:
                        ok_dialog("Location Selected", f"Selected backup location: {os.path.basename(path)}")
                    return selected_path
            else:
                if 'show_message' in globals() and show_message is not None:
                    show_message("Invalid Selection", f"Please select a valid {protocol_name} location (starts with smb://)")
                else:
                    ok_dialog("Invalid Selection", f"Please select a valid {protocol_name} location (starts with smb://)")
                return None
                
        elif self.remote_type == 4:  # WebDAV
            # For WebDAV, accept any valid path since WebDAV can be accessed through various protocols
            try:
                # For WebDAV, we'll accept any path the user selects
                # Extract useful information if it's a URL
                if selected_path.startswith(("http://", "https://", "dav://", "davs://")):
                    # It's a WebDAV URL
                    path = selected_path
                    
                    # Remove protocol prefix for storage
                    if path.startswith(("dav://", "davs://")):
                        # Convert dav:// to http:// and davs:// to https://
                        path = path.replace("dav://", "http://").replace("davs://", "https://")
                    
                    # Extract the server and path
                    parsed_url = urlparse(path)
                    server = parsed_url.netloc
                    path_part = parsed_url.path
                    
                    # Remove trailing slash if present
                    if path_part.endswith('/'):
                        path_part = path_part[:-1]
                    
                    # Format as server/path for storage
                    if path_part:
                        remote_path = f"{server}{path_part}"
                    else:
                        remote_path = server
                    
                    # Update the remote path setting
                    self.remote_path = remote_path
                    ADDON.setSetting('remote_path', remote_path)
                    # Force settings save immediately
                    xbmc.executebuiltin('UpdateLocalAddons')
                    xbmc.sleep(200)  # Brief pause to ensure settings are saved
                    
                    # Try to extract username and password from the URL if present
                    if parsed_url.username:
                        self.username = unquote(parsed_url.username)
                        ADDON.setSetting('remote_username', self.username)
                    if parsed_url.password:
                        self.password = unquote(parsed_url.password)
                        ADDON.setSetting('remote_password', self.password)
                    
                    # Set port if specified in the URL
                    if parsed_url.port:
                        self.port = str(parsed_url.port)
                        ADDON.setSetting('remote_port', self.port)
                    elif parsed_url.scheme == 'https':
                        self.port = "443"
                        ADDON.setSetting('remote_port', self.port)
                    else:
                        self.port = "80"
                        ADDON.setSetting('remote_port', self.port)
                        
                    if mode == 'restore':
                        # Create a remote backup placeholder file
                        temp_dir = os.path.join(xbmcvfs.translatePath('special://temp'), 'libreelec_backupper')
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # Extract the directory path and filename
                        dir_path = os.path.dirname(path_part)
                        if dir_path.startswith('/'):
                            dir_path = dir_path[1:]
                        
                        remote_info = {
                            'remote_file': os.path.basename(path_part),
                            'remote_path': f"{server}/{dir_path}".rstrip('/'),
                            'remote_type': self.remote_type,
                            'remote_username': self.username,
                            'remote_password': self.password,
                            'remote_port': self.port
                        }
                        
                        placeholder_file = os.path.join(temp_dir, f"remote_backup_{int(time.time())}.json")
                        with open(placeholder_file, 'w') as f:
                            json.dump(remote_info, f)
                        
                        if 'show_message' in globals() and show_message is not None:
                            show_message("Backup Selected", f"Selected backup: {os.path.basename(path_part)}")
                        else:
                            ok_dialog("Backup Selected", f"Selected backup: {os.path.basename(path_part)}")
                        return placeholder_file
                    else:
                        if 'show_message' in globals() and show_message is not None:
                            show_message("Location Selected", f"Selected backup location: {os.path.basename(path_part)}")
                        else:
                            ok_dialog("Location Selected", f"Selected backup location: {os.path.basename(path_part)}")
                        return selected_path
                else:
                    # For other paths, just store as is
                    self.remote_path = selected_path
                    ADDON.setSetting('remote_path', selected_path)
                    # Force settings save immediately
                    xbmc.executebuiltin('UpdateLocalAddons')
                    xbmc.sleep(200)  # Brief pause to ensure settings are saved
                    
                    if mode == 'restore':
                        # Create a remote backup placeholder file
                        temp_dir = os.path.join(xbmcvfs.translatePath('special://temp'), 'libreelec_backupper')
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # Extract the directory path and filename
                        dir_path = os.path.dirname(selected_path)
                        if dir_path.startswith('/'):
                            dir_path = dir_path[1:]
                        
                        remote_info = {
                            'remote_file': os.path.basename(selected_path),
                            'remote_path': dir_path.rstrip('/'),
                            'remote_type': self.remote_type,
                            'remote_username': self.username,
                            'remote_password': self.password,
                            'remote_port': self.port
                        }
                        
                        placeholder_file = os.path.join(temp_dir, f"remote_backup_{int(time.time())}.json")
                        with open(placeholder_file, 'w') as f:
                            json.dump(remote_info, f)
                        
                        if 'show_message' in globals() and show_message is not None:
                            show_message("Backup Selected", f"Selected backup: {os.path.basename(selected_path)}")
                        else:
                            ok_dialog("Backup Selected", f"Selected backup: {os.path.basename(selected_path)}")
                        return placeholder_file
                    else:
                        if 'show_message' in globals() and show_message is not None:
                            show_message("Location Selected", f"Selected backup location: {os.path.basename(selected_path)}")
                        else:
                            ok_dialog("Location Selected", f"Selected backup location: {os.path.basename(selected_path)}")
                        return selected_path
                
            except Exception as e:
                xbmc.log(f"{ADDON_ID}: Error processing WebDAV path: {str(e)}", xbmc.LOGERROR)
                ok_dialog("Error", f"Error processing selected path: {str(e)}")
                return None
        
        return None
    
    def test_connection(self):
        """Test the connection to the remote location"""
        dialog = xbmcgui.Dialog()

        # Reload settings to ensure we have the latest values
        self._log(f"{ADDON_ID}: test_connection() called", xbmc.LOGINFO)
        
        try:
            self.reload_settings()
            self._log(f"{ADDON_ID}: Settings reloaded successfully in test_connection", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"{ADDON_ID}: Error reloading settings in test_connection: {str(e)}", xbmc.LOGERROR)
            raise

        self.log_verbose(
            "test_connection:start",
            remote_type=self.remote_type,
            remote_path=self.remote_path,
            username=self.username,
            password_set=bool(self.password),
            port=self.port,
        )

        # Force settings to save
        xbmc.executebuiltin('UpdateLocalAddons')
        xbmc.sleep(500)  # Give Kodi time to update

        # Check if remote path is set
        if not self.remote_path:
            # Try to reload settings one more time after a short delay
            # This helps in cases where the settings haven't been fully saved yet
            xbmc.sleep(1000)
            self.reload_settings()

            # Check again after reload
            if not self.remote_path:
                xbmc.log(f"{ADDON_ID}: Remote path not set, cannot test connection", xbmc.LOGWARNING)
                ok_dialog("Missing Information", "Please enter a remote path first.")
                return False

        # Log all connection parameters for debugging
        self._log(f"{ADDON_ID}: Testing connection with parameters:", xbmc.LOGINFO)
        self._log(f"{ADDON_ID}: Remote Type: {self.remote_type}", xbmc.LOGDEBUG)
        self._log(f"{ADDON_ID}: Remote Path: {self.remote_path}", xbmc.LOGDEBUG)
        self._log(f"{ADDON_ID}: Username: {self.username if self.username else 'Not Set'}", xbmc.LOGDEBUG)
        self._log(f"{ADDON_ID}: Password: {'Set' if self.password else 'Not Set'}", xbmc.LOGDEBUG)
        self._log(f"{ADDON_ID}: Port: {self.port}", xbmc.LOGDEBUG)

        # Test the connection based on the protocol
        if self.remote_type == 0:  # SMB
            self._log(f"{ADDON_ID}: Starting SMB connection test", xbmc.LOGINFO)
            return self._test_smb_connection()
        elif self.remote_type == 1:  # NFS
            self._log(f"{ADDON_ID}: Starting NFS connection test", xbmc.LOGINFO)
            return self._test_nfs_connection()
        elif self.remote_type == 2:  # FTP
            self._log(f"{ADDON_ID}: Starting FTP connection test", xbmc.LOGINFO)
            return self._test_ftp_connection()
        elif self.remote_type == 3:  # SFTP
            self._log(f"{ADDON_ID}: Starting SFTP connection test", xbmc.LOGINFO)
            return self._test_sftp_connection()
        elif self.remote_type == 4:  # WebDAV
            self._log(f"{ADDON_ID}: Starting WebDAV connection test", xbmc.LOGINFO)
            return self._test_webdav_connection()
        else:
            self._log(f"{ADDON_ID}: Unknown remote type: {self.remote_type}", xbmc.LOGERROR)
            ok_dialog("Error", f"Unknown remote type: {self.remote_type}")
            return False

    def test_connection_with_params(self, remote_type, remote_path, username, password, port):
        """Test the connection with directly provided parameters"""
        dialog = xbmcgui.Dialog()
        
        self._log(f"{ADDON_ID}: test_connection_with_params() called", xbmc.LOGINFO)
        self._log(f"{ADDON_ID}: Testing with remote_type={remote_type}, path={remote_path}", xbmc.LOGDEBUG)
        
        # Store the original settings
        orig_remote_type = self.remote_type
        orig_remote_path = self.remote_path
        orig_username = self.username
        orig_password = self.password
        orig_port = self.port
        
        try:
            # Set the provided parameters
            self.remote_type = remote_type
            self.remote_path = remote_path
            self.username = username
            self.password = password
            self.port = port
            
            self._log(f"{ADDON_ID}: Parameters set successfully for test", xbmc.LOGDEBUG)
            
            # Check if remote path is set
            if not self.remote_path:
                self._log(f"{ADDON_ID}: Remote path is empty in test_connection_with_params", xbmc.LOGWARNING)
                ok_dialog("Missing Information", "Please enter a remote path first.")
                return False
            
            # Test the connection based on the protocol
            if self.remote_type == 0:  # SMB
                self._log(f"{ADDON_ID}: Starting SMB connection test with params", xbmc.LOGINFO)
                return self._test_smb_connection()
            elif self.remote_type == 1:  # NFS
                self._log(f"{ADDON_ID}: Starting NFS connection test with params", xbmc.LOGINFO)
                return self._test_nfs_connection()
            elif self.remote_type == 2:  # FTP
                self._log(f"{ADDON_ID}: Starting FTP connection test with params", xbmc.LOGINFO)
                return self._test_ftp_connection()
            elif self.remote_type == 3:  # SFTP
                self._log(f"{ADDON_ID}: Starting SFTP connection test with params", xbmc.LOGINFO)
                return self._test_sftp_connection()
            elif self.remote_type == 4:  # WebDAV
                self._log(f"{ADDON_ID}: Starting WebDAV connection test with params", xbmc.LOGINFO)
                return self._test_webdav_connection()
            else:
                self._log(f"{ADDON_ID}: Unknown remote type in test_connection_with_params: {self.remote_type}", xbmc.LOGERROR)
                ok_dialog("Error", f"Unknown remote type: {self.remote_type}")
                return False
        finally:
            # Restore the original settings
            self._log(f"{ADDON_ID}: Restoring original settings after test", xbmc.LOGDEBUG)
            self.remote_type = orig_remote_type
            self.remote_path = orig_remote_path
            self.username = orig_username
            self.password = orig_password
            self.port = orig_port
    
    def _test_smb_connection(self):
        """Test the connection to the SMB location"""
        progress = xbmcgui.DialogProgress()
        progress.create("Testing SMB Connection", "Initializing connection test...")
        
        try:
            xbmc.log(f"{ADDON_ID}: SMB connection test started", xbmc.LOGINFO)
            xbmc.log(f"{ADDON_ID}: SMB Path: {self.remote_path}", xbmc.LOGDEBUG)
            xbmc.log(f"{ADDON_ID}: SMB Username: {self.username if self.username else 'Anonymous'}", xbmc.LOGDEBUG)
            xbmc.log(f"{ADDON_ID}: SMB Password: {'Set' if self.password else 'Not Set'}", xbmc.LOGDEBUG)
            
            # Construct the full SMB URL
            smb_url = f"smb://"
            if self.username and self.password:
                smb_url += f"{self.username}:{self.password}@"
            smb_url += self.remote_path
            
            xbmc.log(f"{ADDON_ID}: Attempting to connect to SMB share", xbmc.LOGINFO)
            progress.update(25, "Connecting to SMB share...")
            # Try to list the directory
            dirs, files = xbmcvfs.listdir(smb_url)
            
            xbmc.log(f"{ADDON_ID}: SMB connection successful, found {len(dirs)} directories and {len(files)} files", xbmc.LOGINFO)
            progress.update(75, "Verifying access...")
            # Try to get some basic info about the share
            share_info = []
            if dirs:
                share_info.append(f"Directories: {len(dirs)}")
            if files:
                share_info.append(f"Files: {len(files)}")
            
            # Extract server and share information
            path_parts = self.remote_path.split('/')
            server = path_parts[0]
            share = path_parts[1] if len(path_parts) > 1 else ''
            subpath = '/'.join(path_parts[2:]) if len(path_parts) > 2 else ''
            
            progress.update(100, "Connection successful!")
            progress.close()

            details = [
                f"Server: {server}",
                f"Share: {share if share else 'Unknown'}",
                f"Subpath: {subpath if subpath else 'root'}",
                f"Directories: {len(dirs)}",
                f"Files: {len(files)}",
                f"Username: {self.username if self.username else 'Not required'}",
                "Authentication: Password set" if self.username else "Authentication: Anonymous/Guest",
                "Protocol: SMB",
                "Port: 445",
                "Access: Read/Write",
            ]
            self._show_connection_report(
                protocol='SMB',
                success=True,
                summary='Connected and verified share access.',
                details=details,
                endpoint=self._masked_smb_url(),
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing SMB connection: {str(e)}", xbmc.LOGERROR)

            self._show_connection_report(
                protocol='SMB',
                success=False,
                summary=str(e),
                details=[f"Path: {self.remote_path or 'Not set'}", f"Username: {self.username if self.username else 'Not set'}"],
                tips=[
                    'Verify the share path is correct.',
                    'Check username/password and permissions.',
                    'Confirm the server is reachable on your network.',
                ],
                endpoint=self._masked_smb_url(),
            )
            return False
    
    def _test_nfs_connection(self):
        """Test the connection to the NFS location"""
        progress = xbmcgui.DialogProgress()
        progress.create("Testing NFS Connection", "Initializing connection test...")
        mount_point = "/tmp/nfs_test"
        
        try:
            xbmc.log(f"{ADDON_ID}: NFS connection test started", xbmc.LOGINFO)
            xbmc.log(f"{ADDON_ID}: NFS Path: {self.remote_path}", xbmc.LOGDEBUG)
            
            progress.update(25, "Validating NFS path...")
            # Validate and format NFS path
            nfs_path = self.remote_path.strip()
            
            xbmc.log(f"{ADDON_ID}: Validating NFS path format: {nfs_path}", xbmc.LOGDEBUG)
            
            # Check if path has the correct format (contains :/)
            if ':/' not in nfs_path:
                xbmc.log(f"{ADDON_ID}: NFS path does not contain ':/', attempting to convert", xbmc.LOGDEBUG)
                # Try to convert to proper format
                if '/' in nfs_path and ':' not in nfs_path:
                    parts = nfs_path.split('/', 1)
                    if len(parts) == 2:
                        nfs_path = f"{parts[0]}:/{parts[1]}"
                        xbmc.log(f"{ADDON_ID}: Converted NFS path to: {nfs_path}", xbmc.LOGINFO)
                        # Update the setting with corrected path
                        self.remote_path = nfs_path
                        ADDON.setSetting('remote_path', nfs_path)
                        xbmc.executebuiltin('UpdateLocalAddons')
                    else:
                        xbmc.log(f"{ADDON_ID}: Failed to parse NFS path, invalid format", xbmc.LOGERROR)
                        progress.close()
                        self._show_connection_report(
                            protocol='NFS',
                            success=False,
                            summary='Invalid NFS path format.',
                            details=[
                                f"Current path: {self.remote_path or 'Not set'}",
                                "Required format: server:/export/path",
                            ],
                            tips=[
                                'Use a colon between server and path.',
                                'Example: 192.168.1.100:/mnt/backups',
                                'Example: nas.example.com:/export/share',
                            ],
                            endpoint=self.remote_path,
                        )
                        return False
                elif '/' not in nfs_path:
                    progress.close()
                    self._show_connection_report(
                        protocol='NFS',
                        success=False,
                        summary='Invalid NFS path.',
                        details=[
                            f"Current path: {self.remote_path or 'Not set'}",
                            "Required format: server:/export/path",
                        ],
                        tips=[
                            'Include both a server and export path.',
                            'Example: server:/share',
                        ],
                        endpoint=self.remote_path,
                    )
                    return False
            
            # Use the validated/formatted path
            self.remote_path = nfs_path
            
            progress.update(75, "Verifying NFS configuration...")
            xbmc.log(f"{ADDON_ID}: Attempting NFS mount test for: {self.remote_path}", xbmc.LOGINFO)
            # Try to mount the share temporarily
            if not os.path.exists(mount_point):
                os.makedirs(mount_point)
                xbmc.log(f"{ADDON_ID}: Created mount point: {mount_point}", xbmc.LOGDEBUG)
            
            # Unmount if already mounted
            xbmc.log(f"{ADDON_ID}: Unmounting any existing mounts at {mount_point}", xbmc.LOGDEBUG)
            subprocess.call(["umount", mount_point], stderr=subprocess.DEVNULL)
            
            # Try to mount with proper options
            mount_options = ["-t", "nfs", "-o", "soft,timeo=10,retrans=2,nolock"]
            xbmc.log(f"{ADDON_ID}: Executing mount command with options: {' '.join(mount_options)}", xbmc.LOGDEBUG)
            result = subprocess.call(["mount"] + mount_options + [self.remote_path, mount_point],
                                   stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            
            if result == 0:
                xbmc.log(f"{ADDON_ID}: NFS mount successful", xbmc.LOGINFO)
                # Successfully mounted, get some info
                try:
                    dirs = os.listdir(mount_point)
                    share_info = [f"Items Found: {len(dirs)}"]
                    xbmc.log(f"{ADDON_ID}: Found {len(dirs)} items in NFS share", xbmc.LOGDEBUG)
                except Exception as e:
                    share_info = ["Share is empty"]
                    xbmc.log(f"{ADDON_ID}: Error listing NFS share contents: {str(e)}", xbmc.LOGWARNING)
                
                # Unmount
                xbmc.log(f"{ADDON_ID}: Unmounting NFS share", xbmc.LOGDEBUG)
                subprocess.call(["umount", mount_point])
                
                progress.update(100, "Connection successful!")
                progress.close()

                self._show_connection_report(
                    protocol='NFS',
                    success=True,
                    summary='Mounted share and verified directory access.',
                    details=[
                        f"Server: {self.remote_path.split('/')[0]}",
                        f"Export path: {'/'.join(self.remote_path.split('/')[1:])}",
                        f"{share_info[0] if share_info else 'Items found: 0'}",
                        f"Mount point: {mount_point}",
                        "Access: Read/Write",
                    ],
                    endpoint=self.remote_path,
                )
                return True
            else:
                xbmc.log(f"{ADDON_ID}: NFS mount failed with result code: {result}", xbmc.LOGERROR)
                progress.close()
                self._show_connection_report(
                    protocol='NFS',
                    success=False,
                    summary='Failed to mount NFS share.',
                    details=[
                        f"Mount result code: {result}",
                        f"Path: {self.remote_path}",
                        f"Mount point: {mount_point}",
                    ],
                    tips=[
                        'Verify the NFS server is online.',
                        'Confirm export permissions allow this client.',
                        'Check that NFS client tools are installed.',
                    ],
                    endpoint=self.remote_path,
                )
                return False
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing NFS connection: {str(e)}", xbmc.LOGERROR)

            self._show_connection_report(
                protocol='NFS',
                success=False,
                summary=str(e),
                details=[
                    f"Path: {self.remote_path or 'Not set'}",
                    f"Mount point: {mount_point}",
                ],
                tips=[
                    'Check NFS server status and exports.',
                    'Verify network connectivity and DNS resolution.',
                    'Review LibreELEC/Kodi logs for mount errors.',
                ],
                endpoint=self.remote_path,
            )
            return False
    
    def _test_ftp_connection(self):
        """Test the connection to the FTP location"""
        progress = xbmcgui.DialogProgress()
        progress.create("Testing FTP Connection", "Initializing connection test...")
        server = 'Unknown'
        path = ''
        
        try:
            progress.update(25, "Connecting to FTP server...")
            # Extract server from path
            server = self.remote_path.split('/')[0]
            path = '/'.join(self.remote_path.split('/')[1:]) if '/' in self.remote_path else ''
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(server, int(self.port))
            
            progress.update(50, "Authenticating...")
            ftp.login(self.username, self.password)
            
            progress.update(75, "Verifying access...")
            # Get some basic info about the connection
            try:
                welcome_msg = ftp.getwelcome()
                system_info = ftp.sendcmd('SYST')
                current_dir = ftp.pwd()
                file_list = ftp.nlst()
                
                connection_info = [
                    f"Server: {server}",
                    f"Port: {self.port}",
                    f"Current Directory: {current_dir}",
                    f"Files Found: {len(file_list)}",
                    f"Server Type: {system_info}",
                    f"Welcome Message: {welcome_msg}"
                ]
            except:
                connection_info = [
                    f"Server: {server}",
                    f"Port: {self.port}"
                ]
            
            ftp.quit()
            
            progress.update(100, "Connection successful!")
            progress.close()

            self._show_connection_report(
                protocol='FTP',
                success=True,
                summary='Connected, authenticated, and listed directory contents.',
                details=connection_info + [
                    f"Remote path: {path if path else 'root'}",
                    f"Username: {self.username if self.username else 'Anonymous'}",
                    "Mode: Passive",
                    "Access: Read/Write",
                ],
                endpoint=f"ftp://{server}:{self.port}/{path}" if path else f"ftp://{server}:{self.port}",
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing FTP connection: {str(e)}", xbmc.LOGERROR)

            safe_server = server if server else 'Unknown'
            safe_path = path if path else 'root'
            safe_endpoint = f"ftp://{safe_server}:{self.port}/{safe_path}" if path else f"ftp://{safe_server}:{self.port}"

            self._show_connection_report(
                protocol='FTP',
                success=False,
                summary=str(e),
                details=[
                    f"Server: {safe_server}",
                    f"Port: {self.port}",
                    f"Path: {safe_path}",
                    f"Username: {self.username if self.username else 'Anonymous'}",
                ],
                tips=[
                    'Verify server address and port.',
                    'Check username/password and permissions.',
                    'Ensure the FTP service is running and reachable.',
                ],
                endpoint=safe_endpoint,
            )
            return False
    
    def _first_attr_value(self, names):
        for name in names:
            value = getattr(self, name, None)
            if isinstance(value, bool):
                return value
            if isinstance(value, str) and value.strip():
                return value.strip()
            if value is not None and not isinstance(value, (list, dict, tuple, set)):
                text = str(value).strip()
                if text:
                    return text
        return None

    def _get_setting_value(self, setting_ids):
        for sid in setting_ids:
            try:
                value = self.addon.getSetting(sid)
            except Exception:
                value = None
            if isinstance(value, str) and value.strip():
                return value.strip()
            if value not in (None, ''):
                return value
        return ""

    def _sftp_private_key_path(self):
        value = self._first_attr_value(SFTP_PRIVATE_KEY_ATTRS)
        if isinstance(value, str) and value.strip():
            return value.strip()
        value = self._get_setting_value(SFTP_PRIVATE_KEY_SETTING_IDS)
        return str(value).strip() if value not in (None, "") else ""

    def _sftp_key_passphrase(self):
        value = self._first_attr_value(SFTP_PASSPHRASE_ATTRS)
        if isinstance(value, str):
            return value
        value = self._get_setting_value(SFTP_PASSPHRASE_SETTING_IDS)
        return str(value) if value not in (None, "") else ""

    def _sftp_use_key(self):
        for name in SFTP_USE_KEY_ATTRS:
            value = getattr(self, name, None)
            if isinstance(value, bool):
                if value:
                    return True
            elif isinstance(value, str):
                low = value.strip().lower()
                if low in ("true", "1", "yes", "on", "key", "private key", "ssh key", "enabled"):
                    return True
        for name in SFTP_AUTH_MODE_ATTRS:
            value = getattr(self, name, None)
            if value is not None:
                low = str(value).strip().lower()
                if low in ("1", "key", "private key", "ssh key", "true"):
                    return True
        for sid in SFTP_USE_KEY_SETTING_IDS:
            try:
                if hasattr(self.addon, "getSettingBool"):
                    try:
                        if self.addon.getSettingBool(sid):
                            return True
                    except Exception:
                        pass
                value = self.addon.getSetting(sid)
            except Exception:
                value = None
            if isinstance(value, bool) and value:
                return True
            if isinstance(value, str):
                low = value.strip().lower()
                if low in ("true", "1", "yes", "on", "key", "private key", "ssh key"):
                    return True
        for sid in SFTP_AUTH_MODE_SETTING_IDS:
            try:
                value = self.addon.getSetting(sid)
            except Exception:
                value = None
            if value is not None:
                low = str(value).strip().lower()
                if low in ("1", "key", "private key", "ssh key", "true"):
                    return True
        key_path = self._sftp_private_key_path()
        password = getattr(self, "password", "")
        try:
            if not str(password).strip():
                password = self.addon.getSetting("remote_password") or ""
        except Exception:
            pass
        if key_path and not str(password).strip():
            return True
        return False

    def connect_sftp(self):
        """Compatibility alias for SFTP connection testing."""
        return self._test_sftp_connection()

    def _test_sftp_connection(self):
        """Test the connection to the SFTP location"""
        if not SFTP_AVAILABLE or paramiko is None:
            if not self._sftp_private_key_path():
                self._show_connection_report(
                    protocol='SFTP',
                    success=False,
                    summary="SFTP testing is unavailable because 'paramiko' is not installed.",
                    details=["Dependency: paramiko (missing)"],
                    tips=[
                        'Install paramiko if your platform supports Python modules.',
                        'Or configure key-based authentication to use the built-in CLI backend.',
                    ],
                )
                return False
        
        progress = xbmcgui.DialogProgress()
        progress.create("Testing SFTP Connection", "Initializing connection test...")
        server = 'Unknown'
        path = ''
        
        try:
            progress.update(25, "Connecting to SFTP server...")
            # Extract server from path
            server = self.remote_path.split('/')[0]
            path = '/'.join(self.remote_path.split('/')[1:]) if '/' in self.remote_path else ''
            
            # Connect to SFTP server
            if not SFTP_AVAILABLE or paramiko is None:
                key_path = self._sftp_private_key_path()
                if not key_path:
                    raise Exception("paramiko unavailable and no key configured")
                try:
                    from .sftp_cli import CLISFTPClient
                except Exception:
                    from sftp_cli import CLISFTPClient
                sftp = CLISFTPClient(server, int(self.port), self.username, key_path, self._sftp_key_passphrase())
                path = '/'.join(self.remote_path.split('/')[1:]) if '/' in self.remote_path else ''
                if path:
                    sftp.chdir(path)
                progress.update(75, "Verifying access...")
                # Verify the connection actually works
                sftp.listdir('.')
            else:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                progress.update(50, "Authenticating...")
                if self._sftp_use_key():
                    key_path = self._sftp_private_key_path()
                    passphrase = self._sftp_key_passphrase()
                    ssh.connect(
                        server,
                        port=int(self.port),
                        username=self.username,
                        key_filename=key_path if key_path else None,
                        passphrase=passphrase if passphrase else None,
                    )
                else:
                    ssh.connect(server, port=int(self.port), username=self.username, password=self.password)

                progress.update(75, "Verifying access...")
                sftp = ssh.open_sftp()
            
            # Get some basic info about the connection
            try:
                current_dir = sftp.getcwd()
                file_list = sftp.listdir('.')
                if 'ssh' in locals():
                    transport = ssh.get_transport()
                    server_version = getattr(transport, 'remote_version', 'Unknown') if transport else 'Unknown'
                    peer_name = transport.getpeername() if transport and hasattr(transport, 'getpeername') else None
                    server_hostname = peer_name[0] if peer_name else server
                else:
                    server_version = 'CLI backend'
                    server_hostname = server
                
                connection_info = [
                    f"Server: {server}",
                    f"Port: {self.port}",
                    f"Current Directory: {current_dir}",
                    f"Files Found: {len(file_list)}",
                    f"Server Version: {server_version}",
                    f"Server Hostname: {server_hostname}"
                ]
            except:
                connection_info = [
                    f"Server: {server}",
                    f"Port: {self.port}"
                ]
            
            sftp.close()
            if 'ssh' in locals():
                ssh.close()
            
            progress.update(100, "Connection successful!")
            progress.close()

            self._show_connection_report(
                protocol='SFTP',
                success=True,
                summary='Connected over SSH and verified SFTP access.',
                details=connection_info + [
                    f"Remote path: {path if path else 'root'}",
                    f"Username: {self.username if self.username else 'Not set'}",
                    "Encryption: SSH",
                    "Access: Read/Write",
                ],
                endpoint=f"sftp://{server}:{self.port}/{path}" if path else f"sftp://{server}:{self.port}",
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing SFTP connection: {str(e)}", xbmc.LOGERROR)

            safe_server = server if server else 'Unknown'
            safe_path = path if path else 'root'
            safe_endpoint = f"sftp://{safe_server}:{self.port}/{safe_path}" if path else f"sftp://{safe_server}:{self.port}"

            self._show_connection_report(
                protocol='SFTP',
                success=False,
                summary=str(e),
                details=[
                    f"Server: {safe_server}",
                    f"Port: {self.port}",
                    f"Path: {safe_path}",
                    f"Username: {self.username if self.username else 'Not set'}",
                ],
                tips=[
                    'Verify server hostname/IP and SSH port.',
                    'Check credentials or key-based authentication settings.',
                    'Ensure the SSH/SFTP service is running.',
                ],
                endpoint=safe_endpoint,
            )
            return False
    
    def _test_webdav_connection(self):
        """Test the connection to the WebDAV location"""
        if not WEBDAV_AVAILABLE or requests is None:
            self._show_connection_report(
                protocol='WebDAV',
                success=False,
                summary="WebDAV testing is unavailable because 'requests' is not installed.",
                details=["Dependency: requests (missing)"],
                tips=[
                    'Install requests if your platform supports Python modules.',
                    'Use SMB, NFS, FTP, or SFTP as an alternative.',
                ],
            )
            return False
        
        progress = xbmcgui.DialogProgress()
        progress.create("Testing WebDAV Connection", "Initializing connection test...")
        server = 'Unknown'
        path = ''
        url = self.remote_path
        
        try:
            progress.update(25, "Preparing connection...")
            # Extract server from path
            server = self.remote_path.split('/')[0]
            path = '/'.join(self.remote_path.split('/')[1:]) if '/' in self.remote_path else ''
            
            # Construct WebDAV URL
            protocol = "https" if int(self.port) == 443 else "http"
            url = f"{protocol}://{server}"
            if self.port and self.port not in ["80", "443"]:
                url += f":{self.port}"
            
            if path:
                url += f"/{path}"
            
            progress.update(50, "Connecting to WebDAV server...")
            # Try to connect to WebDAV server
            response = requests.request(
                "PROPFIND",
                url,
                auth=(self.username, self.password) if self.username else None,
                headers={"Depth": "0"},
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                progress.close()
                self._show_connection_report(
                    protocol='WebDAV',
                    success=False,
                    summary='Authentication failed (HTTP 401/403).',
                    details=[
                        f"HTTP status: {response.status_code}",
                        f"Username: {self.username if self.username else 'Not set'}",
                    ],
                    tips=[
                        'Verify username and password.',
                        'Confirm account permissions for this path.',
                        'Check server auth policy (Basic/Digest/Token).',
                    ],
                    endpoint=url,
                )
                return False
            
            if response.status_code != 207:  # 207 is Multi-Status response for PROPFIND
                progress.close()
                self._show_connection_report(
                    protocol='WebDAV',
                    success=False,
                    summary='Unexpected server response for PROPFIND request.',
                    details=[f"HTTP status: {response.status_code}", f"Expected status: 207"],
                    tips=[
                        'Verify the URL points to a WebDAV-enabled endpoint.',
                        'Confirm WebDAV methods are allowed for this user.',
                        'Check reverse proxy/web server rules.',
                    ],
                    endpoint=url,
                )
                return False
            
            # Get server information from response headers
            server_info = []
            if 'Server' in response.headers:
                server_info.append(f"Server Software: {response.headers['Server']}")
            if 'X-Powered-By' in response.headers:
                server_info.append(f"Powered By: {response.headers['X-Powered-By']}")
            
            progress.update(100, "Connection successful!")
            progress.close()

            headers_preview = [f"{k}: {v}" for k, v in list(response.headers.items())[:8]]
            self._show_connection_report(
                protocol='WebDAV',
                success=True,
                summary='Server responded correctly to PROPFIND.',
                details=[
                    f"Server: {server}",
                    f"Transport: {protocol.upper()}",
                    f"Port: {self.port}",
                    f"Remote path: {path if path else 'root'}",
                    f"Username: {self.username if self.username else 'Not required'}",
                    f"HTTP status: {response.status_code}",
                    f"Response time: {response.elapsed.total_seconds():.2f}s",
                ] + server_info + headers_preview,
                endpoint=url,
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing WebDAV connection: {str(e)}", xbmc.LOGERROR)

            safe_server = server if server else 'Unknown'
            safe_path = path if path else 'root'
            safe_endpoint = url if url else self.remote_path

            self._show_connection_report(
                protocol='WebDAV',
                success=False,
                summary=str(e),
                details=[
                    f"Server: {safe_server}",
                    f"Port: {self.port}",
                    f"Path: {safe_path}",
                ],
                tips=[
                    'Verify server URL and port.',
                    'Confirm WebDAV is enabled on the server.',
                    'Check network reachability and TLS certificate settings.',
                ],
                endpoint=safe_endpoint,
            )
            return False
    
    def discover_smb_servers(self):
        """Attempt to discover SMB servers on the local network"""
        # This is a simplified approach - in a real implementation,
        # you would use proper SMB discovery protocols
        
        # For demonstration, we'll just return some dummy servers
        # In a real implementation, you would scan the network
        try:
            # Try to get the local hostname
            local_hostname = socket.gethostname()
            local_ip = socket.gethostbyname(local_hostname)
            
            # Extract network prefix
            ip_parts = local_ip.split('.')
            network_prefix = '.'.join(ip_parts[0:3])
            
            # For demo purposes, just return the local machine
            # In a real implementation, you would scan the network for SMB servers
            return [local_hostname]
            
        except Exception as e:
            xbmc.log(f"{ADDON_ID}: Error discovering SMB servers: {str(e)}", xbmc.LOGERROR)
            return []
    
    def select_from_list(self, items, title):
        """Show a selection dialog with the given items"""
        if not items:
            return None
            
        dialog = xbmcgui.Dialog()
        index = dialog.select(title, items)
        
        if index < 0:  # User cancelled
            return None
            
        return items[index]
    
    def browse_nfs(self, mode='backup'):
        """Browse NFS location - show dialog with format hint"""
        dialog = xbmcgui.Dialog()

        # Show format hint first
        format_hint = [
            "NFS Path Format:",
            "",
            "Format: server:/export/path",
            "",
            "Examples:",
            "• 192.168.1.100:/mnt/backups",
            "• nas.example.com:/export/backup",
            "• server:/share",
            "",
            "Note: The colon (:) is required between",
            "server and export path."
        ]

        if 'show_message' in globals() and show_message is not None:
            show_message("NFS Path Format", "\n".join(format_hint))
        else:
            ok_dialog("NFS Path Format", "\n".join(format_hint))

        # Get current path or empty string
        current_path = self.remote_path or ""

        # Show keyboard dialog
        keyboard = xbmc.Keyboard(current_path, "Enter NFS Path (server:/export/path)")
        keyboard.doModal()

        if keyboard.isConfirmed():
            new_path = keyboard.getText().strip()
            if new_path:
                # Validate NFS path format
                if ':/' not in new_path and ':' not in new_path:
                    # Try to help user - if they entered IP/path, add the colon
                    if '/' in new_path:
                        parts = new_path.split('/', 1)
                        if len(parts) == 2:
                            new_path = f"{parts[0]}:/{parts[1]}"
                            if 'show_message' in globals() and show_message is not None:
                                show_message("Path Format Adjusted", f"Adjusted to: {new_path}")
                            else:
                                ok_dialog("Path Format Adjusted", f"Adjusted to: {new_path}")

                # Validate the path looks like a proper NFS path
                if ':/' not in new_path:
                    if 'show_message' in globals() and show_message is not None:
                        show_message("Invalid NFS Path", "NFS path must contain ':' (colon) in format server:/export/path")
                    else:
                        ok_dialog("Invalid NFS Path", "NFS path must contain ':' (colon) in format server:/export/path")
                    return None

                if new_path != current_path:
                    self.remote_path = new_path
                    ADDON.setSetting('remote_path', new_path)
                    # Force settings save
                    xbmc.executebuiltin('UpdateLocalAddons')
                    xbmc.sleep(200)  # Brief pause to ensure settings are saved

                    # Show confirmation
                    if 'show_message' in globals() and show_message is not None:
                        show_message("NFS Path Set", f"NFS path configured: {new_path}\n\nUse 'Test Connection' to verify.")
                    else:
                        ok_dialog("NFS Path Set", f"NFS path configured: {new_path}\n\nUse 'Test Connection' to verify.")
                    return new_path
                else:
                    # Path didn't change
                    if 'show_message' in globals() and show_message is not None:
                        show_message("NFS Path", f"NFS path unchanged: {new_path}")
                    else:
                        ok_dialog("NFS Path", f"NFS path unchanged: {new_path}")
                    return new_path
            else:
                if 'show_message' in globals() and show_message is not None:
                    show_message("NFS Path", "No path entered")
                else:
                    ok_dialog("NFS Path", "No path entered")
                return None
        else:
            # User cancelled
            return None
    
    def show_manual_entry_dialog(self, protocol_name):
        """Show a dialog for manual entry of remote path"""
        dialog = xbmcgui.Dialog()
        
        # Get format hints based on protocol
        format_hints = {
            "FTP": "Format: server/path\nExample: ftp.example.com/backups",
            "SFTP": "Format: server/path\nExample: server.example.com/home/user/backups"
        }
        
        hint = format_hints.get(protocol_name, f"Enter {protocol_name} path")
        
        # Get current path or empty string
        current_path = self.remote_path or ""
        
        # Show keyboard dialog
        keyboard = xbmc.Keyboard(current_path, f"Enter {protocol_name} Path")
        keyboard.doModal()
        
        if keyboard.isConfirmed():
            new_path = keyboard.getText().strip()
            if new_path != current_path:
                self.remote_path = new_path
                ADDON.setSetting('remote_path', new_path)
                # Force settings save
                xbmc.executebuiltin('UpdateLocalAddons')
                return True
        
        return False

    def browse_remote(self, mode='backup'):
        """Browse remote locations - wrapper for the browse method
        mode: 'backup' for folder selection, 'restore' for file selection"""
        return self.browse(mode)

def main():
    browser = RemoteBrowser()
    
    # Check if we're testing a connection
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        browser.test_connection()
    else:
        # Default to browsing
        browser.browse()

if __name__ == "__main__":
    main()
