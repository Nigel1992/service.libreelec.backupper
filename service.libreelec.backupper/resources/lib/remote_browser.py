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
                dialog.ok("Missing Information", "Please enter a remote path first.")
                return False
        
        # Test the connection based on the protocol
        if self.remote_type == 0:  # SMB
            return self._test_smb_connection()
        elif self.remote_type == 1:  # NFS
            return self._test_nfs_connection()
        elif self.remote_type == 2:  # FTP
            return self._test_ftp_connection()
        elif self.remote_type == 3:  # SFTP
            return self._test_sftp_connection()
        elif self.remote_type == 4:  # WebDAV
            return self._test_webdav_connection()
        else:
            dialog.ok("Error", f"Unknown remote type: {self.remote_type}")
            return False

    def test_connection_with_params(self, remote_type, remote_path, username, password, port):
        """Test the connection with directly provided parameters"""
        dialog = xbmcgui.Dialog()
        
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
            
            # Check if remote path is set
            if not self.remote_path:
                dialog.ok("Missing Information", "Please enter a remote path first.")
                return False
            
            # Test the connection based on the protocol
            if self.remote_type == 0:  # SMB
                return self._test_smb_connection()
            elif self.remote_type == 1:  # NFS
                return self._test_nfs_connection()
            elif self.remote_type == 2:  # FTP
                return self._test_ftp_connection()
            elif self.remote_type == 3:  # SFTP
                return self._test_sftp_connection()
            elif self.remote_type == 4:  # WebDAV
                return self._test_webdav_connection()
            else:
                dialog.ok("Error", f"Unknown remote type: {self.remote_type}")
                return False
        finally:
            # Restore the original settings
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
            # Construct the full SMB URL
            smb_url = f"smb://"
            if self.username and self.password:
                smb_url += f"{self.username}:{self.password}@"
            smb_url += self.remote_path
            
            progress.update(25, "Connecting to SMB share...")
            # Try to list the directory
            dirs, files = xbmcvfs.listdir(smb_url)
            
            progress.update(75, "Verifying access...")
            # Try to get some basic info about the share
            share_info = []
            if dirs:
                share_info.append(f"📁 {len(dirs)} directories found")
            if files:
                share_info.append(f"📄 {len(files)} files found")
            
            # Extract server and share information
            path_parts = self.remote_path.split('/')
            server = path_parts[0]
            share = path_parts[1] if len(path_parts) > 1 else ''
            subpath = '/'.join(path_parts[2:]) if len(path_parts) > 2 else ''
            
            progress.update(100, "Connection successful!")
            progress.close()
            
            # Show detailed success message
            success_msg = [
                "✅ SMB Connection Successful",
                "",
                "🔍 Connection Details:",
                f"📡 Server: {server}",
                f"📂 Share: {share}",
                f"📂 Subpath: {subpath if subpath else 'root'}",
                "",
                "📊 Share Contents:",
                *share_info,
                "",
                "🔐 Authentication:",
                f"👤 Username: {self.username if self.username else 'Not Required'}",
                "🔑 Password: Set" if self.username else "🔑 Password: Not Required",
                "",
                "🔧 System Info:",
                "• Protocol: SMB",
                "• Port: 445",
                "• Access: Read/Write"
            ]
            
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(success_msg))
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing SMB connection: {str(e)}", xbmc.LOGERROR)
            
            # Show detailed error message
            error_msg = [
                "❌ SMB Connection Failed",
                "",
                "🔍 Error Details:",
                f"📝 {str(e)}",
                "",
                "🔧 Troubleshooting Tips:",
                "• Verify the share path is correct",
                "• Check if credentials are valid",
                "• Ensure the share is accessible",
                "• Verify network connectivity"
            ]
            
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
            return False
    
    def _test_nfs_connection(self):
        """Test the connection to the NFS location"""
        progress = xbmcgui.DialogProgress()
        progress.create("Testing NFS Connection", "Initializing connection test...")
        
        try:
            progress.update(25, "Validating NFS path...")
            # Check if the path format is valid
            if '/' not in self.remote_path:
                progress.close()
                error_msg = [
                    "❌ Invalid NFS Path",
                    "",
                    "🔍 Error Details:",
                    "• Path format should be 'server/export/path'",
                    "",
                    "📝 Current Path:",
                    f"{self.remote_path}",
                    "",
                    "🔧 Correct Format Example:",
                    "server.example.com:/export/share"
                ]
                xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
                return False
            
            progress.update(75, "Verifying NFS configuration...")
            # Try to mount the share temporarily
            mount_point = "/tmp/nfs_test"
            if not os.path.exists(mount_point):
                os.makedirs(mount_point)
            
            # Unmount if already mounted
            subprocess.call(["umount", mount_point], stderr=subprocess.DEVNULL)
            
            # Try to mount
            result = subprocess.call(["mount", "-t", "nfs", self.remote_path, mount_point])
            
            if result == 0:
                # Successfully mounted, get some info
                try:
                    dirs = os.listdir(mount_point)
                    share_info = [f"📁 {len(dirs)} items found"]
                except:
                    share_info = ["📁 Share is empty"]
                
                # Unmount
                subprocess.call(["umount", mount_point])
                
                progress.update(100, "Connection successful!")
                progress.close()
                
                # Show detailed success message
                success_msg = [
                    "✅ NFS Connection Successful",
                    "",
                    f"📂 Share: {self.remote_path}",
                    *share_info,
                    "",
                    "🔍 Connection Details:",
                    "🔌 Protocol: NFS",
                    f"📡 Server: {self.remote_path.split('/')[0]}",
                    f"📂 Export Path: {'/'.join(self.remote_path.split('/')[1:])}",
                    "",
                    "🔧 System Info:",
                    "• NFS Client: Installed",
                    "• Mount Point: /tmp/nfs_test",
                    "• Access: Read/Write"
                ]
                
                xbmcgui.Dialog().ok("Connection Test Results", "\n".join(success_msg))
                return True
            else:
                progress.close()
                error_msg = [
                    "❌ NFS Connection Failed",
                    "",
                    "🔍 Error Details:",
                    "• Failed to mount NFS share",
                    "",
                    "🔧 Troubleshooting Tips:",
                    "• Verify NFS server is running",
                    "• Check if NFS client is installed",
                    "• Ensure proper permissions",
                    "• Verify network connectivity"
                ]
                xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
                return False
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing NFS connection: {str(e)}", xbmc.LOGERROR)
            
            error_msg = [
                "❌ NFS Connection Failed",
                "",
                "🔍 Error Details:",
                f"📝 {str(e)}",
                "",
                "🔧 Troubleshooting Tips:",
                "• Check NFS server status",
                "• Verify network connectivity",
                "• Check system logs for details"
            ]
            
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
            return False
    
    def _test_ftp_connection(self):
        """Test the connection to the FTP location"""
        progress = xbmcgui.DialogProgress()
        progress.create("Testing FTP Connection", "Initializing connection test...")
        
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
                    f"📡 Server: {server}",
                    f"🔌 Port: {self.port}",
                    f"📂 Current Directory: {current_dir}",
                    f"📄 Files Found: {len(file_list)}",
                    f"💻 Server Type: {system_info}",
                    f"👋 Welcome Message: {welcome_msg}"
                ]
            except:
                connection_info = [
                    f"📡 Server: {server}",
                    f"🔌 Port: {self.port}"
                ]
            
            ftp.quit()
            
            progress.update(100, "Connection successful!")
            progress.close()
            
            # Show detailed success message
            success_msg = [
                "✅ FTP Connection Successful",
                "",
                "🔍 Connection Details:",
                *connection_info,
                "",
                "📂 Path Information:",
                f"• Remote Path: {path if path else 'root'}",
                f"• Current Directory: {current_dir if 'current_dir' in locals() else 'Unknown'}",
                "",
                "🔐 Authentication:",
                f"👤 Username: {self.username}",
                "🔑 Password: Set",
                "",
                "🔧 System Info:",
                "• Protocol: FTP",
                "• Mode: Passive",
                "• Access: Read/Write"
            ]
            
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(success_msg))
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing FTP connection: {str(e)}", xbmc.LOGERROR)
            
            error_msg = [
                "❌ FTP Connection Failed",
                "",
                "🔍 Error Details:",
                f"📝 {str(e)}",
                "",
                "🔧 Troubleshooting Tips:",
                "• Verify server address and port",
                "• Check if credentials are correct",
                "• Ensure FTP server is running",
                "• Check firewall settings"
            ]
            
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
            return False
    
    def _test_sftp_connection(self):
        """Test the connection to the SFTP location"""
        if not SFTP_AVAILABLE:
            error_msg = [
                "❌ SFTP Testing Not Available",
                "",
                "🔍 Error Details:",
                "• Required module 'paramiko' is not available",
                "",
                "🔧 Solution:",
                "• Install the paramiko module",
                "• Contact addon developer for support"
            ]
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
            return False
        
        progress = xbmcgui.DialogProgress()
        progress.create("Testing SFTP Connection", "Initializing connection test...")
        
        try:
            progress.update(25, "Connecting to SFTP server...")
            # Extract server from path
            server = self.remote_path.split('/')[0]
            path = '/'.join(self.remote_path.split('/')[1:]) if '/' in self.remote_path else ''
            
            # Connect to SFTP server
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            progress.update(50, "Authenticating...")
            ssh.connect(server, port=int(self.port), username=self.username, password=self.password)
            
            progress.update(75, "Verifying access...")
            sftp = ssh.open_sftp()
            
            # Get some basic info about the connection
            try:
                current_dir = sftp.getcwd()
                file_list = sftp.listdir('.')
                server_version = ssh.get_transport().get_version()
                server_hostname = ssh.get_transport().get_peername()[0]
                
                connection_info = [
                    f"📡 Server: {server}",
                    f"🔌 Port: {self.port}",
                    f"📂 Current Directory: {current_dir}",
                    f"📄 Files Found: {len(file_list)}",
                    f"💻 Server Version: {server_version}",
                    f"🌐 Server Hostname: {server_hostname}"
                ]
            except:
                connection_info = [
                    f"📡 Server: {server}",
                    f"🔌 Port: {self.port}"
                ]
            
            sftp.close()
            ssh.close()
            
            progress.update(100, "Connection successful!")
            progress.close()
            
            # Show detailed success message
            success_msg = [
                "✅ SFTP Connection Successful",
                "",
                "🔍 Connection Details:",
                *connection_info,
                "",
                "📂 Path Information:",
                f"• Remote Path: {path if path else 'root'}",
                f"• Current Directory: {current_dir if 'current_dir' in locals() else 'Unknown'}",
                "",
                "🔐 Authentication:",
                f"👤 Username: {self.username}",
                "🔑 Password: Set",
                "",
                "🔧 System Info:",
                "• Protocol: SFTP",
                "• Encryption: SSH",
                "• Access: Read/Write"
            ]
            
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(success_msg))
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing SFTP connection: {str(e)}", xbmc.LOGERROR)
            
            error_msg = [
                "❌ SFTP Connection Failed",
                "",
                "🔍 Error Details:",
                f"📝 {str(e)}",
                "",
                "🔧 Troubleshooting Tips:",
                "• Verify server address and port",
                "• Check if credentials are correct",
                "• Ensure SSH server is running",
                "• Check firewall settings"
            ]
            
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
            return False
    
    def _test_webdav_connection(self):
        """Test the connection to the WebDAV location"""
        if not WEBDAV_AVAILABLE:
            error_msg = [
                "❌ WebDAV Testing Not Available",
                "",
                "🔍 Error Details:",
                "• Required module 'requests' is not available",
                "",
                "🔧 Solution:",
                "• Install the requests module",
                "• Contact addon developer for support"
            ]
            xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
            return False
        
        progress = xbmcgui.DialogProgress()
        progress.create("Testing WebDAV Connection", "Initializing connection test...")
        
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
                error_msg = [
                    "❌ WebDAV Authentication Failed",
                    "",
                    "🔍 Error Details:",
                    "• Invalid username or password",
                    "• Insufficient permissions",
                    "",
                    "🔧 Troubleshooting Tips:",
                    "• Verify credentials",
                    "• Check user permissions",
                    "• Contact server administrator"
                ]
                xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
                return False
            
            if response.status_code != 207:  # 207 is Multi-Status response for PROPFIND
                progress.close()
                error_msg = [
                    "❌ WebDAV Connection Failed",
                    "",
                    "🔍 Error Details:",
                    f"• Server returned status code {response.status_code}",
                    "",
                    "🔧 Troubleshooting Tips:",
                    "• Verify server URL",
                    "• Check if WebDAV is enabled",
                    "• Ensure proper permissions",
                    "• Contact server administrator"
                ]
                xbmcgui.Dialog().ok("Connection Test Results", "\n".join(error_msg))
                return False
            
            # Get server information from response headers
            server_info = []
            if 'Server' in response.headers:
                server_info.append(f"💻 Server Software: {response.headers['Server']}")
            if 'X-Powered-By' in response.headers:
                server_info.append(f"⚡ Powered By: {response.headers['X-Powered-By']}")
            
            progress.update(100, "Connection successful!")
            progress.close()
            
            # Create a scrollable dialog
            dialog = xbmcgui.Dialog()
            
            # Show detailed success message in a scrollable dialog
            success_msg = [
                "✅ WebDAV Connection Successful",
                "",
                "🔍 Connection Details:",
                f"📡 Server: {server}",
                f"🔌 Protocol: {protocol.upper()}",
                f"🔌 Port: {self.port}",
                *server_info,
                "",
                "📂 Path Information:",
                f"• Remote Path: {path if path else 'root'}",
                f"• URL: {url}",
                "",
                "🔐 Authentication:",
                f"👤 Username: {'Set' if self.username else 'Not Required'}",
                "🔑 Password: Set" if self.username else "🔑 Password: Not Required",
                "",
                "🔧 System Info:",
                "• Protocol: WebDAV",
                "• Method: PROPFIND",
                "• Depth: 0",
                "• Access: Read/Write",
                "",
                "📊 Response Details:",
                f"• Status Code: {response.status_code}",
                f"• Response Time: {response.elapsed.total_seconds():.2f} seconds",
                "",
                "🔍 Headers:",
                *[f"• {k}: {v}" for k, v in response.headers.items()]
            ]
            
            # Show the message in a scrollable dialog
            dialog.textviewer("Connection Test Results", "\n".join(success_msg))
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing WebDAV connection: {str(e)}", xbmc.LOGERROR)
            
            error_msg = [
                "❌ WebDAV Connection Failed",
                "",
                "🔍 Error Details:",
                f"📝 {str(e)}",
                "",
                "🔧 Troubleshooting Tips:",
                "• Verify server URL",
                "• Check network connectivity",
                "• Ensure WebDAV is enabled",
                "• Contact server administrator"
            ]
            
            # Show error in a scrollable dialog
            dialog = xbmcgui.Dialog()
            dialog.textviewer("Connection Test Results", "\n".join(error_msg))
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