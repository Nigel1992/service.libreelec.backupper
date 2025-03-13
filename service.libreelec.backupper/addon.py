#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
from resources.lib.backup_utils import BackupManager
from resources.lib.remote_browser import RemoteBrowser

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ADDON_ICON = ADDON.getAddonInfo('icon')

# Log function
def log(message, level=xbmc.LOGINFO):
    xbmc.log(f'{ADDON_ID}: {message}', level)

class BackupBrowser:
    """GUI for browsing and restoring backups"""
    
    def __init__(self):
        self.backup_utils = BackupManager()
    
    def show_backups(self):
        """Display a list of available backups"""
        backups = self.backup_utils.get_all_backups()
        
        if not backups:
            xbmcgui.Dialog().ok(ADDON_NAME, "No backups found")
            return
        
        backup_names = [os.path.basename(b) for b in backups]
        selected = xbmcgui.Dialog().select("Select backup to restore", backup_names)
        
        if selected >= 0:
            if xbmcgui.Dialog().yesno(ADDON_NAME, "Are you sure you want to restore this backup?"):
                success, message = self.backup_utils.restore_backup(backups[selected])
                if not success:
                    xbmcgui.Dialog().ok(ADDON_NAME, f"Failed to restore backup: {message}")

def show_notification(message, time=5000, icon=ADDON_ICON):
    """Show a notification to the user"""
    xbmcgui.Dialog().notification(ADDON_NAME, message, icon, time)

def show_main_menu():
    """Show the main menu dialog"""
    options = [
        ADDON.getLocalizedString(32001),  # Create Backup
        ADDON.getLocalizedString(32002),  # Restore Backup
        ADDON.getLocalizedString(32003),  # Browse Remote Location
        ADDON.getLocalizedString(32004),  # Settings
    ]
    
    dialog = xbmcgui.Dialog()
    choice = dialog.select(ADDON_NAME, options)
    
    if choice == 0:  # Create Backup
        backup_manager = BackupManager(ADDON)
        success, message = backup_manager.create_backup()
        show_notification(message)
        
    elif choice == 1:  # Restore Backup
        backup_manager = BackupBrowser()
        success, message = backup_manager.show_backups()
        if success:
            show_notification(message)
            # Ask user if they want to restart Kodi
            if dialog.yesno(ADDON_NAME, ADDON.getLocalizedString(32100)):  # Restart Kodi?
                xbmc.executebuiltin('RestartApp')
        else:
            show_notification(message)
            
    elif choice == 2:  # Browse Remote Location
        if ADDON.getSettingInt('backup_location_type') != 0:  # Only if remote location is selected
            remote_browser = RemoteBrowser(ADDON)
            remote_browser.browse()
        else:
            show_notification(ADDON.getLocalizedString(32101))  # Please configure a remote location first
            
    elif choice == 3:  # Settings
        ADDON.openSettings()

def run():
    """Main entry point"""
    # Check if any arguments were passed
    if len(sys.argv) > 1:
        # Handle command line arguments
        if sys.argv[1] == 'backup':
            backup_manager = BackupManager(ADDON)
            success, message = backup_manager.create_backup()
            show_notification(message)
            
        elif sys.argv[1] == 'restore':
            backup_manager = BackupBrowser()
            success, message = backup_manager.show_backups()
            if success:
                show_notification(message)
                # Ask user if they want to restart Kodi
                if xbmcgui.Dialog().yesno(ADDON_NAME, ADDON.getLocalizedString(32100)):  # Restart Kodi?
                    xbmc.executebuiltin('RestartApp')
            else:
                show_notification(message)
                
        elif sys.argv[1] == 'browse':
            if ADDON.getSettingInt('backup_location_type') != 0:  # Only if remote location is selected
                remote_browser = RemoteBrowser(ADDON)
                remote_browser.browse()
            else:
                show_notification(ADDON.getLocalizedString(32101))  # Please configure a remote location first
    else:
        # Show the main menu
        show_main_menu()

if __name__ == '__main__':
    # This file is only used for script functionality, not service
    run() 