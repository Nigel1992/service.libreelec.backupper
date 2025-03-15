#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import glob
import shutil
import xbmc
import xbmcaddon
import xbmcvfs
import subprocess
from datetime import datetime, timedelta
import zipfile
import json
import time
import gc  # Add garbage collector import
import re
import ftplib
import socket
import urllib.parse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xbmcgui

# Try to import paramiko, but don't fail if it's not available
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False
    xbmc.log("Paramiko module not available. SFTP functionality will be disabled.", xbmc.LOGWARNING)

class BackupManager:
    """Utility class to manage config backups"""
    
    def __init__(self, addon=None):
        self.addon = addon or xbmcaddon.Addon()
        self.update_backup_location()
        self._temp_files = set()  # Track temporary files
        self.remote_connection = None
        self._webdav_session = None  # Persistent WebDAV session
        self.temp_dir = None  # Initialize temp_dir
        self._cleanup_old_temp_files()  # Clean up any old temp files on startup
    
    def update_backup_location(self):
        """Update backup location from settings"""
        # Get backup location type from settings
        self.location_type = int(self.addon.getSetting('backup_location_type') or "0")
        
        # Define paths for various Kodi directories
        self.kodi_home = xbmcvfs.translatePath('special://home')
        self.kodi_userdata = xbmcvfs.translatePath('special://userdata')
        
        # Initialize backup_dir
        self.backup_dir = None
        
        # Handle local backup location
        if self.location_type == 0:  # Local
            self.backup_dir = self.addon.getSetting('backup_location')
            if not self.backup_dir:
                self.backup_dir = "/storage/backup"  # Default location
        else:  # Remote
            # Get remote settings
            self.remote_type = int(self.addon.getSetting('remote_location_type') or "0")
            self.remote_path = self.addon.getSetting('remote_path')
            self.remote_username = self.addon.getSetting('remote_username')
            self.remote_password = self.addon.getSetting('remote_password')
            self.remote_port = int(self.addon.getSetting('remote_port') or "0")
            
            # Set default ports if not specified
            if self.remote_port == 0:
                if self.remote_type == 0:  # SMB
                    self.remote_port = 445
                elif self.remote_type == 1:  # NFS
                    self.remote_port = 2049
                elif self.remote_type == 2:  # FTP
                    self.remote_port = 21
                elif self.remote_type == 3:  # SFTP
                    self.remote_port = 22
                elif self.remote_type == 4:  # WebDAV
                    self.remote_port = 80
            
            # Create a temporary local directory for staging remote files
            self.backup_dir = os.path.join(xbmcvfs.translatePath('special://temp'), 'libreelec_backupper')
        
        # Ensure backup directory exists
        if self.backup_dir and not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir)
            except Exception as e:
                xbmc.log(f"Error creating backup directory: {str(e)}", xbmc.LOGERROR)
                # Fall back to addon profile if custom location can't be created
                self.backup_dir = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
                if not os.path.exists(self.backup_dir):
                    os.makedirs(self.backup_dir)
                if self.location_type == 0:  # Only update setting for local backups
                    self.addon.setSetting('backup_location', self.backup_dir)
    
    def _create_webdav_session(self):
        """Create a WebDAV session with retry logic and connection pooling"""
        if self._webdav_session is not None:
            return self._webdav_session
            
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504]  # retry on these status codes
        )
        
        # Create session with connection pooling
        session = requests.Session()
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=1,  # maintain one connection in the pool
            pool_maxsize=1,  # max number of connections in the pool
            pool_block=False  # don't block when pool is full
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        if self.remote_username:
            session.auth = (self.remote_username, self.remote_password)
            
        self._webdav_session = session
        return session

    def connect_remote(self):
        """Connect to the remote location"""
        if self.location_type == 0:  # Local
            return True
        
        try:
            if self.remote_type == 0:  # SMB
                # Use Kodi's built-in SMB support via xbmcvfs
                remote_url = f"smb://{self.remote_username}:{urllib.parse.quote(self.remote_password)}@{self.remote_path}"
                self.remote_connection = remote_url
                # Test connection by trying to list directory
                dirs, files = xbmcvfs.listdir(remote_url)
                return True
                
            elif self.remote_type == 1:  # NFS
                # Mount NFS share
                mount_point = os.path.join(self.backup_dir, "nfs_mount")
                if not os.path.exists(mount_point):
                    os.makedirs(mount_point)
                
                # Unmount if already mounted
                subprocess.call(["umount", mount_point], stderr=subprocess.DEVNULL)
                
                # Mount the NFS share
                result = subprocess.call(["mount", "-t", "nfs", self.remote_path, mount_point])
                if result == 0:
                    self.remote_connection = mount_point
                    return True
                else:
                    xbmc.log(f"Failed to mount NFS share: {self.remote_path}", xbmc.LOGERROR)
                    return False
                
            elif self.remote_type == 2:  # FTP
                # Connect to FTP server
                ftp = ftplib.FTP()
                ftp.connect(self.remote_path.split('/')[0], self.remote_port)
                ftp.login(self.remote_username, self.remote_password)
                
                # Change to the specified directory if provided
                if '/' in self.remote_path:
                    remote_dir = '/'.join(self.remote_path.split('/')[1:])
                    if remote_dir:
                        ftp.cwd(remote_dir)
                
                self.remote_connection = ftp
                return True
                
            elif self.remote_type == 3:  # SFTP
                # Check if paramiko is available
                if not PARAMIKO_AVAILABLE:
                    xbmc.log("Cannot use SFTP: Paramiko module not available", xbmc.LOGERROR)
                    return False
                
                # Connect to SFTP server
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                host = self.remote_path.split('/')[0]
                ssh.connect(host, port=self.remote_port, username=self.remote_username, password=self.remote_password)
                
                sftp = ssh.open_sftp()
                
                # Change to the specified directory if provided
                if '/' in self.remote_path:
                    remote_dir = '/'.join(self.remote_path.split('/')[1:])
                    if remote_dir:
                        sftp.chdir(remote_dir)
                
                self.remote_connection = sftp
                return True
                
            elif self.remote_type == 4:  # WebDAV
                # Use the entire WebDAV URL from settings
                webdav_url = self.remote_path
                if not webdav_url.startswith(('http://', 'https://')):
                    # For Koofr, we need to use the correct WebDAV URL format
                    if 'koofr.net' in webdav_url:
                        # Extract the path components
                        parts = webdav_url.split('/')
                        if len(parts) >= 4:
                            # Construct the proper Koofr WebDAV URL
                            webdav_url = f"https://{parts[0]}/dav/{parts[2]}/{parts[3]}"
                            if len(parts) > 4:
                                webdav_url += '/' + '/'.join(parts[4:])
                    else:
                        # For other WebDAV servers, use standard format
                        webdav_url = f"https://{webdav_url}" if self.remote_port == 443 else f"http://{webdav_url}"
                
                if not webdav_url.endswith('/'):
                    webdav_url += '/'
                xbmc.log(f"Testing WebDAV connection to: {webdav_url}", xbmc.LOGINFO)
                
                # Get or create WebDAV session
                try:
                    session = self._create_webdav_session()
                    xbmc.log("WebDAV session created successfully", xbmc.LOGINFO)
                except Exception as e:
                    xbmc.log(f"Failed to create WebDAV session: {str(e)}", xbmc.LOGERROR)
                    return False
                
                # Set credentials if provided
                if self.remote_username and self.remote_password:
                    try:
                        session.auth = (self.remote_username, self.remote_password)
                        xbmc.log("WebDAV credentials set successfully", xbmc.LOGINFO)
                    except Exception as e:
                        xbmc.log(f"Failed to set WebDAV credentials: {str(e)}", xbmc.LOGERROR)
                        return False
                
                # Test connection with retry logic
                try:
                    xbmc.log(f"Testing WebDAV connection to: {webdav_url}", xbmc.LOGINFO)
                    response = session.request('PROPFIND', webdav_url, headers={'Depth': '1'})
                    xbmc.log(f"WebDAV response status: {response.status_code}", xbmc.LOGINFO)
                    xbmc.log(f"WebDAV response headers: {dict(response.headers)}", xbmc.LOGINFO)
                    xbmc.log(f"WebDAV response text: {response.text}", xbmc.LOGINFO)
                    
                    if response.status_code in [207, 200]:  # 207 is Multi-Status response
                        self.remote_connection = {
                            'session': session,
                            'base_url': webdav_url
                        }
                        xbmc.log("WebDAV connection successful", xbmc.LOGINFO)
                        return True
                    else:
                        xbmc.log(f"WebDAV connection failed with status code: {response.status_code}", xbmc.LOGERROR)
                        xbmc.log(f"WebDAV response: {response.text}", xbmc.LOGERROR)
                        return False
                except requests.exceptions.RetryError as e:
                    xbmc.log(f"WebDAV connection failed after retries: {str(e)}", xbmc.LOGERROR)
                    return False
                except requests.exceptions.RequestException as e:
                    xbmc.log(f"WebDAV request failed: {str(e)}", xbmc.LOGERROR)
                    return False
                except Exception as e:
                    xbmc.log(f"Unexpected error during WebDAV connection: {str(e)}", xbmc.LOGERROR)
                    return False
                
        except Exception as e:
            xbmc.log(f"Error connecting to remote location: {str(e)}", xbmc.LOGERROR)
            return False
    
    def disconnect_remote(self):
        """Disconnect from the remote location"""
        if self.location_type == 0 or not self.remote_connection:  # Local or not connected
            return
        
        try:
            if self.remote_type == 0:  # SMB
                # Nothing to disconnect for SMB via xbmcvfs
                self.remote_connection = None
                
            elif self.remote_type == 1:  # NFS
                # Unmount NFS share
                mount_point = self.remote_connection
                subprocess.call(["umount", mount_point], stderr=subprocess.DEVNULL)
                self.remote_connection = None
                
            elif self.remote_type == 2:  # FTP
                # Close FTP connection
                self.remote_connection.quit()
                self.remote_connection = None
                
            elif self.remote_type == 3:  # SFTP
                # Close SFTP connection
                self.remote_connection.close()
                self.remote_connection.get_channel().get_transport().close()
                self.remote_connection = None
                
            elif self.remote_type == 4:  # WebDAV
                # Don't close the session, just clear the connection info
                self.remote_connection = None
                
        except Exception as e:
            xbmc.log(f"Error disconnecting from remote location: {str(e)}", xbmc.LOGERROR)
    
    def get_remote_path(self, filename):
        """Get the full path to a file on the remote location"""
        if self.location_type == 0:  # Local
            return os.path.join(self.backup_dir, filename)
        
        if self.remote_type == 0:  # SMB
            if self.remote_connection.endswith('/'):
                return f"{self.remote_connection}{filename}"
            else:
                return f"{self.remote_connection}/{filename}"
                
        elif self.remote_type == 1:  # NFS
            return os.path.join(self.remote_connection, filename)
                
        elif self.remote_type in [2, 3]:  # FTP or SFTP
            return filename  # Just return the filename for FTP/SFTP
            
        elif self.remote_type == 4:  # WebDAV
            base_url = self.remote_connection['base_url']
            if base_url.endswith('/'):
                return f"{base_url}{filename}"
            else:
                return f"{base_url}/{filename}"
    
    def upload_file(self, local_path, remote_filename):
        """Upload a file to the remote location"""
        if self.location_type == 0:  # Local
            # Just copy the file to the backup directory
            dest_path = os.path.join(self.backup_dir, remote_filename)
            shutil.copy2(local_path, dest_path)
            return True
        
        try:
            if self.remote_type == 0:  # SMB
                # Use xbmcvfs to copy the file
                remote_path = self.get_remote_path(remote_filename)
                return xbmcvfs.copy(local_path, remote_path)
                
            elif self.remote_type == 1:  # NFS
                # Copy the file to the mounted directory
                remote_path = self.get_remote_path(remote_filename)
                shutil.copy2(local_path, remote_path)
                return True
                
            elif self.remote_type == 2:  # FTP
                # Upload the file via FTP
                with open(local_path, 'rb') as f:
                    self.remote_connection.storbinary(f'STOR {remote_filename}', f)
                return True
                
            elif self.remote_type == 3:  # SFTP
                # Upload the file via SFTP
                self.remote_connection.put(local_path, remote_filename)
                return True
                
            elif self.remote_type == 4:  # WebDAV
                # Upload the file via WebDAV
                remote_url = self.get_remote_path(remote_filename)
                with open(local_path, 'rb') as f:
                    response = self.remote_connection['session'].put(remote_url, data=f)
                    return response.status_code in [200, 201, 204]
                
        except Exception as e:
            xbmc.log(f"Error uploading file to remote location: {str(e)}", xbmc.LOGERROR)
            return False
    
    def download_file(self, remote_filename, local_path):
        """Download a file from the remote location"""
        if self.location_type == 0:  # Local
            # Just copy the file from the backup directory
            source_path = os.path.join(self.backup_dir, remote_filename)
            shutil.copy2(source_path, local_path)
            return True
        
        try:
            if self.remote_type == 0:  # SMB
                # Use xbmcvfs to copy the file
                remote_path = self.get_remote_path(remote_filename)
                return xbmcvfs.copy(remote_path, local_path)
                
            elif self.remote_type == 1:  # NFS
                # Copy the file from the mounted directory
                remote_path = self.get_remote_path(remote_filename)
                shutil.copy2(remote_path, local_path)
                return True
                
            elif self.remote_type == 2:  # FTP
                # Download the file via FTP
                with open(local_path, 'wb') as f:
                    self.remote_connection.retrbinary(f'RETR {remote_filename}', f.write)
                return True
                
            elif self.remote_type == 3:  # SFTP
                # Download the file via SFTP
                self.remote_connection.get(remote_filename, local_path)
                return True
                
            elif self.remote_type == 4:  # WebDAV
                # Download the file via WebDAV
                remote_url = self.get_remote_path(remote_filename)
                response = self.remote_connection['session'].get(remote_url, stream=True)
                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                return False
                
        except Exception as e:
            xbmc.log(f"Error downloading file from remote location: {str(e)}", xbmc.LOGERROR)
            return False
    
    def list_remote_files(self):
        """List files in the remote location"""
        if self.location_type == 0:  # Local
            # Just list files in the backup directory
            return [f for f in os.listdir(self.backup_dir) if os.path.isfile(os.path.join(self.backup_dir, f))]
        
        try:
            if self.remote_type == 0:  # SMB
                # Use xbmcvfs to list files
                xbmc.log(f"Listing SMB files from: {self.remote_connection}", xbmc.LOGINFO)
                _, files = xbmcvfs.listdir(self.remote_connection)
                xbmc.log(f"Found {len(files)} files via SMB", xbmc.LOGINFO)
                return files
                
            elif self.remote_type == 1:  # NFS
                # List files in the mounted directory
                xbmc.log(f"Listing NFS files from: {self.remote_connection}", xbmc.LOGINFO)
                files = [f for f in os.listdir(self.remote_connection) if os.path.isfile(os.path.join(self.remote_connection, f))]
                xbmc.log(f"Found {len(files)} files via NFS", xbmc.LOGINFO)
                return files
                
            elif self.remote_type == 2:  # FTP
                # List files via FTP
                xbmc.log(f"Listing FTP files", xbmc.LOGINFO)
                files = self.remote_connection.nlst()
                # Filter out directories and hidden files
                files = [f for f in files if not f.startswith('.') and not self.is_remote_dir(f)]
                xbmc.log(f"Found {len(files)} files via FTP", xbmc.LOGINFO)
                return files
                
            elif self.remote_type == 3:  # SFTP
                # List files via SFTP
                xbmc.log(f"Listing SFTP files", xbmc.LOGINFO)
                files = [f for f in self.remote_connection.listdir() if not self.is_remote_dir(f)]
                xbmc.log(f"Found {len(files)} files via SFTP", xbmc.LOGINFO)
                return files
                
            elif self.remote_type == 4:  # WebDAV
                # List files via WebDAV
                xbmc.log(f"Listing WebDAV files from: {self.remote_connection['base_url']}", xbmc.LOGINFO)
                xbmc.log(f"Using WebDAV credentials: username={self.remote_username}, password={'*' * len(self.remote_password) if self.remote_password else 'None'}", xbmc.LOGINFO)
                
                response = self.remote_connection['session'].request(
                    'PROPFIND', 
                    self.remote_connection['base_url'], 
                    headers={'Depth': '1'}
                )
                
                xbmc.log(f"WebDAV PROPFIND response status: {response.status_code}", xbmc.LOGINFO)
                xbmc.log(f"WebDAV response headers: {dict(response.headers)}", xbmc.LOGINFO)
                xbmc.log(f"WebDAV response text: {response.text}", xbmc.LOGINFO)
                
                if response.status_code != 207:  # Multi-Status response
                    xbmc.log(f"WebDAV PROPFIND failed with status code: {response.status_code}", xbmc.LOGERROR)
                    xbmc.log(f"WebDAV response: {response.text}", xbmc.LOGERROR)
                    return []
                
                # Parse XML response to get file names
                files = []
                
                # Log the raw response text for debugging
                xbmc.log(f"Raw response text: {response.text}", xbmc.LOGINFO)
                
                # Look for both href and displayname tags (case insensitive)
                response_lines = response.text.splitlines()
                
                for line in response_lines:
                    # Check for href tags (case insensitive)
                    if '<D:href>' in line and '</D:href>' in line:
                        href = line[line.find('<D:href>')+8:line.find('</D:href>')]
                        filename = href.split('/')[-1] if href.split('/')[-1] else href.split('/')[-2]
                        filename = urllib.parse.unquote(filename)
                        xbmc.log(f"Found href: {filename}", xbmc.LOGINFO)
                        
                        if filename.endswith('.zip'):
                            if filename not in files:  # Avoid duplicates
                                files.append(filename)
                                xbmc.log(f"Added file from href: {filename}", xbmc.LOGINFO)
                    
                    # Check for displayname tags (case insensitive)
                    if '<D:displayname>' in line and '</D:displayname>' in line:
                        filename = line[line.find('<D:displayname>')+14:line.find('</D:displayname>')]
                        xbmc.log(f"Found displayname: {filename}", xbmc.LOGINFO)
                        
                        if filename.endswith('.zip'):
                            if filename not in files:  # Avoid duplicates
                                files.append(filename)
                                xbmc.log(f"Added file from displayname: {filename}", xbmc.LOGINFO)
                
                xbmc.log(f"Final list of backup files found: {files}", xbmc.LOGINFO)
                xbmc.log(f"Found {len(files)} backup files via WebDAV", xbmc.LOGINFO)
                return files
                
        except Exception as e:
            xbmc.log(f"Error listing files in remote location: {str(e)}", xbmc.LOGERROR)
            import traceback
            xbmc.log(f"Traceback: {traceback.format_exc()}", xbmc.LOGERROR)
            return []
    
    def is_remote_dir(self, path):
        """Check if a path on the remote location is a directory"""
        if self.remote_type == 3:  # SFTP
            try:
                return self.remote_connection.stat(path).st_mode & 0o40000 != 0
            except:
                return False
        return False
    
    def delete_remote_file(self, filename):
        """Delete a file from the remote location"""
        if self.location_type == 0:  # Local
            # Just delete the file from the backup directory
            os.remove(os.path.join(self.backup_dir, filename))
            return True
        
        try:
            if self.remote_type == 0:  # SMB
                # Use xbmcvfs to delete the file
                remote_path = self.get_remote_path(filename)
                return xbmcvfs.delete(remote_path)
                
            elif self.remote_type == 1:  # NFS
                # Delete the file from the mounted directory
                remote_path = self.get_remote_path(filename)
                os.remove(remote_path)
                return True
                
            elif self.remote_type == 2:  # FTP
                # Delete the file via FTP
                self.remote_connection.delete(filename)
                return True
                
            elif self.remote_type == 3:  # SFTP
                # Delete the file via SFTP
                self.remote_connection.remove(filename)
                return True
                
            elif self.remote_type == 4:  # WebDAV
                # Delete the file via WebDAV
                remote_url = self.get_remote_path(filename)
                response = self.remote_connection['session'].delete(remote_url)
                return response.status_code in [200, 204]
                
        except Exception as e:
            xbmc.log(f"Error deleting file from remote location: {str(e)}", xbmc.LOGERROR)
            return False
    
    def get_next_backup_time(self):
        """Calculate the next backup time based on schedule settings"""
        return None
    
    def update_schedule_info(self):
        """Update the last and next backup time in settings"""
        pass
    
    def should_run_backup(self):
        """Check if it's time to run a scheduled backup"""
        return False
    
    def notify(self, message, detailed_info="", persistent=False):
        """Show notification if enabled"""
        if self.addon.getSettingBool('show_notifications'):
            # Always show progress information regardless of detailed_notifications setting
            if any(keyword in message.lower() for keyword in ['progress:', 'backing up', 'processed:']):
                # For progress notifications, always show the detailed info
                message = f"{message} - {detailed_info}" if detailed_info else message
            # For other notifications, respect detailed_notifications setting
            elif self.addon.getSettingBool('detailed_notifications') and detailed_info:
                message = f"{message} - {detailed_info}"
            
            # Make backup/restore notifications persistent by default
            if any(keyword in message.lower() for keyword in ['backup', 'restore', 'progress']):
                persistent = True
            
            # For persistent notifications, use a longer timeout (30 seconds)
            # For non-persistent, use the default 3 seconds
            timeout = 30000 if persistent else 3000
            
            # Get the addon icon path
            icon = xbmcvfs.translatePath(os.path.join(self.addon.getAddonInfo('path'), 'resources', 'icon.png'))
            xbmc.executebuiltin(f'Notification({self.addon.getAddonInfo("name")}, {message}, {timeout}, {icon})')
    
    def format_size(self, size_bytes):
        """Format file size in bytes to human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/1024/1024:.1f} MB"
        else:
            return f"{size_bytes/1024/1024/1024:.2f} GB"
    
    def get_repository_paths(self):
        """Get all repository addon paths"""
        repo_paths = {}
        addons_dir = os.path.join(self.kodi_home, 'addons')
        if os.path.exists(addons_dir):
            for item in os.listdir(addons_dir):
                if item.startswith('repository.') and os.path.isdir(os.path.join(addons_dir, item)):
                    # Add the repository addon folder
                    repo_paths[f'repo_{item}'] = os.path.join(addons_dir, item)
                    # Add its addon data if it exists
                    addon_data_path = os.path.join(self.kodi_userdata, 'addon_data', item)
                    if os.path.exists(addon_data_path):
                        repo_paths[f'repo_data_{item}'] = addon_data_path
        return repo_paths

    def get_backup_paths(self):
        """Get paths for all backup items based on settings"""
        paths = {}
        
        # Log which backup items are selected
        xbmc.log("Backup items selected:", xbmc.LOGINFO)
        xbmc.log(f"Configs: {self.addon.getSettingBool('backup_configs')}", xbmc.LOGINFO)
        xbmc.log(f"Addons: {self.addon.getSettingBool('backup_addons')}", xbmc.LOGINFO)
        xbmc.log(f"Repositories: {self.addon.getSettingBool('backup_repositories')}", xbmc.LOGINFO)
        xbmc.log(f"Userdata: {self.addon.getSettingBool('backup_userdata')}", xbmc.LOGINFO)
        xbmc.log(f"Sources: {self.addon.getSettingBool('backup_sources')}", xbmc.LOGINFO)
        
        # Configuration Files
        if self.addon.getSettingBool('backup_configs'):
            # Create temp directory if it doesn't exist
            if not self.temp_dir:
                self.temp_dir = os.path.join(xbmc.translatePath('special://temp'), 'libreelec_backupper')
                os.makedirs(self.temp_dir, exist_ok=True)
                self._temp_files.add(self.temp_dir)  # Track for cleanup

            # Handle config.txt specially - copy to temp location first
            config_src = '/flash/config.txt'
            if os.path.exists(config_src):
                config_temp = os.path.join(self.temp_dir, 'config.txt')
                try:
                    shutil.copy2(config_src, config_temp)
                    self._temp_files.add(config_temp)  # Track for cleanup
                    paths['config'] = config_temp  # Use temp location for backup
                    xbmc.log(f"Copied config.txt to temp location: {config_temp}", xbmc.LOGINFO)
                except Exception as e:
                    xbmc.log(f"Failed to copy config.txt: {str(e)}", xbmc.LOGERROR)

            # Add other config files
            config_paths = {
                'guisettings': os.path.join(self.kodi_userdata, 'guisettings.xml'),
                'advancedsettings': os.path.join(self.kodi_userdata, 'advancedsettings.xml'),
                'keyboard': os.path.join(self.kodi_userdata, 'keyboard.xml'),
                'keymaps': os.path.join(self.kodi_userdata, 'keymaps')
            }
            # Only add paths that exist
            for key, path in config_paths.items():
                if os.path.exists(path):
                    paths[key] = path
            xbmc.log(f"Added config paths: {list(paths.keys())}", xbmc.LOGINFO)
        
        # Sources
        if self.addon.getSettingBool('backup_sources'):
            sources_path = os.path.join(self.kodi_userdata, 'sources.xml')
            if os.path.exists(sources_path):
                paths['sources'] = sources_path
                xbmc.log("Added sources path", xbmc.LOGINFO)
        
        # Addons
        if self.addon.getSettingBool('backup_addons'):
            addons_path = os.path.join(self.kodi_home, 'addons')
            if os.path.exists(addons_path):
                paths['addons'] = addons_path
                xbmc.log("Added addons path", xbmc.LOGINFO)
        
        # Repositories
        if self.addon.getSettingBool('backup_repositories'):
            repo_paths = self.get_repository_paths()
            if repo_paths:
                paths.update(repo_paths)
                xbmc.log(f"Added repository paths: {list(repo_paths.keys())}", xbmc.LOGINFO)
        
        # Addon User Data and Settings
        if self.addon.getSettingBool('backup_userdata'):
            addon_data_path = os.path.join(self.kodi_userdata, 'addon_data')
            if os.path.exists(addon_data_path):
                paths['addon_data'] = addon_data_path
                xbmc.log("Added addon data path", xbmc.LOGINFO)
        
        xbmc.log(f"Final backup paths: {list(paths.keys())}", xbmc.LOGINFO)
        return paths
    
    def cleanup_resources(self):
        """Clean up resources before addon shutdown"""
        try:
            # Close WebDAV session if it exists
            if hasattr(self, '_webdav_session') and self._webdav_session is not None:
                try:
                    self._webdav_session.close()
                except Exception as e:
                    xbmc.log(f"Error closing WebDAV session: {str(e)}", xbmc.LOGWARNING)
                finally:
                    self._webdav_session = None
                
            # Disconnect remote connection
            if hasattr(self, 'remote_connection') and self.remote_connection is not None:
                try:
                    self.disconnect_remote()
                except Exception as e:
                    xbmc.log(f"Error disconnecting remote: {str(e)}", xbmc.LOGWARNING)
            
            # Clean up temporary files
            if hasattr(self, '_temp_files'):
                for temp_file in self._temp_files:
                    try:
                        if os.path.exists(temp_file):
                            if os.path.isdir(temp_file):
                                shutil.rmtree(temp_file, ignore_errors=True)
                            else:
                                os.remove(temp_file)
                    except Exception as e:
                        xbmc.log(f"Error removing temp file {temp_file}: {str(e)}", xbmc.LOGWARNING)
            
            self._temp_files.clear()
            
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            xbmc.log(f"Error during resource cleanup: {str(e)}", xbmc.LOGERROR)

    def _cleanup_old_temp_files(self):
        """Clean up any old temporary files from previous sessions"""
        try:
            temp_dir = os.path.join(xbmcvfs.translatePath('special://temp'), 'libreelec_backupper')
            if os.path.exists(temp_dir):
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        # Skip JSON files that contain remote backup information
                        if item.endswith('.json') and 'remote_backup_' in item:
                            xbmc.log(f"Preserving remote backup info file: {item}", xbmc.LOGINFO)
                            continue
                            
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        xbmc.log(f"Error cleaning up old temp file {item}: {str(e)}")
        except Exception as e:
            xbmc.log(f"Error in cleanup_old_temp_files: {str(e)}")

    def cleanup_current_session(self):
        """Clean up temporary files from current session"""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                # Don't delete JSON files containing remote backup information
                for item in os.listdir(self.temp_dir):
                    item_path = os.path.join(self.temp_dir, item)
                    if item.endswith('.json') and 'remote_backup_' in item:
                        xbmc.log(f"Preserving remote backup info file: {item}", xbmc.LOGINFO)
                        continue
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        xbmc.log(f"Error removing temp file {item}: {str(e)}")
                xbmc.log("Cleaned up current session temporary directory")
        except Exception as e:
            xbmc.log(f"Error in cleanup_current_session: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup_current_session()
        except Exception as e:
            xbmc.log(f"Error in destructor: {str(e)}")

    def buffered_copy(self, source, dest, file_size, processed_size, total_size):
        """Copy file with progress updates using buffered reads"""
        buffer_size = 1024 * 1024  # 1MB buffer
        bytes_copied = 0
        last_update = 0
        
        while True:
            chunk = source.read(buffer_size)
            if not chunk:
                break
            dest.write(chunk)
            bytes_copied += len(chunk)
            current_total = processed_size + bytes_copied
            
            # Update progress every ~1% or at least every 1MB
            progress = int((current_total / total_size) * 100) if total_size > 0 else 0
            if progress > last_update or bytes_copied >= buffer_size:
                last_update = progress
                processed_formatted = self.format_size(current_total)
                total_formatted = self.format_size(total_size)
                self.notify("Backing up files", f"{processed_formatted} / {total_formatted} ({progress}%)")
        
        return bytes_copied

    def create_backup(self, backup_name=None):
        """Create a backup of the selected items"""
        try:
            # Clean up any old temporary files first
            self._cleanup_old_temp_files()
            
            # Create a new temporary directory for this session
            self.temp_dir = os.path.join(xbmcvfs.translatePath('special://temp'), 'libreelec_backupper', str(int(time.time())))
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # Update backup location in case it changed
            self.update_backup_location()
            
            # Connect to remote location if needed
            if self.location_type != 0:  # Remote
                if not self.connect_remote():
                    self.notify("Backup failed", "Failed to connect to remote location")
                    return False, "Failed to connect to remote location"
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Get paths to backup
            paths = self.get_backup_paths()
            
            # Log the paths that will be backed up
            xbmc.log(f"Paths to backup: {paths}", xbmc.LOGINFO)
            
            # Don't create empty backups
            if not paths:
                self.notify("Backup failed", "No items selected for backup")
                return False, "No items selected for backup"
            
            # Create backup name with included items
            backup_items = []
            if self.addon.getSettingBool('backup_configs'):
                backup_items.append('conf')
            if self.addon.getSettingBool('backup_addons'):
                backup_items.append('addons')
            if self.addon.getSettingBool('backup_repositories'):
                backup_items.append('repos')
            if self.addon.getSettingBool('backup_userdata'):
                backup_items.append('userdata')
            if self.addon.getSettingBool('backup_sources'):
                backup_items.append('src')
            
            # Add items to backup name
            items_str = '-'.join(backup_items) if backup_items else 'empty'
            backup_name = f'backup_{items_str}_{timestamp}'
            
            # Create backup path in temp directory
            backup_path = os.path.join(self.temp_dir, f'{backup_name}.zip')
            self._temp_files.add(backup_path)  # Track for cleanup
            self._temp_files.add(self.temp_dir)  # Track temp directory for cleanup
            
            try:
                # Show initial notification
                self.notify("Starting backup...", "Calculating total size...")
                
                # Calculate total size and collect files to backup
                total_size = 0
                files_to_backup = []
                processed_size = 0  # Track processed size
                
                # Process each path based on its type
                for item_name, path in paths.items():
                    xbmc.log(f"Processing backup item: {item_name} at path: {path}", xbmc.LOGINFO)
                    
                    if not os.path.exists(path):
                        xbmc.log(f"Path does not exist: {path}", xbmc.LOGWARNING)
                        continue
                        
                    if os.path.isfile(path):
                        if not os.path.islink(path):  # Skip symbolic links
                            try:
                                file_size = os.path.getsize(path)
                                total_size += file_size
                                
                                # Determine the appropriate archive name for configuration files
                                if item_name == 'config':
                                    arcname = 'flash/config.txt'  # Ensure config.txt goes to flash directory
                                elif item_name == 'sources':
                                    arcname = 'userdata/sources.xml'
                                elif item_name == 'guisettings':
                                    arcname = 'userdata/guisettings.xml'
                                elif item_name == 'advancedsettings':
                                    arcname = 'userdata/advancedsettings.xml'
                                elif item_name == 'keyboard':
                                    arcname = 'userdata/keyboard.xml'
                                else:
                                    arcname = item_name
                                    
                                files_to_backup.append((path, arcname, file_size))
                                xbmc.log(f"Added file to backup: {path} as {arcname} ({self.format_size(file_size)})", xbmc.LOGINFO)
                            except OSError as e:
                                xbmc.log(f"Error getting size for {path}: {str(e)}", xbmc.LOGWARNING)
                                continue
                    else:  # Directory
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                if not os.path.islink(file_path):  # Skip symbolic links
                                    try:
                                        file_size = os.path.getsize(file_path)
                                        total_size += file_size
                                        
                                        # Determine relative path based on directory type
                                        if item_name == 'addons':
                                            rel_path = os.path.relpath(file_path, os.path.dirname(path))
                                            arcname = rel_path
                                        elif item_name == 'addon_data':
                                            rel_path = os.path.relpath(file_path, os.path.dirname(path))
                                            arcname = f"userdata/{rel_path}"
                                        elif item_name == 'keymaps':
                                            rel_path = os.path.relpath(file_path, path)
                                            arcname = f"userdata/keymaps/{rel_path}"
                                        elif item_name.startswith('repo_'):
                                            rel_path = os.path.relpath(file_path, os.path.dirname(path))
                                            arcname = f"repo/{rel_path}"
                                        else:
                                            rel_path = os.path.relpath(file_path, path)
                                            arcname = f"{item_name}/{rel_path}"
                                        
                                        files_to_backup.append((file_path, arcname, file_size))
                                    except OSError as e:
                                        xbmc.log(f"Error getting size for {file_path}: {str(e)}", xbmc.LOGWARNING)
                                        continue
                
                xbmc.log(f"Total files to backup: {len(files_to_backup)}", xbmc.LOGINFO)
                total_size_formatted = self.format_size(total_size)
                self.notify("Starting backup", f"Total size: {total_size_formatted}")
                xbmc.log(f"Total backup size: {total_size_formatted} ({total_size} bytes)", xbmc.LOGINFO)
                
                # Create manifest
                manifest = {
                    'timestamp': timestamp,
                    'items': list(paths.keys()),
                    'paths': paths,
                    'backed_up_files': [],
                    'total_size': total_size,
                    'total_size_formatted': total_size_formatted
                }
                
                # Set compression settings based on addon settings
                compression_level = self.addon.getSettingInt('compression_level')
                # Map compression settings to actual ZIP compression levels
                compression_mapping = {
                    0: (zipfile.ZIP_STORED, 0),    # None
                    1: (zipfile.ZIP_DEFLATED, 1),  # Fast
                    2: (zipfile.ZIP_DEFLATED, 6),  # Normal
                    3: (zipfile.ZIP_DEFLATED, 9)   # Maximum
                }
                compression_method, compression_strength = compression_mapping.get(compression_level, (zipfile.ZIP_DEFLATED, 6))
                
                # Create ZIP file with selected compression
                with zipfile.ZipFile(backup_path, 'w', compression=compression_method, compresslevel=compression_strength, allowZip64=True) as zipf:
                    # Process each file
                    last_update_time = time.time()
                    update_interval = 0.5  # Update progress every 0.5 seconds
                    batch_size = 0  # Track size of current batch
                    
                    for file_path, arcname, file_size in files_to_backup:
                        try:
                            # Read and write directly to zip
                            with open(file_path, 'rb') as source:
                                # Create a ZipInfo object for more control
                                info = zipfile.ZipInfo(arcname)
                                info.file_size = file_size
                                info.compress_type = compression_method
                                
                                # Open entry in zip file
                                with zipf.open(info, mode='w') as dest:
                                    # Copy with batched progress updates
                                    buffer_size = 1024 * 1024  # 1MB buffer
                                    bytes_copied = 0
                                    
                                    while True:
                                        chunk = source.read(buffer_size)
                                        if not chunk:
                                            break
                                        
                                        dest.write(chunk)
                                        bytes_copied += len(chunk)
                                        processed_size += len(chunk)
                                        batch_size += len(chunk)
                                        
                                        # Update progress based on time interval
                                        current_time = time.time()
                                        if current_time - last_update_time >= update_interval:
                                            progress = int((processed_size / total_size) * 100) if total_size > 0 else 0
                                            processed_formatted = self.format_size(processed_size)
                                            total_formatted = self.format_size(total_size)
                                            
                                            # Update progress notification
                                            self.notify("Backing up files", f"{processed_formatted} / {total_formatted} ({progress}%)")
                                            last_update_time = current_time
                                            batch_size = 0  # Reset batch size
                        
                            manifest['backed_up_files'].append(arcname)
                            
                        except Exception as e:
                            xbmc.log(f"Error backing up file {file_path}: {str(e)}", xbmc.LOGERROR)
                    
                    # Show final progress
                    progress = int((processed_size / total_size) * 100) if total_size > 0 else 0
                    processed_formatted = self.format_size(processed_size)
                    total_formatted = self.format_size(total_size)
                    self.notify("Backing up files", f"{processed_formatted} / {total_formatted} ({progress}%)")
                    
                    # Add manifest file
                    zipf.writestr('manifest.json', json.dumps(manifest, indent=4))
                
                # Show completion notification
                self.notify("Backup completed", f"Total size: {total_size_formatted}")
                
                # Get final backup size
                final_size = os.path.getsize(backup_path)
                final_size_formatted = self.format_size(final_size)
                compression_ratio = (1 - (final_size / total_size)) * 100 if total_size > 0 else 0
                size_info = f"Original: {total_size_formatted}, Compressed: {final_size_formatted} ({compression_ratio:.1f}% saved)"
                
                # Upload to remote location if needed
                if self.location_type != 0:  # Remote
                    self.notify("Uploading backup...", size_info)
                    if not self.upload_file(backup_path, f'{backup_name}.zip'):
                        self.notify("Backup failed", "Failed to upload to remote location")
                        self.disconnect_remote()
                        return False, "Failed to upload backup to remote location"
                else:  # Local
                    # Move the backup file to the final location
                    final_path = os.path.join(self.backup_dir, f'{backup_name}.zip')
                    shutil.move(backup_path, final_path)
                    self._temp_files.remove(backup_path)  # Remove from cleanup tracking
                
                # Cleanup old backups
                self.cleanup_old_backups(int(self.addon.getSetting('max_backups')))
                
                # Disconnect from remote location if needed
                if self.location_type != 0:  # Remote
                    self.disconnect_remote()
                
                # Show completion notification with persistent notification
                self.notify("Backup completed successfully", size_info, True)
                xbmc.log(f"Backup completed: {size_info}", xbmc.LOGINFO)
                
                return True, f"Backup completed successfully. {size_info}"
                
            except Exception as e:
                error_msg = f"Error creating backup: {str(e)}"
                self.notify("Backup failed", error_msg)
                if self.location_type != 0:  # Remote
                    self.disconnect_remote()
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error in create_backup: {str(e)}"
            self.notify("Backup failed", error_msg)
            if self.location_type != 0:  # Remote
                self.disconnect_remote()
            return False, error_msg
        finally:
            # Clean up resources and temporary files only after everything is done
            try:
                self.cleanup_current_session()
                self.cleanup_resources()
            except Exception as e:
                xbmc.log(f"Error during final cleanup: {str(e)}", xbmc.LOGERROR)
    
    def get_all_backups(self):
        """Get list of all available backup files"""
        self.update_backup_location()
        
        if self.location_type == 0:  # Local
            backup_pattern = os.path.join(self.backup_dir, 'backup_*.zip')
            return sorted(glob.glob(backup_pattern))
        else:  # Remote
            try:
                # Connect to remote location
                if self.location_type == 1:  # WebDAV
                    if not self.webdav:
                        self.webdav = self.connect_webdav()
                    if not self.webdav:
                        return []
                    
                    # List files from WebDAV
                    xbmc.log(f"Listing WebDAV files from: {self.webdav_url}", xbmc.LOGINFO)
                    xbmc.log(f"Using WebDAV credentials: username={self.webdav_username}, password=****************", xbmc.LOGINFO)
                    
                    try:
                        response = self.webdav.list(self.webdav_path)
                        xbmc.log(f"WebDAV PROPFIND response status: {response.status_code}", xbmc.LOGINFO)
                        xbmc.log(f"WebDAV response headers: {response.headers}", xbmc.LOGINFO)
                        xbmc.log(f"WebDAV response text: {response.text}", xbmc.LOGINFO)
                        
                        if response.status_code == 207:  # Multi-status
                            files = []
                            # Parse XML response
                            for line in response.text.split('\n'):
                                if '<D:href>' in line:
                                    href = line.strip().replace('<D:href>', '').replace('</D:href>', '')
                                    if href.endswith('.zip'):
                                        files.append(href)
                                elif '<D:displayname>' in line:
                                    name = line.strip().replace('<D:displayname>', '').replace('</D:displayname>', '')
                                    if name.endswith('.zip'):
                                        xbmc.log(f"Found backup file: {name}", xbmc.LOGINFO)
                                        files.append(name)
                            
                            # Remove duplicates and sort
                            files = sorted(list(set(files)))
                            xbmc.log(f"Final list of backup files found: {files}", xbmc.LOGINFO)
                            xbmc.log(f"Found {len(files)} backup files via WebDAV", xbmc.LOGINFO)
                            return files
                        else:
                            xbmc.log(f"WebDAV PROPFIND failed with status: {response.status_code}", xbmc.LOGERROR)
                            return []
                            
                    except Exception as e:
                        xbmc.log(f"Error listing WebDAV files: {str(e)}", xbmc.LOGERROR)
                        return []
            except Exception as e:
                xbmc.log(f"Error getting remote backups: {str(e)}", xbmc.LOGERROR)
                import traceback
                xbmc.log(f"Traceback: {traceback.format_exc()}", xbmc.LOGERROR)
                return []
    
    def cleanup_old_backups(self, max_backups=10):
        """Remove old backups, keeping only the specified number"""
        try:
            if self.location_type == 0:  # Local
                backups = self.get_all_backups()
                
                # If we have more backups than the maximum allowed
                if len(backups) > max_backups:
                    # Remove the oldest backups (they're sorted newest first)
                    for old_backup in backups[max_backups:]:
                        try:
                            os.remove(old_backup)
                            xbmc.log(f"Removed old backup: {old_backup}", xbmc.LOGINFO)
                        except Exception as e:
                            xbmc.log(f"Failed to remove old backup {old_backup}: {str(e)}", xbmc.LOGERROR)
            else:  # Remote
                # Connect to remote location
                if not self.connect_remote():
                    xbmc.log("Failed to connect to remote location for cleanup", xbmc.LOGERROR)
                    return
                
                try:
                    # Get list of backup files
                    all_files = self.list_remote_files()
                    backup_files = [f for f in all_files if f.endswith('.zip')]
                    backup_files.sort(reverse=True)  # Sort newest first
                    
                    # If we have more backups than the maximum allowed
                    if len(backup_files) > max_backups:
                        # Remove the oldest backups
                        for old_backup in backup_files[max_backups:]:
                            try:
                                self.delete_remote_file(old_backup)
                                xbmc.log(f"Removed old remote backup: {old_backup}", xbmc.LOGINFO)
                            except Exception as e:
                                xbmc.log(f"Failed to remove old remote backup {old_backup}: {str(e)}", xbmc.LOGERROR)
                finally:
                    # Disconnect from remote location
                    self.disconnect_remote()
        finally:
            # Clean up after removing old backups
            self.cleanup_resources()
    
    def mount_flash_rw(self):
        """Mount /flash in read-write mode"""
        try:
            subprocess.run(['mount', '-o', 'remount,rw', '/flash'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            xbmc.log(f"Error mounting /flash as read-write: {str(e)}", xbmc.LOGERROR)
            return False
    
    def mount_flash_ro(self):
        """Mount /flash back in read-only mode"""
        try:
            subprocess.run(['mount', '-o', 'remount,ro', '/flash'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            xbmc.log(f"Error mounting /flash as read-only: {str(e)}", xbmc.LOGERROR)
            return False
    
    def mount_userdata_rw(self):
        """Mount userdata directory in read-write mode"""
        try:
            # Get the actual mount point for userdata
            userdata_path = self.kodi_userdata
            
            # Check if userdata is already writable
            test_file = os.path.join(userdata_path, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                xbmc.log("Userdata directory is already writable", xbmc.LOGINFO)
                return True
            except (IOError, PermissionError):
                xbmc.log("Userdata directory is not writable, attempting to remount", xbmc.LOGINFO)
            
            # Find the mount point that contains userdata
            mount_info = subprocess.run(['mount'], capture_output=True, text=True, check=True)
            mount_lines = mount_info.stdout.splitlines()
            
            userdata_mount = None
            for line in mount_lines:
                parts = line.split()
                if len(parts) >= 3 and userdata_path.startswith(parts[2]):
                    userdata_mount = parts[2]
                    break
            
            if userdata_mount:
                xbmc.log(f"Mounting {userdata_mount} as read-write", xbmc.LOGINFO)
                subprocess.run(['mount', '-o', 'remount,rw', userdata_mount], check=True)
                
                # Verify it's now writable
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    xbmc.log("Verified userdata directory is now writable", xbmc.LOGINFO)
                    return True
                except (IOError, PermissionError):
                    xbmc.log("Userdata directory is still not writable after remount", xbmc.LOGERROR)
                    return False
            else:
                xbmc.log(f"Could not find mount point for userdata: {userdata_path}", xbmc.LOGERROR)
                return False
                
        except Exception as e:
            xbmc.log(f"Error mounting userdata as read-write: {str(e)}", xbmc.LOGERROR)
            return False
            
    def mount_userdata_ro(self):
        """Mount userdata directory back in read-only mode"""
        try:
            # Get the actual mount point for userdata
            userdata_path = self.kodi_userdata
            
            # Find the mount point that contains userdata
            mount_info = subprocess.run(['mount'], capture_output=True, text=True, check=True)
            mount_lines = mount_info.stdout.splitlines()
            
            userdata_mount = None
            for line in mount_lines:
                parts = line.split()
                if len(parts) >= 3 and userdata_path.startswith(parts[2]):
                    userdata_mount = parts[2]
                    break
            
            if userdata_mount:
                xbmc.log(f"Remounting {userdata_mount} as read-only", xbmc.LOGINFO)
                subprocess.run(['mount', '-o', 'remount,ro', userdata_mount], check=True)
                return True
            else:
                xbmc.log(f"Could not find mount point for userdata: {userdata_path}", xbmc.LOGERROR)
                return False
                
        except Exception as e:
            xbmc.log(f"Error mounting userdata as read-only: {str(e)}", xbmc.LOGERROR)
            return False
    
    def restore_file(self, zip_file, file_info, extract_path):
        """Restore a single file with special handling for config.txt and userdata"""
        try:
            # Handle configuration files that need /flash to be writable
            if extract_path == '/flash/config.txt' or extract_path.startswith('/flash/'):
                xbmc.log(f"Preparing to restore configuration file: {extract_path}", xbmc.LOGINFO)
                
                # Mount /flash in read-write mode
                if not self.mount_flash_rw():
                    xbmc.log("Failed to mount /flash in read-write mode", xbmc.LOGERROR)
                    return False, "Failed to mount /flash in read-write mode"
                
                xbmc.log("/flash mounted in read-write mode", xbmc.LOGINFO)
                restore_success = False
                
                try:
                    # Extract the file
                    zip_file.extract(file_info, '/')
                    xbmc.log(f"Configuration file extracted successfully: {extract_path}", xbmc.LOGINFO)
                    
                    # Ensure proper permissions
                    os.chmod(extract_path, 0o644)
                    xbmc.log(f"File permissions set to 644: {extract_path}", xbmc.LOGINFO)
                    
                    restore_success = True
                except Exception as e:
                    xbmc.log(f"Error during configuration file restore: {str(e)}", xbmc.LOGERROR)
                    raise e
                finally:
                    # Always try to remount as read-only
                    xbmc.log("Attempting to remount /flash as read-only", xbmc.LOGINFO)
                    if not self.mount_flash_ro():
                        error_msg = "Warning: Failed to remount /flash as read-only"
                        xbmc.log(error_msg, xbmc.LOGWARNING)
                        # If restore was successful but remount failed, still warn the user
                        if restore_success:
                            self.notify(error_msg)
                    else:
                        xbmc.log("/flash remounted as read-only", xbmc.LOGINFO)
                    
                    if not restore_success:
                        return False, f"Failed to restore {os.path.basename(extract_path)}"
                
                return True, None
            
            # Handle userdata files
            elif extract_path.startswith(self.kodi_userdata):
                xbmc.log(f"Preparing to restore userdata file: {extract_path}", xbmc.LOGINFO)
                
                # Mount userdata in read-write mode
                if not self.mount_userdata_rw():
                    xbmc.log("Failed to mount userdata in read-write mode", xbmc.LOGERROR)
                    return False, "Failed to mount userdata in read-write mode"
                
                xbmc.log("Userdata mounted in read-write mode", xbmc.LOGINFO)
                restore_success = False
                
                try:
                    # Ensure the directory exists
                    os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                    
                    # Extract the file
                    with zip_file.open(file_info) as source, open(extract_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    xbmc.log(f"File extracted successfully: {extract_path}", xbmc.LOGINFO)
                    
                    # Ensure proper permissions (644 for files, 755 for directories)
                    if os.path.isdir(extract_path):
                        os.chmod(extract_path, 0o755)
                    else:
                        os.chmod(extract_path, 0o644)
                    
                    restore_success = True
                except Exception as e:
                    xbmc.log(f"Error during userdata file restore: {str(e)}", xbmc.LOGERROR)
                    raise e
                finally:
                    # Always try to remount as read-only
                    xbmc.log("Attempting to remount userdata as read-only", xbmc.LOGINFO)
                    if not self.mount_userdata_ro():
                        error_msg = "Warning: Failed to remount userdata as read-only"
                        xbmc.log(error_msg, xbmc.LOGWARNING)
                        # If restore was successful but remount failed, still warn the user
                        if restore_success:
                            self.notify(error_msg)
                    else:
                        xbmc.log("Userdata remounted as read-only", xbmc.LOGINFO)
                    
                    if not restore_success:
                        return False, f"Failed to restore {os.path.basename(extract_path)}"
                
                return True, None
            
            else:
                # Normal file extraction
                # Ensure the directory exists
                os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                
                # Extract the file
                with zip_file.open(file_info) as source, open(extract_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                
                return True, None
                
        except Exception as e:
            return False, str(e)
    
    def restore_backup(self, backup_file=None):
        """Restore a backup from a file"""
        try:
            if backup_file is None:
                # Get list of available backups
                backups = self.get_all_backups()
                if not backups:
                    return False, "No backup files found"
                
                # Create backup options with detailed information
                backup_options = []
                for backup in backups:
                    try:
                        # Check if this is a remote backup placeholder
                        if isinstance(backup, str) and backup.endswith('.json'):
                            with open(backup, 'r') as f:
                                remote_info = json.load(f)
                                backup_name = remote_info.get('remote_file', 'Unknown backup')
                        else:
                            backup_name = os.path.basename(backup)
                        
                        # Get backup date and info
                        backup_date = self.get_backup_date(backup)
                        backup_items = self.get_backup_info(backup)
                        backup_size = os.path.getsize(backup) if os.path.exists(backup) else 0
                        backup_size_formatted = self.format_size(backup_size)
                        
                        # Create display string
                        display_name = f"{backup_date} - {backup_name} ({backup_size_formatted})"
                        if backup_items:
                            display_name += f" [{', '.join(backup_items)}]"
                        
                        backup_options.append((display_name, backup))
                    except Exception as e:
                        xbmc.log(f"Error processing backup {backup}: {str(e)}", xbmc.LOGERROR)
                        continue
                
                if not backup_options:
                    return False, "No valid backup files found"
                
                # Show dialog to select backup
                dialog = xbmcgui.Dialog()
                selected = dialog.select("Select backup to restore", [opt[0] for opt in backup_options])
                
                if selected == -1:  # User cancelled
                    return False, "Backup restore cancelled"
                
                backup_file = backup_options[selected][1]
            
            # Clean up any old temporary files first
            self._cleanup_old_temp_files()
            
            # Create a new temporary directory for this session
            temp_base = xbmcvfs.translatePath('special://temp')
            self.temp_dir = os.path.join(temp_base, 'libreelec_backupper', str(int(time.time())))
            os.makedirs(self.temp_dir, exist_ok=True)
            xbmc.log(f"Created temporary directory: {self.temp_dir}", xbmc.LOGINFO)
            
            # Check if this is a remote backup placeholder
            is_remote = False
            remote_info = None
            try:
                if isinstance(backup_file, str) and backup_file.endswith('.json'):
                    # Ensure the JSON file exists
                    if not os.path.exists(backup_file):
                        xbmc.log(f"Remote backup info file not found: {backup_file}", xbmc.LOGERROR)
                        return False, f"Remote backup info file not found: {backup_file}"
                        
                    with open(backup_file, 'r') as f:
                        remote_info = json.load(f)
                        is_remote = True
                        
                        # Validate remote info
                        required_fields = ['remote_file', 'remote_path', 'remote_type']
                        missing_fields = [field for field in required_fields if field not in remote_info]
                        if missing_fields:
                            xbmc.log(f"Missing required fields in remote info: {missing_fields}", xbmc.LOGERROR)
                            return False, f"Invalid remote backup information: missing {', '.join(missing_fields)}"
                            
                        # Log remote info for debugging
                        xbmc.log(f"Remote backup info: {json.dumps(remote_info, indent=2)}", xbmc.LOGINFO)
            except (json.JSONDecodeError, IOError) as e:
                xbmc.log(f"Error reading remote info: {str(e)}", xbmc.LOGERROR)
                return False, f"Invalid remote backup information: {str(e)}"
            
            if is_remote and remote_info:
                # Download the remote backup first
                xbmc.log(f"Downloading remote backup: {remote_info.get('remote_file', 'Unknown')}", xbmc.LOGINFO)
                
                # Connect to remote location
                self.remote_path = remote_info.get('remote_path', '')
                self.remote_type = remote_info.get('remote_type', 0)
                self.remote_username = remote_info.get('remote_username', '')
                self.remote_password = remote_info.get('remote_password', '')
                self.remote_port = remote_info.get('remote_port', '')
                
                # Log connection details for debugging
                xbmc.log(f"Connecting to remote location: type={self.remote_type}, path={self.remote_path}", xbmc.LOGINFO)
                
                if not self.connect_remote():
                    return False, "Failed to connect to remote location"
                
                try:
                    # Download the backup file
                    remote_file = remote_info.get('remote_file', '')
                    if not remote_file:
                        return False, "Invalid remote file information: missing remote_file"
                        
                    local_backup = os.path.join(self.temp_dir, remote_file)
                    xbmc.log(f"Downloading {remote_file} to {local_backup}", xbmc.LOGINFO)
                    
                    if not self.download_file(remote_file, local_backup):
                        return False, "Failed to download backup file"
                    
                    backup_file = local_backup
                finally:
                    self.disconnect_remote()
            
            # For remote backups, the backup_file is now downloaded to the temp directory
            if not os.path.exists(backup_file):
                return False, f"Backup file not found: {backup_file}"
            
            # Get backup size for display
            backup_size = os.path.getsize(backup_file)
            backup_size_formatted = self.format_size(backup_size)
            
            self.notify(self.addon.getLocalizedString(32103), f"Size: {backup_size_formatted}")  # Starting restore...
            
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Read manifest
                try:
                    manifest = json.loads(zipf.read('manifest.json'))
                except Exception as e:
                    return False, f"Invalid backup file (no manifest): {str(e)}"
                
                # Get list of files to restore (excluding manifest.json)
                files_to_restore = [f for f in zipf.filelist if f.filename != 'manifest.json']
                total_files = len(files_to_restore)
                current_file = 0
                
                # Restore each file
                for file_info in files_to_restore:
                    current_file += 1
                    # Ensure progress never exceeds 100%
                    progress = min(int((current_file / total_files) * 100), 100)
                    
                    try:
                        # Show progress with file info and size
                        file_size = file_info.file_size
                        file_size_formatted = self.format_size(file_size)
                        progress_info = f"{file_info.filename} ({file_size_formatted})"
                        
                        self.notify(f"{self.addon.getLocalizedString(32103)} ({progress}%)", progress_info)
                        
                        # Get the full path where this file should be restored
                        if file_info.filename.startswith('userdata/'):
                            # Handle userdata paths correctly
                            extract_path = os.path.join(self.kodi_userdata, os.path.relpath(file_info.filename, 'userdata'))
                        else:
                            # Handle all other files
                            extract_path = os.path.join('/', file_info.filename)
                        
                        # Restore the file with special handling for config.txt
                        success, error = self.restore_file(zipf, file_info, extract_path)
                        if not success:
                            raise Exception(f"Failed to restore {file_info.filename}: {error}")
                            
                    except Exception as e:
                        xbmc.log(f"Error restoring {file_info.filename}: {str(e)}", xbmc.LOGERROR)
                        self.notify(f"Error restoring", file_info.filename)
                        return False, str(e)
            
            self.notify(self.addon.getLocalizedString(32104), f"Size: {backup_size_formatted}")  # Restore completed successfully
            return True, "Backup restored successfully"
            
        except Exception as e:
            error_msg = f"Error restoring backup: {str(e)}"
            xbmc.log(error_msg, xbmc.LOGERROR)
            self.notify(self.addon.getLocalizedString(32105), str(e))  # Restore failed
            return False, error_msg
        finally:
            # Clean up temporary files after successful restore
            self.cleanup_current_session()
    
    def get_backup_date(self, backup_file):
        """Extract date from backup filename"""
        try:
            # Extract date from filename format: backup_[items]_YYYYMMDD_HHMMSS.zip
            filename = os.path.basename(backup_file)
            date_part = filename.split('_')[-2] + '_' + filename.split('_')[-1].replace('.zip', '')
            date_obj = datetime.strptime(date_part, '%Y%m%d_%H%M%S')
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return "Unknown date"
    
    def get_backup_info(self, backup_file):
        """Get information about what's included in a backup"""
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                with zipf.open('manifest.json') as f:
                    manifest = json.load(f)
                return manifest['items']
        except:
            return []

    def sanitize_filename(self, filename):
        """Sanitize filename to handle encoding issues"""
        try:
            # Replace any problematic characters with their closest ASCII equivalent
            filename = filename.encode('ascii', 'replace').decode('ascii')
            # Remove any remaining problematic characters
            return ''.join(char for char in filename if ord(char) < 128)
        except Exception:
            # If all else fails, return a safe string
            return 'invalid_filename'

    def verify_backup(self, backup_file):
        """Verify the integrity of a backup file"""
        if not os.path.exists(backup_file):
            return False, "Backup file not found"

        try:
            # Test ZIP file integrity
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # First test the ZIP file structure
                test_result = zipf.testzip()
                if test_result is not None:
                    return False, f"Corrupt ZIP file, first bad file: {test_result}"

                # Verify manifest exists and is valid JSON
                try:
                    manifest_data = zipf.read('manifest.json')
                    try:
                        manifest = json.loads(manifest_data.decode('utf-8'))
                    except UnicodeDecodeError:
                        # Try with a more lenient encoding if UTF-8 fails
                        manifest = json.loads(manifest_data.decode('latin-1'))
                except Exception as e:
                    return False, f"Invalid or missing manifest: {str(e)}"

                # Log what's being verified
                xbmc.log(f"Verifying backup: {backup_file}", xbmc.LOGINFO)
                xbmc.log(f"Manifest items: {', '.join(str(item) for item in manifest['items'])}", xbmc.LOGINFO)

                # Get list of all files in the ZIP
                try:
                    zip_files = set(self.sanitize_filename(name) for name in zipf.namelist())
                    zip_files.discard('manifest.json')  # Remove manifest from comparison
                except Exception as e:
                    return False, f"Error reading ZIP contents: {str(e)}"

                # If we have backed_up_files in manifest, use that for verification
                if 'backed_up_files' in manifest:
                    manifest_files = set(self.sanitize_filename(name) for name in manifest['backed_up_files'])
                    
                    # Compare files in ZIP vs manifest (using sanitized names)
                    missing_files = manifest_files - zip_files
                    extra_files = zip_files - manifest_files

                    if missing_files:
                        xbmc.log(f"Missing files in backup: {', '.join(sorted(missing_files))}", xbmc.LOGERROR)
                        return False, f"Missing files in backup: {', '.join(sorted(missing_files)[:5])}..."

                    if extra_files:
                        # Just log extra files but don't fail verification
                        xbmc.log(f"Extra files in backup (not in manifest): {', '.join(sorted(extra_files))}", xbmc.LOGWARNING)

                xbmc.log("Backup verification completed successfully", xbmc.LOGINFO)
                return True, "Backup verified successfully"

        except Exception as e:
            error_msg = f"Error verifying backup: {str(e)}"
            xbmc.log(error_msg, xbmc.LOGERROR)
            return False, error_msg
            
        finally:
            # Clean up after verification
            try:
                if 'temp_dir' in locals():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                xbmc.log(f"Error during cleanup: {str(e)}", xbmc.LOGERROR) 