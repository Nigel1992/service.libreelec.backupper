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

class BackupManager:
    """Utility class to manage config backups"""
    
    def __init__(self, addon=None):
        self.addon = addon or xbmcaddon.Addon()
        self.update_backup_location()
    
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
    
    def notify(self, message, detailed_info=""):
        """Show notification if enabled"""
        if self.addon.getSettingBool('show_notifications'):
            if self.addon.getSettingBool('detailed_notifications') and detailed_info:
                message = f"{message} - {detailed_info}"
            xbmc.executebuiltin(f'Notification({self.addon.getAddonInfo("name")}, {message}, 3000)')
    
    def get_backup_paths(self):
        """Get paths for all backup items based on settings"""
        paths = {}
        
        # Config.txt
        if self.addon.getSettingBool('backup_config'):
            paths['config'] = '/flash/config.txt'
        
        # Addons
        if self.addon.getSettingBool('backup_addons'):
            paths['addons'] = os.path.join(self.kodi_home, 'addons')
        
        # Addon User Data
        if self.addon.getSettingBool('backup_userdata'):
            paths['addon_data'] = os.path.join(self.kodi_userdata, 'addon_data')
        
        # Sources
        if self.addon.getSettingBool('backup_sources'):
            paths['sources'] = os.path.join(self.kodi_userdata, 'sources.xml')
        
        # Profiles
        if self.addon.getSettingBool('backup_profiles'):
            paths['profiles'] = os.path.join(self.kodi_userdata, 'profiles.xml')
            paths['profiles_dir'] = os.path.join(self.kodi_userdata, 'profiles')
        
        # Configuration Files
        if self.addon.getSettingBool('backup_configs'):
            paths['guisettings'] = os.path.join(self.kodi_userdata, 'guisettings.xml')
            paths['advancedsettings'] = os.path.join(self.kodi_userdata, 'advancedsettings.xml')
            paths['keyboard'] = os.path.join(self.kodi_userdata, 'keyboard.xml')
            paths['keymaps'] = os.path.join(self.kodi_userdata, 'keymaps')
        
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
            paths['skin_settings'] = os.path.join(self.kodi_userdata, 'addon_data', 'skin.*')
        
        return paths
    
    def create_backup(self):
        """Create a backup of all selected items"""
        # Update backup location in case it changed
        self.update_backup_location()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'kodi_backup_{timestamp}'
        zip_path = os.path.join(self.backup_dir, f'{backup_name}.zip')
        
        try:
            # Get paths to backup
            paths = self.get_backup_paths()
            total_items = len(paths)
            current_item = 0
            
            self.notify(self.addon.getLocalizedString(32100))  # Starting backup...
            
            # Create manifest
            manifest = {
                'timestamp': timestamp,
                'items': list(paths.keys()),
                'paths': paths
            }
            
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add manifest
                zipf.writestr('manifest.json', json.dumps(manifest, indent=4))
                
                # Backup each item
                for item_name, path in paths.items():
                    current_item += 1
                    progress = int((current_item / total_items) * 100)
                    
                    try:
                        self.notify(f"{self.addon.getLocalizedString(32100)} ({progress}%)", item_name)
                        
                        if os.path.exists(path):
                            if os.path.isfile(path):
                                # For single files, maintain the full path structure
                                arcname = os.path.relpath(path, '/')
                                zipf.write(path, arcname)
                            else:
                                # For directories, walk through and maintain structure
                                for root, _, files in os.walk(path):
                                    for file in files:
                                        file_path = os.path.join(root, file)
                                        # Maintain full path structure by using relpath from root
                                        arcname = os.path.relpath(file_path, '/')
                                        zipf.write(file_path, arcname)
                    except Exception as e:
                        xbmc.log(f"Error backing up {item_name}: {str(e)}", xbmc.LOGERROR)
                        self.notify(f"Error backing up", item_name)
            
            # Update last backup time
            self.addon.setSetting('last_backup', datetime.now().strftime('%Y-%m-%d %H:%M'))
            self.update_schedule_info()
            
            # Clean up old backups
            self.cleanup_old_backups(int(self.addon.getSetting('max_backups')))
            
            self.notify(self.addon.getLocalizedString(32101))  # Backup completed successfully
            return True, "Backup created successfully"
        except Exception as e:
            error_msg = f"Error creating backup: {str(e)}"
            self.notify(self.addon.getLocalizedString(32102), str(e))  # Backup failed
            return False, error_msg
    
    def get_all_backups(self):
        """Get a list of all backup files"""
        # Update backup location in case it changed
        self.update_backup_location()
        backup_pattern = os.path.join(self.backup_dir, 'kodi_backup_*.zip')
        return sorted(glob.glob(backup_pattern), reverse=True)
    
    def cleanup_old_backups(self, max_backups=10):
        """Remove old backups, keeping only the specified number"""
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
    
    def restore_file(self, zip_file, file_info, extract_path):
        """Restore a single file with special handling for config.txt"""
        try:
            if extract_path == '/flash/config.txt':
                # Mount /flash in read-write mode
                if not self.mount_flash_rw():
                    return False, "Failed to mount /flash in read-write mode"
                
                try:
                    # Extract config.txt
                    zip_file.extract(file_info, '/')
                    
                    # Ensure proper permissions
                    os.chmod('/flash/config.txt', 0o644)
                    
                    # Mount /flash back in read-only mode
                    if not self.mount_flash_ro():
                        xbmc.log("Warning: Failed to remount /flash as read-only", xbmc.LOGWARNING)
                    
                    return True, None
                except Exception as e:
                    # Try to remount as read-only even if we failed
                    self.mount_flash_ro()
                    raise e
            else:
                # Normal file extraction
                zip_file.extract(file_info, '/')
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
                
                total_items = len(manifest['items'])
                current_item = 0
                
                # Restore each item
                for file_info in zipf.filelist:
                    if file_info.filename == 'manifest.json':
                        continue
                    
                    current_item += 1
                    progress = int((current_item / total_items) * 100)
                    
                    try:
                        self.notify(f"{self.addon.getLocalizedString(32103)} ({progress}%)", file_info.filename)
                        
                        # Get the full path where this file should be restored
                        extract_path = os.path.join('/', file_info.filename)
                        
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                        
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
            # Extract date from filename format: kodi_backup_YYYYMMDD_HHMMSS.zip
            filename = os.path.basename(backup_file)
            date_str = filename.replace('kodi_backup_', '').replace('.zip', '')
            date_obj = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
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