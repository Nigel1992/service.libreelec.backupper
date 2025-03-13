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
    
    def update_backup_location(self):
        """Update backup location from settings"""
        # Get backup location type from settings
        self.location_type = int(self.addon.getSetting('backup_location_type') or "0")
        
        # Define paths for various Kodi directories
        self.kodi_home = xbmcvfs.translatePath('special://home')
        self.kodi_userdata = xbmcvfs.translatePath('special://userdata')
        
        # Handle local backup location
        if self.location_type == 0:  # Local
            self.backup_dir = self.addon.getSetting('backup_location')
            if not self.backup_dir:
                self.backup_dir = "/storage/backup"  # Default location
            
            # Ensure backup directory exists
            if not os.path.exists(self.backup_dir):
                try:
                    os.makedirs(self.backup_dir)
                except Exception as e:
                    xbmc.log(f"Error creating backup directory: {str(e)}", xbmc.LOGERROR)
                    # Fall back to addon profile if custom location can't be created
                    self.backup_dir = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
                    if not os.path.exists(self.backup_dir):
                        os.makedirs(self.backup_dir)
                    self.addon.setSetting('backup_location', self.backup_dir)
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
            self.backup_dir = xbmcvfs.translatePath(os.path.join(self.addon.getAddonInfo('profile'), 'temp'))
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
    
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
                # Construct WebDAV URL
                host = self.remote_path.split('/')[0]
                protocol = "https" if self.remote_port == 443 else "http"
                
                # Build base URL
                if self.remote_port == 80 or self.remote_port == 443:
                    base_url = f"{protocol}://{host}"
                else:
                    base_url = f"{protocol}://{host}:{self.remote_port}"
                
                # Add path if provided
                if '/' in self.remote_path:
                    path = '/'.join(self.remote_path.split('/')[1:])
                    if path:
                        if not path.startswith('/'):
                            path = '/' + path
                        if not path.endswith('/'):
                            path = path + '/'
                        base_url = f"{base_url}{path}"
                
                # Get or create WebDAV session
                session = self._create_webdav_session()
                
                # Test connection with retry logic
                try:
                    response = session.request('PROPFIND', base_url, headers={'Depth': '1'})
                    if response.status_code in [207, 200]:  # 207 is Multi-Status response
                        self.remote_connection = {
                            'session': session,
                            'base_url': base_url
                        }
                        return True
                except requests.exceptions.RetryError:
                    xbmc.log("WebDAV connection failed after retries", xbmc.LOGERROR)
                    return False
                except Exception as e:
                    xbmc.log(f"WebDAV connection error: {str(e)}", xbmc.LOGERROR)
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
                _, files = xbmcvfs.listdir(self.remote_connection)
                return files
                
            elif self.remote_type == 1:  # NFS
                # List files in the mounted directory
                return [f for f in os.listdir(self.remote_connection) if os.path.isfile(os.path.join(self.remote_connection, f))]
                
            elif self.remote_type == 2:  # FTP
                # List files via FTP
                return self.remote_connection.nlst()
                
            elif self.remote_type == 3:  # SFTP
                # List files via SFTP
                return [f for f in self.remote_connection.listdir() if not self.is_remote_dir(f)]
                
            elif self.remote_type == 4:  # WebDAV
                # List files via WebDAV
                response = self.remote_connection['session'].request(
                    'PROPFIND', 
                    self.remote_connection['base_url'], 
                    headers={'Depth': '1'}
                )
                
                if response.status_code != 207:  # Multi-Status response
                    return []
                
                # Parse XML response to get file names
                # This is a simplified approach - WebDAV responses can be complex
                files = []
                for line in response.text.splitlines():
                    if '<d:href>' in line and '</d:href>' in line:
                        href = line.split('<d:href>')[1].split('</d:href>')[0]
                        # Extract filename from the href
                        if href.endswith('/'):
                            continue  # Skip directories
                        filename = href.rstrip('/').split('/')[-1]
                        if filename and not filename.startswith('.'):
                            files.append(urllib.parse.unquote(filename))
                
                return files
                
        except Exception as e:
            xbmc.log(f"Error listing files in remote location: {str(e)}", xbmc.LOGERROR)
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
        if not self.addon.getSettingBool('enable_schedule'):
            return None
        
        interval = int(self.addon.getSetting('backup_interval'))
        if interval == 0:  # Disabled
            return None
        
        now = datetime.now()
        backup_time = datetime.strptime(self.addon.getSetting('backup_time'), '%H:%M').time()
        
        if interval == 1:  # Hourly
            next_backup = now.replace(minute=backup_time.minute)
            if next_backup <= now:
                next_backup += timedelta(hours=1)
        elif interval == 2:  # Daily
            next_backup = now.replace(hour=backup_time.hour, minute=backup_time.minute)
            if next_backup <= now:
                next_backup += timedelta(days=1)
        else:  # Weekly
            target_day = int(self.addon.getSetting('backup_day'))
            days_ahead = target_day - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_backup = now.replace(hour=backup_time.hour, minute=backup_time.minute)
            next_backup += timedelta(days=days_ahead)
        
        return next_backup
    
    def update_schedule_info(self):
        """Update the last and next backup time in settings"""
        next_backup = self.get_next_backup_time()
        if next_backup:
            self.addon.setSetting('next_backup', next_backup.strftime('%Y-%m-%d %H:%M'))
        else:
            self.addon.setSetting('next_backup', '')
    
    def should_run_backup(self):
        """Check if it's time to run a scheduled backup"""
        if not self.addon.getSettingBool('enable_schedule'):
            return False
        
        next_backup = self.get_next_backup_time()
        if not next_backup:
            return False
        
        return datetime.now() >= next_backup
    
    def notify(self, message, detailed_info="", persistent=False):
        """Show notification if enabled"""
        if self.addon.getSettingBool('show_notifications'):
            if self.addon.getSettingBool('detailed_notifications') and detailed_info:
                message = f"{message} - {detailed_info}"
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
        
        # Configuration Files
        if self.addon.getSettingBool('backup_configs'):
            paths['config'] = '/flash/config.txt'
            paths['guisettings'] = os.path.join(self.kodi_userdata, 'guisettings.xml')
            paths['advancedsettings'] = os.path.join(self.kodi_userdata, 'advancedsettings.xml')
            paths['keyboard'] = os.path.join(self.kodi_userdata, 'keyboard.xml')
            paths['keymaps'] = os.path.join(self.kodi_userdata, 'keymaps')
        
        # Sources
        if self.addon.getSettingBool('backup_sources'):
            paths['sources'] = os.path.join(self.kodi_userdata, 'sources.xml')
        
        # Addons
        if self.addon.getSettingBool('backup_addons'):
            paths['addons'] = os.path.join(self.kodi_home, 'addons')
        
        # Repositories
        if self.addon.getSettingBool('backup_repositories'):
            paths.update(self.get_repository_paths())
        
        # Addon User Data and Settings
        if self.addon.getSettingBool('backup_userdata'):
            paths['addon_data'] = os.path.join(self.kodi_userdata, 'addon_data')
        
        # Profiles
        if self.addon.getSettingBool('backup_profiles'):
            paths['profiles'] = os.path.join(self.kodi_userdata, 'profiles.xml')
            paths['profiles_dir'] = os.path.join(self.kodi_userdata, 'profiles')
        
        # Game Saves
        if self.addon.getSettingBool('backup_gamesaves'):
            paths['gamesaves'] = os.path.join(self.kodi_userdata, 'addon_data', 'game.saves')
        
        # Playlists
        if self.addon.getSettingBool('backup_playlists'):
            paths['playlists'] = os.path.join(self.kodi_userdata, 'playlists')
        
        # Thumbnails/Fanart
        if self.addon.getSettingBool('backup_thumbnails'):
            paths['thumbnails'] = os.path.join(self.kodi_userdata, 'Thumbnails')
            paths['fanart'] = os.path.join(self.kodi_home, 'addons', 'fanart')
        
        # Skins
        if self.addon.getSettingBool('backup_skins'):
            paths['skins'] = os.path.join(self.kodi_home, 'addons', 'skin.*')
            # Only include skin settings if addon_data is not being backed up
            if not self.addon.getSettingBool('backup_userdata'):
                paths['skin_settings'] = os.path.join(self.kodi_userdata, 'addon_data', 'skin.*')
        
        return paths
    
    def cleanup_resources(self):
        """Clean up resources before addon shutdown"""
        try:
            # Close WebDAV session if it exists
            if self._webdav_session is not None:
                self._webdav_session.close()
                self._webdav_session = None
                
            # Disconnect remote connection
            self.disconnect_remote()
            
            # Clean up temporary files
            for temp_file in self._temp_files:
                if os.path.exists(temp_file):
                    try:
                        if os.path.isdir(temp_file):
                            shutil.rmtree(temp_file)
                        else:
                            os.remove(temp_file)
                    except Exception as e:
                        xbmc.log(f"Error removing temp file {temp_file}: {str(e)}", xbmc.LOGWARNING)
            
            self._temp_files.clear()
            
            # Force garbage collection
            gc.collect()
            
        except Exception as e:
            xbmc.log(f"Error during resource cleanup: {str(e)}", xbmc.LOGERROR)

    def create_backup(self):
        """Create a backup of all selected items"""
        try:
            # Update backup location in case it changed
            self.update_backup_location()
            
            # Connect to remote location if needed
            if self.location_type != 0:  # Remote
                if not self.connect_remote():
                    return False, "Failed to connect to remote location"
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Get paths to backup
            paths = self.get_backup_paths()
            
            # Create backup name with included items
            backup_items = []
            if self.addon.getSettingBool('backup_configs'):
                backup_items.append('conf')
            if self.addon.getSettingBool('backup_addons'):
                backup_items.append('addons')
            if self.addon.getSettingBool('backup_repositories'):
                backup_items.append('repos')
            if self.addon.getSettingBool('backup_userdata'):
                backup_items.append('data')
            if self.addon.getSettingBool('backup_sources'):
                backup_items.append('src')
            
            # Add items to backup name
            items_str = '-'.join(backup_items) if backup_items else 'empty'
            backup_name = f'backup_{items_str}_{timestamp}'
            
            # For remote locations, create a temporary local file first
            if self.location_type != 0:  # Remote
                temp_dir = xbmcvfs.translatePath(os.path.join(self.addon.getAddonInfo('profile'), 'temp'))
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                zip_path = os.path.join(temp_dir, f'{backup_name}.zip')
                self._temp_files.add(zip_path)  # Track for cleanup
            else:
                zip_path = os.path.join(self.backup_dir, f'{backup_name}.zip')
            
            try:
                total_items = len(paths)
                current_item = 0
                
                # Don't create empty backups
                if total_items == 0:
                    if self.location_type != 0:  # Remote
                        self.disconnect_remote()
                    return False, "No items selected for backup"
                
                # Check available space (only for local backups or temp directory)
                try:
                    total_size = 0
                    for _, path in paths.items():
                        if os.path.exists(path):
                            if os.path.isfile(path):
                                total_size += os.path.getsize(path)
                            else:
                                for root, _, files in os.walk(path):
                                    for file in files:
                                        try:
                                            total_size += os.path.getsize(os.path.join(root, file))
                                        except OSError:
                                            continue
                
                    # Get available space in backup directory
                    check_dir = os.path.dirname(zip_path)
                    stat = os.statvfs(check_dir)
                    available_space = stat.f_frsize * stat.f_bavail
                    
                    # Format sizes for display
                    total_size_formatted = self.format_size(total_size)
                    available_space_formatted = self.format_size(available_space)
                    
                    # Check if we have enough space (total size + 10% buffer)
                    if total_size * 1.1 > available_space:
                        if self.location_type != 0:  # Remote
                            self.disconnect_remote()
                        return False, f"Not enough space for backup. Need {total_size_formatted} but only {available_space_formatted} available"
                    
                    # Show space information in notification
                    space_info = f"Size: {total_size_formatted} / Available: {available_space_formatted}"
                    self.notify(self.addon.getLocalizedString(32100), space_info, True)  # Starting backup... (persistent)
                    
                except Exception as e:
                    xbmc.log(f"Error checking space: {str(e)}", xbmc.LOGWARNING)
                    # Still show a notification, but without space info
                    self.notify(self.addon.getLocalizedString(32100), "", True)  # Starting backup... (persistent)
                
                # Track what files we actually backed up
                backed_up_files = set()
                current_size = 0
                
                # Create manifest
                manifest = {
                    'timestamp': timestamp,
                    'items': list(paths.keys()),
                    'paths': paths,
                    'backed_up_files': []  # Will be populated during backup
                }
                
                # Create zip file with UTF-8 encoding error handling
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
                    # Backup each item
                    for item_name, path in paths.items():
                        current_item += 1
                        progress = int((current_item / total_items) * 100)
                        
                        try:
                            # Show progress with item name and current/total size
                            progress_info = f"{item_name} ({self.format_size(current_size)}/{total_size_formatted})"
                            self.notify(f"{self.addon.getLocalizedString(32100)} ({progress}%)", progress_info, True)
                            
                            if os.path.exists(path):
                                if os.path.isfile(path):
                                    # For single files, maintain the full path structure
                                    try:
                                        if not os.path.islink(path):  # Skip symbolic links
                                            arcname = self.sanitize_filename(os.path.relpath(path, '/'))
                                            zipf.write(path, arcname)
                                            file_size = os.path.getsize(path)
                                            current_size += file_size
                                            backed_up_files.add(arcname)
                                            manifest['backed_up_files'].append(arcname)
                                    except Exception as e:
                                        xbmc.log(f"Error backing up file {path}: {str(e)}", xbmc.LOGWARNING)
                                else:
                                    # For directories, walk through and add each file
                                    for root, _, files in os.walk(path):
                                        for file in files:
                                            try:
                                                file_path = os.path.join(root, file)
                                                if not os.path.islink(file_path):  # Skip symbolic links
                                                    arcname = self.sanitize_filename(os.path.relpath(file_path, '/'))
                                                    zipf.write(file_path, arcname)
                                                    file_size = os.path.getsize(file_path)
                                                    current_size += file_size
                                                    backed_up_files.add(arcname)
                                                    manifest['backed_up_files'].append(arcname)
                                            except Exception as e:
                                                xbmc.log(f"Error backing up file {file_path}: {str(e)}", xbmc.LOGWARNING)
                        except Exception as e:
                            xbmc.log(f"Error backing up item {item_name}: {str(e)}", xbmc.LOGWARNING)
                    
                    # Add manifest file
                    zipf.writestr('manifest.json', json.dumps(manifest, indent=4))
                
                # Show final backup size
                final_size = os.path.getsize(zip_path)
                final_size_formatted = self.format_size(final_size)
                
                # Upload to remote location if needed
                if self.location_type != 0:  # Remote
                    self.notify(f"{self.addon.getLocalizedString(32100)} (Uploading...)", f"Size: {final_size_formatted}", True)
                    if not self.upload_file(zip_path, f'{backup_name}.zip'):
                        self.disconnect_remote()
                        return False, "Failed to upload backup to remote location"
                
                # Cleanup old backups
                self.cleanup_old_backups(int(self.addon.getSetting('max_backups')))
                
                # Update last backup time
                self.addon.setSetting('last_backup', datetime.now().strftime('%Y-%m-%d %H:%M'))
                self.update_schedule_info()
                
                # Disconnect from remote location if needed
                if self.location_type != 0:  # Remote
                    self.disconnect_remote()
                
                self.notify(self.addon.getLocalizedString(32101), f"Size: {final_size_formatted}")  # Backup completed successfully
                return True, f"Backup completed successfully. Size: {final_size_formatted}"
                
            except Exception as e:
                xbmc.log(f"Error creating backup: {str(e)}", xbmc.LOGERROR)
                if self.location_type != 0:  # Remote
                    self.disconnect_remote()
                return False, f"Error creating backup: {str(e)}"
                
        except Exception as e:
            xbmc.log(f"Error in backup process: {str(e)}", xbmc.LOGERROR)
            if self.location_type != 0:  # Remote
                self.disconnect_remote()
            return False, f"Error in backup process: {str(e)}"
        finally:
            # Clean up resources
            self.cleanup_resources()
    
    def get_all_backups(self):
        """Get a list of all backup files"""
        # Update backup location in case it changed
        self.update_backup_location()
        
        if self.location_type == 0:  # Local
            backup_pattern = os.path.join(self.backup_dir, 'backup_*.zip')
            return sorted(glob.glob(backup_pattern), reverse=True)
        else:  # Remote
            try:
                # Connect to remote location
                if not self.connect_remote():
                    xbmc.log("Failed to connect to remote location", xbmc.LOGERROR)
                    return []
                
                # Get list of backup files
                try:
                    all_files = self.list_remote_files()
                    backup_files = [f for f in all_files if f.startswith('backup_') and f.endswith('.zip')]
                    
                    # For remote files, we need to create full paths
                    backup_paths = []
                    for backup_file in backup_files:
                        # Download to temp directory for viewing
                        temp_path = os.path.join(self.backup_dir, backup_file)
                        if not os.path.exists(temp_path):
                            self.download_file(backup_file, temp_path)
                            self._temp_files.add(temp_path)  # Track for cleanup
                        backup_paths.append(temp_path)
                    
                    return sorted(backup_paths, reverse=True)
                finally:
                    # Disconnect from remote location
                    self.disconnect_remote()
            except Exception as e:
                xbmc.log(f"Error getting remote backups: {str(e)}", xbmc.LOGERROR)
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
                    backup_files = [f for f in all_files if f.startswith('backup_') and f.endswith('.zip')]
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
            # Handle config.txt specially
            if extract_path == '/flash/config.txt':
                xbmc.log("Preparing to restore config.txt...", xbmc.LOGINFO)
                
                # Mount /flash in read-write mode
                if not self.mount_flash_rw():
                    xbmc.log("Failed to mount /flash in read-write mode", xbmc.LOGERROR)
                    return False, "Failed to mount /flash in read-write mode"
                
                xbmc.log("/flash mounted in read-write mode", xbmc.LOGINFO)
                restore_success = False
                
                try:
                    # Extract config.txt
                    zip_file.extract(file_info, '/')
                    xbmc.log("config.txt extracted successfully", xbmc.LOGINFO)
                    
                    # Ensure proper permissions
                    os.chmod('/flash/config.txt', 0o644)
                    xbmc.log("config.txt permissions set to 644", xbmc.LOGINFO)
                    
                    restore_success = True
                except Exception as e:
                    xbmc.log(f"Error during config.txt restore: {str(e)}", xbmc.LOGERROR)
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
                        return False, "Failed to restore config.txt"
                
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
    
    def restore_backup(self, backup_file):
        """Restore a backup"""
        # For remote backups, the backup_file is already downloaded to the temp directory
        # by the get_all_backups method, so we can just use it directly
        if not os.path.exists(backup_file):
            return False, "Backup file not found"
        
        try:
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
            self.notify(self.addon.getLocalizedString(32105), str(e))  # Restore failed
            return False, error_msg
    
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
            self.cleanup_resources() 