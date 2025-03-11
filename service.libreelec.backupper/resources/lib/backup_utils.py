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

class BackupManager:
    """Utility class to manage config backups"""
    
    def __init__(self, addon=None):
        self.addon = addon or xbmcaddon.Addon()
        self.update_backup_location()
        self._temp_files = set()  # Track temporary files
    
    def update_backup_location(self):
        """Update backup location from settings"""
        # Get backup location from settings
        self.backup_dir = self.addon.getSetting('backup_location')
        if not self.backup_dir:
            self.backup_dir = "/storage/backup"  # Default location
        
        # Define paths for various Kodi directories
        self.kodi_home = xbmcvfs.translatePath('special://home')
        self.kodi_userdata = xbmcvfs.translatePath('special://userdata')
        
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
            xbmc.executebuiltin(f'Notification({self.addon.getAddonInfo("name")}, {message}, {timeout})')
    
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
        """Clean up any temporary resources and force garbage collection"""
        try:
            # Clean up any temporary files we created
            for temp_file in self._temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    xbmc.log(f"Error removing temp file {temp_file}: {str(e)}", xbmc.LOGWARNING)
            
            self._temp_files.clear()
            
            # Force garbage collection
            gc.collect()
            
            # Small sleep to allow system to stabilize
            xbmc.sleep(500)
            
        except Exception as e:
            xbmc.log(f"Error during cleanup: {str(e)}", xbmc.LOGWARNING)

    def create_backup(self):
        """Create a backup of all selected items"""
        try:
            # Update backup location in case it changed
            self.update_backup_location()
            
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
            zip_path = os.path.join(self.backup_dir, f'{backup_name}.zip')
            
            try:
                total_items = len(paths)
                current_item = 0
                
                # Don't create empty backups
                if total_items == 0:
                    return False, "No items selected for backup"
                
                # Check available space
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
                    stat = os.statvfs(self.backup_dir)
                    available_space = stat.f_frsize * stat.f_bavail
                    
                    # Check if we have enough space (total size + 10% buffer)
                    if total_size * 1.1 > available_space:
                        return False, f"Not enough space for backup. Need {total_size/1024/1024:.1f}MB but only {available_space/1024/1024:.1f}MB available"
                except Exception as e:
                    xbmc.log(f"Error checking space: {str(e)}", xbmc.LOGWARNING)
                
                self.notify(self.addon.getLocalizedString(32100), "", True)  # Starting backup... (persistent)
                
                # Track what files we actually backed up
                backed_up_files = set()
                
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
                            self.notify(f"{self.addon.getLocalizedString(32100)} ({progress}%)", item_name, True)
                            
                            if os.path.exists(path):
                                if os.path.isfile(path):
                                    # For single files, maintain the full path structure
                                    try:
                                        if not os.path.islink(path):  # Skip symbolic links
                                            arcname = self.sanitize_filename(os.path.relpath(path, '/'))
                                            zipf.write(path, arcname)
                                            backed_up_files.add(arcname)
                                            xbmc.log(f"Successfully backed up file: {path}", xbmc.LOGINFO)
                                    except Exception as e:
                                        xbmc.log(f"Failed to backup file {path}: {str(e)}", xbmc.LOGERROR)
                                        continue
                                else:
                                    # For directories, walk through and maintain structure
                                    try:
                                        for root, _, files in os.walk(path):
                                            for file in files:
                                                file_path = os.path.join(root, file)
                                                try:
                                                    if os.path.islink(file_path):  # Skip symbolic links
                                                        continue
                                                        
                                                    # Use a more reliable path handling for special paths
                                                    if 'userdata' in root or 'addon_data' in root:
                                                        # Keep the userdata/addon_data structure
                                                        arcname = self.sanitize_filename(os.path.join('userdata', os.path.relpath(file_path, self.kodi_userdata)))
                                                    else:
                                                        arcname = self.sanitize_filename(os.path.relpath(file_path, '/'))
                                                    
                                                    # Skip problematic files
                                                    if any(x in file_path.lower() for x in ['.sock', '.socket', '.lock', '.pid']):
                                                        continue
                                                    
                                                    try:
                                                        # Try to open file first to check if readable
                                                        with open(file_path, 'rb') as f:
                                                            zipf.writestr(arcname, f.read())
                                                            backed_up_files.add(arcname)
                                                        xbmc.log(f"Successfully backed up: {file_path}", xbmc.LOGDEBUG)
                                                    except (IOError, OSError) as e:
                                                        xbmc.log(f"Cannot read file {file_path}: {str(e)}", xbmc.LOGWARNING)
                                                        continue
                                                except Exception as e:
                                                    xbmc.log(f"Failed to backup {file_path}: {str(e)}", xbmc.LOGERROR)
                                                    continue
                                    except Exception as e:
                                        xbmc.log(f"Error walking directory {path}: {str(e)}", xbmc.LOGERROR)
                                        continue
                            else:
                                xbmc.log(f"Path does not exist: {path}", xbmc.LOGWARNING)
                        except Exception as e:
                            xbmc.log(f"Error backing up {item_name}: {str(e)}", xbmc.LOGERROR)
                            self.notify(f"Error backing up", item_name)
                            continue
                    
                    # Update manifest with actual backed up files
                    manifest['backed_up_files'] = list(backed_up_files)
                    zipf.writestr('manifest.json', json.dumps(manifest, indent=4))
                
                # Update last backup time
                self.addon.setSetting('last_backup', datetime.now().strftime('%Y-%m-%d %H:%M'))
                self.update_schedule_info()
                
                # Clean up old backups
                self.cleanup_old_backups(int(self.addon.getSetting('max_backups')))
                
                # Verify backup if enabled
                if self.addon.getSettingBool('verify_backup'):
                    self.notify("Verifying Backup", "Starting verification process...", True)
                    xbmc.sleep(2000)  # Wait 2 seconds before starting verification
                    
                    success, message = self.verify_backup(zip_path)
                    if not success:
                        raise Exception(f"Backup verification failed: {message}")
                    
                    xbmc.sleep(2000)  # Wait 2 seconds before showing success
                    self.notify("Verification Complete", "Backup verified successfully", True)
                    xbmc.sleep(1000)  # Wait 1 second before final backup success message
                    
                    self.notify(self.addon.getLocalizedString(32101))  # Backup completed successfully (non-persistent)
                else:
                    self.notify(self.addon.getLocalizedString(32101))  # Backup completed successfully (non-persistent)
                
                return True, "Backup created successfully"
            except Exception as e:
                error_msg = f"Error creating backup: {str(e)}"
                self.notify(self.addon.getLocalizedString(32102), str(e))  # Backup failed (non-persistent)
                # Try to clean up failed backup
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except:
                        pass
                return False, error_msg
        finally:
            # Always clean up resources, even if backup fails
            self.cleanup_resources()
    
    def get_all_backups(self):
        """Get a list of all backup files"""
        # Update backup location in case it changed
        self.update_backup_location()
        backup_pattern = os.path.join(self.backup_dir, 'backup_*.zip')
        return sorted(glob.glob(backup_pattern), reverse=True)
    
    def cleanup_old_backups(self, max_backups=10):
        """Remove old backups, keeping only the specified number"""
        try:
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
        if not os.path.exists(backup_file):
            return False, "Backup file not found"
        
        try:
            self.notify(self.addon.getLocalizedString(32103))  # Starting restore...
            
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
                        self.notify(f"{self.addon.getLocalizedString(32103)} ({progress}%)", file_info.filename)
                        
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
            
            self.notify(self.addon.getLocalizedString(32104))  # Restore completed successfully
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