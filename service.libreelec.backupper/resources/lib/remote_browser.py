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

try:
    import paramiko
    SFTP_AVAILABLE = True
except ImportError:
    SFTP_AVAILABLE = False

try:
    import requests
    WEBDAV_AVAILABLE = True
except ImportError:
    WEBDAV_AVAILABLE = False

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
LANGUAGE = ADDON.getLocalizedString

class RemoteBrowser:
    def __init__(self):
        # Always reload settings to ensure we have the latest values
        self.reload_settings()
    
    def reload_settings(self):
        """Reload settings from Kodi"""
        # Force reload of addon to get fresh settings
        global ADDON
        ADDON = xbmcaddon.Addon()
        
        self.remote_type = int(ADDON.getSetting('remote_location_type'))
        self.remote_path = ADDON.getSetting('remote_path')
        self.username = ADDON.getSetting('remote_username')
        self.password = ADDON.getSetting('remote_password')
        self.port = ADDON.getSetting('remote_port')
        
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
    
    def browse(self, mode='backup'):
        """Main method to browse remote locations based on type
        mode: 'backup' for folder selection, 'restore' for file selection"""
        # Reload settings to ensure we have the latest values
        self.reload_settings()
        
        remote_types = ["SMB", "NFS", "FTP", "SFTP", "WebDAV"]
        current_type = remote_types[self.remote_type]
        
        xbmc.log(f"{ADDON_ID}: Browsing {current_type} location for {mode}", xbmc.LOGINFO)
        
        # Use Kodi's built-in file browser for SMB and WebDAV
        if self.remote_type in [0, 4]:  # SMB or WebDAV
            return self.browse_with_kodi_browser(current_type, mode)
        elif self.remote_type == 1:  # NFS
            self.show_manual_entry_dialog("NFS")
            return None
        elif self.remote_type == 2:  # FTP
            self.show_manual_entry_dialog("FTP")
            return None
        elif self.remote_type == 3:  # SFTP
            if not SFTP_AVAILABLE:
                xbmcgui.Dialog().ok("Missing Dependency", 
                                   "SFTP browsing requires the paramiko module which is not available.")
                return None
            self.show_manual_entry_dialog("SFTP")
            return None
        
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
            dialog.ok("Invalid Selection", "Please select a backup file (.zip)")
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
                
                # Update the remote path setting
                self.remote_path = path
                ADDON.setSetting('remote_path', path)
                
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
                    
                    dialog.ok("Backup Selected", f"Selected backup: {os.path.basename(path)}")
                    return placeholder_file
                else:
                    dialog.ok("Location Selected", f"Selected backup location: {os.path.basename(path)}")
                    return selected_path
            else:
                dialog.ok("Invalid Selection", f"Please select a valid {protocol_name} location (starts with smb://)")
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
                        
                        dialog.ok("Backup Selected", f"Selected backup: {os.path.basename(path_part)}")
                        return placeholder_file
                    else:
                        dialog.ok("Location Selected", f"Selected backup location: {os.path.basename(path_part)}")
                        return selected_path
                else:
                    # For other paths, just store as is
                    self.remote_path = selected_path
                    ADDON.setSetting('remote_path', selected_path)
                    
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
                        
                        dialog.ok("Backup Selected", f"Selected backup: {os.path.basename(selected_path)}")
                        return placeholder_file
                    else:
                        dialog.ok("Location Selected", f"Selected backup location: {os.path.basename(selected_path)}")
                        return selected_path
                
            except Exception as e:
                xbmc.log(f"{ADDON_ID}: Error processing WebDAV path: {str(e)}", xbmc.LOGERROR)
                dialog.ok("Error", f"Error processing selected path: {str(e)}")
                return None
        
        return None
    
    def test_connection(self):
        """Test the connection to the remote location"""
        dialog = xbmcgui.Dialog()
        
        # Reload settings to ensure we have the latest values
        self.reload_settings()
        
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
                dialog.ok("❌ Missing Information", "Please enter a remote path first.")
                return False
        
        # Show progress dialog with detailed status
        progress = xbmcgui.DialogProgress()
        progress.create("🔍 Testing Connection", "Initializing connection test...")
        
        # Get protocol name for display
        protocol_names = {
            0: "SMB",
            1: "NFS",
            2: "FTP",
            3: "SFTP",
            4: "WebDAV"
        }
        protocol = protocol_names.get(self.remote_type, "Unknown")
        
        # Test the connection based on the protocol
        try:
            if self.remote_type == 0:  # SMB
                progress.update(25, f"Testing {protocol} connection...")
                result = self._test_smb_connection(progress)
            elif self.remote_type == 1:  # NFS
                progress.update(25, f"Testing {protocol} connection...")
                result = self._test_nfs_connection(progress)
            elif self.remote_type == 2:  # FTP
                progress.update(25, f"Testing {protocol} connection...")
                result = self._test_ftp_connection(progress)
            elif self.remote_type == 3:  # SFTP
                progress.update(25, f"Testing {protocol} connection...")
                result = self._test_sftp_connection(progress)
            elif self.remote_type == 4:  # WebDAV
                progress.update(25, f"Testing {protocol} connection...")
                result = self._test_webdav_connection(progress)
            else:
                progress.close()
                dialog.ok("❌ Error", f"Unknown remote type: {self.remote_type}")
                return False
            
            progress.close()
            return result
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing connection: {str(e)}", xbmc.LOGERROR)
            dialog.ok("❌ Connection Error", f"An unexpected error occurred:\n{str(e)}")
            return False

    def _test_smb_connection(self, progress):
        """Test the connection to the SMB location"""
        try:
            # Construct the full SMB URL
            smb_url = f"smb://"
            if self.username and self.password:
                smb_url += f"{self.username}:{self.password}@"
            smb_url += self.remote_path
            
            progress.update(50, "Attempting to list directory contents...")
            
            # Try to list the directory
            dirs, files = xbmcvfs.listdir(smb_url)
            
            # Count items found
            total_items = len(dirs) + len(files)
            
            progress.update(100, "Connection successful!")
            progress.close()
            
            # Show detailed success message
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "✅ Connection Successful",
                f"Successfully connected to SMB share:\n\n"
                f"📁 Location: {self.remote_path}\n"
                f"👤 Username: {self.username if self.username else 'Not specified'}\n"
                f"🔑 Authentication: {'Required' if self.username else 'Not required'}\n"
                f"📊 Items found: {total_items}\n"
                f"📂 Directories: {len(dirs)}\n"
                f"📄 Files: {len(files)}"
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing SMB connection: {str(e)}", xbmc.LOGERROR)
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "❌ Connection Failed",
                f"Failed to connect to SMB share:\n\n"
                f"📁 Location: {self.remote_path}\n"
                f"👤 Username: {self.username if self.username else 'Not specified'}\n"
                f"❌ Error: {str(e)}\n\n"
                f"Please check:\n"
                f"• Network connectivity\n"
                f"• Share permissions\n"
                f"• Credentials (if required)\n"
                f"• Share availability"
            )
            return False

    def _test_nfs_connection(self, progress):
        """Test the connection to the NFS location"""
        try:
            progress.update(50, "Validating NFS path format...")
            
            # Check path format
            if '/' not in self.remote_path:
                progress.close()
                dialog = xbmcgui.Dialog()
                dialog.ok(
                    "❌ Invalid NFS Path",
                    f"The NFS path is invalid:\n\n"
                    f"📁 Current path: {self.remote_path}\n"
                    f"ℹ️ Required format: server/export/path\n\n"
                    f"Please check the path format and try again."
                )
                return False
            
            progress.update(100, "NFS path validated!")
            progress.close()
            
            # Show NFS-specific message
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "⚠️ NFS Connection",
                f"NFS connection cannot be fully tested.\n\n"
                f"📁 Path: {self.remote_path}\n"
                f"ℹ️ Please ensure:\n"
                f"• NFS server is running\n"
                f"• Export is properly configured\n"
                f"• Network connectivity is available\n"
                f"• Required ports are open"
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing NFS connection: {str(e)}", xbmc.LOGERROR)
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "❌ Connection Failed",
                f"Failed to validate NFS connection:\n\n"
                f"📁 Path: {self.remote_path}\n"
                f"❌ Error: {str(e)}\n\n"
                f"Please check the NFS configuration and try again."
            )
            return False

    def _test_ftp_connection(self, progress):
        """Test the connection to the FTP location"""
        try:
            # Extract server from path
            server = self.remote_path.split('/')[0]
            
            progress.update(50, f"Connecting to FTP server: {server}")
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(server, int(self.port))
            ftp.login(self.username, self.password)
            
            # Get server welcome message
            welcome_msg = ftp.getwelcome()
            
            # Try to get current directory
            current_dir = ftp.pwd()
            
            # Try to list directory contents
            files = []
            ftp.dir(files.append)
            
            ftp.quit()
            
            progress.update(100, "Connection successful!")
            progress.close()
            
            # Show detailed success message
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "✅ Connection Successful",
                f"Successfully connected to FTP server:\n\n"
                f"🌐 Server: {server}\n"
                f"🔢 Port: {self.port}\n"
                f"👤 Username: {self.username if self.username else 'Anonymous'}\n"
                f"📁 Current directory: {current_dir}\n"
                f"📊 Files found: {len(files)}\n"
                f"ℹ️ Server message: {welcome_msg}"
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing FTP connection: {str(e)}", xbmc.LOGERROR)
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "❌ Connection Failed",
                f"Failed to connect to FTP server:\n\n"
                f"🌐 Server: {server}\n"
                f"🔢 Port: {self.port}\n"
                f"👤 Username: {self.username if self.username else 'Anonymous'}\n"
                f"❌ Error: {str(e)}\n\n"
                f"Please check:\n"
                f"• Server availability\n"
                f"• Port number\n"
                f"• Credentials\n"
                f"• Firewall settings"
            )
            return False

    def _test_sftp_connection(self, progress):
        """Test the connection to the SFTP location"""
        if not SFTP_AVAILABLE:
            progress.close()
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "❌ Missing Dependency",
                "SFTP testing requires the paramiko module which is not available.\n\n"
                "Please install the required dependency and try again."
            )
            return False
        
        try:
            # Extract server from path
            server = self.remote_path.split('/')[0]
            
            progress.update(50, f"Connecting to SFTP server: {server}")
            
            # Connect to SFTP server
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server, port=int(self.port), username=self.username, password=self.password)
            
            # Get server information
            server_version = ssh.get_transport().get_remote_version()
            
            # Open SFTP session
            sftp = ssh.open_sftp()
            
            # Get current directory
            current_dir = sftp.getcwd()
            
            # Try to list directory contents
            files = sftp.listdir()
            
            sftp.close()
            ssh.close()
            
            progress.update(100, "Connection successful!")
            progress.close()
            
            # Show detailed success message
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "✅ Connection Successful",
                f"Successfully connected to SFTP server:\n\n"
                f"🌐 Server: {server}\n"
                f"🔢 Port: {self.port}\n"
                f"👤 Username: {self.username}\n"
                f"📁 Current directory: {current_dir}\n"
                f"📊 Files found: {len(files)}\n"
                f"ℹ️ Server version: {server_version}"
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing SFTP connection: {str(e)}", xbmc.LOGERROR)
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "❌ Connection Failed",
                f"Failed to connect to SFTP server:\n\n"
                f"🌐 Server: {server}\n"
                f"🔢 Port: {self.port}\n"
                f"👤 Username: {self.username}\n"
                f"❌ Error: {str(e)}\n\n"
                f"Please check:\n"
                f"• Server availability\n"
                f"• Port number\n"
                f"• Credentials\n"
                f"• SSH key configuration"
            )
            return False

    def _test_webdav_connection(self, progress):
        """Test the connection to the WebDAV location"""
        if not WEBDAV_AVAILABLE:
            progress.close()
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "❌ Missing Dependency",
                "WebDAV testing requires the requests module which is not available.\n\n"
                "Please install the required dependency and try again."
            )
            return False
        
        try:
            # Extract server from path
            server = self.remote_path.split('/')[0]
            path = '/'.join(self.remote_path.split('/')[1:])
            
            progress.update(50, f"Connecting to WebDAV server: {server}")
            
            # Construct WebDAV URL
            protocol = "https" if int(self.port) == 443 else "http"
            url = f"{protocol}://{server}"
            if self.port and self.port not in ["80", "443"]:
                url += f":{self.port}"
            
            if path:
                url += f"/{path}"
            
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
                dialog = xbmcgui.Dialog()
                dialog.ok(
                    "❌ Authentication Failed",
                    f"Failed to authenticate with the WebDAV server:\n\n"
                    f"🌐 Server: {server}\n"
                    f"👤 Username: {self.username if self.username else 'Not specified'}\n"
                    f"❌ Status code: {response.status_code}\n\n"
                    f"Please check your credentials and try again."
                )
                return False
            
            if response.status_code != 207:  # 207 is Multi-Status response for PROPFIND
                progress.close()
                dialog = xbmcgui.Dialog()
                dialog.ok(
                    "❌ WebDAV Error",
                    f"Failed to connect to WebDAV server:\n\n"
                    f"🌐 Server: {server}\n"
                    f"🔢 Port: {self.port}\n"
                    f"📁 Path: {path}\n"
                    f"❌ Status code: {response.status_code}\n\n"
                    f"Please check the server configuration and try again."
                )
                return False
            
            progress.update(100, "Connection successful!")
            progress.close()
            
            # Show detailed success message
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "✅ Connection Successful",
                f"Successfully connected to WebDAV server:\n\n"
                f"🌐 Server: {server}\n"
                f"🔢 Port: {self.port}\n"
                f"📁 Path: {path}\n"
                f"👤 Username: {self.username if self.username else 'Not specified'}\n"
                f"🔒 Protocol: {protocol.upper()}\n"
                f"ℹ️ Server response: {response.status_code}"
            )
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing WebDAV connection: {str(e)}", xbmc.LOGERROR)
            dialog = xbmcgui.Dialog()
            dialog.ok(
                "❌ Connection Failed",
                f"Failed to connect to WebDAV server:\n\n"
                f"🌐 Server: {server}\n"
                f"🔢 Port: {self.port}\n"
                f"📁 Path: {path}\n"
                f"❌ Error: {str(e)}\n\n"
                f"Please check:\n"
                f"• Server availability\n"
                f"• Port number\n"
                f"• Credentials\n"
                f"• SSL/TLS configuration"
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
    
    def show_manual_entry_dialog(self, protocol_name):
        """Show a dialog for manual entry of remote path"""
        dialog = xbmcgui.Dialog()
        
        # Get current path or empty string
        current_path = self.remote_path or ""
        
        # Show keyboard dialog
        keyboard = xbmc.Keyboard(current_path, f"Enter {protocol_name} Path")
        keyboard.doModal()
        
        if keyboard.isConfirmed():
            new_path = keyboard.getText()
            if new_path != current_path:
                self.remote_path = new_path
                ADDON.setSetting('remote_path', new_path)
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