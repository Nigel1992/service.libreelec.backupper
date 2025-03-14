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
        # For SMB, try to list the directory using xbmcvfs
        progress = xbmcgui.DialogProgress()
        progress.create("Testing Connection", "Testing SMB connection...")
        
        try:
            # Construct the full SMB URL
            smb_url = f"smb://"
            if self.username and self.password:
                smb_url += f"{self.username}:{self.password}@"
            smb_url += self.remote_path
            
            # Try to list the directory
            dirs, files = xbmcvfs.listdir(smb_url)
            
            progress.close()
            xbmcgui.Dialog().ok("Connection Successful", f"Successfully connected to SMB share: {self.remote_path}")
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing SMB connection: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Connection Failed", f"Failed to connect to SMB share: {str(e)}")
            return False
    
    def _test_nfs_connection(self):
        """Test the connection to the NFS location"""
        # For NFS, we can't easily test the connection
        progress = xbmcgui.DialogProgress()
        progress.create("Testing Connection", "Testing NFS connection...")
        
        try:
            # Just check if the path format is valid
            if '/' not in self.remote_path:
                progress.close()
                xbmcgui.Dialog().ok("Invalid NFS Path", "NFS path should be in the format 'server/export/path'")
                return False
            
            progress.close()
            xbmcgui.Dialog().ok("NFS Connection", "NFS connection cannot be fully tested. Please ensure your NFS server is properly configured.")
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing NFS connection: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Connection Failed", f"Failed to connect to NFS server: {str(e)}")
            return False
    
    def _test_ftp_connection(self):
        """Test the connection to the FTP location"""
        # For FTP, try to connect using ftplib
        progress = xbmcgui.DialogProgress()
        progress.create("Testing Connection", "Testing FTP connection...")
        
        try:
            # Extract server from path
            server = self.remote_path.split('/')[0]
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(server, int(self.port))
            ftp.login(self.username, self.password)
            ftp.quit()
            
            progress.close()
            xbmcgui.Dialog().ok("Connection Successful", f"Successfully connected to FTP server: {server}")
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing FTP connection: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Connection Failed", f"Failed to connect to FTP server: {str(e)}")
            return False
    
    def _test_sftp_connection(self):
        """Test the connection to the SFTP location"""
        # For SFTP, try to connect using paramiko
        if not SFTP_AVAILABLE:
            xbmcgui.Dialog().ok("Missing Dependency", "SFTP testing requires the paramiko module which is not available.")
            return False
        
        progress = xbmcgui.DialogProgress()
        progress.create("Testing Connection", "Testing SFTP connection...")
        
        try:
            # Extract server from path
            server = self.remote_path.split('/')[0]
            
            # Connect to SFTP server
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server, port=int(self.port), username=self.username, password=self.password)
            sftp = ssh.open_sftp()
            sftp.close()
            ssh.close()
            
            progress.close()
            xbmcgui.Dialog().ok("Connection Successful", f"Successfully connected to SFTP server: {server}")
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing SFTP connection: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Connection Failed", f"Failed to connect to SFTP server: {str(e)}")
            return False
    
    def _test_webdav_connection(self):
        """Test the connection to the WebDAV location"""
        # For WebDAV, try to connect using requests
        if not WEBDAV_AVAILABLE:
            xbmcgui.Dialog().ok("Missing Dependency", "WebDAV testing requires the requests module which is not available.")
            return False
        
        progress = xbmcgui.DialogProgress()
        progress.create("Testing Connection", "Testing WebDAV connection...")
        
        try:
            # Extract server from path
            server = self.remote_path.split('/')[0]
            path = '/'.join(self.remote_path.split('/')[1:])
            
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
                xbmcgui.Dialog().ok("Authentication Failed", "Failed to authenticate with the WebDAV server. Please check your username and password.")
                return False
            
            if response.status_code != 207:  # 207 is Multi-Status response for PROPFIND
                progress.close()
                xbmcgui.Dialog().ok("WebDAV Error", f"Failed to connect to WebDAV server. Server returned status code {response.status_code}.")
                return False
            
            progress.close()
            xbmcgui.Dialog().ok("Connection Successful", f"Successfully connected to WebDAV server: {server}")
            return True
            
        except Exception as e:
            progress.close()
            xbmc.log(f"{ADDON_ID}: Error testing WebDAV connection: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().ok("Connection Failed", f"Failed to connect to WebDAV server: {str(e)}")
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