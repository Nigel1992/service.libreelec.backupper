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

# Log function
def log(message, level=xbmc.LOGINFO):
    xbmc.log(f'{ADDON_ID}: {message}', level)

class BackupBrowser:
    """GUI for browsing and restoring backups"""
    
    def __init__(self):
        self.backup_utils = BackupManager()
        self.remote_browser = RemoteBrowser()
    
    def show_backups(self):
        """Display a list of available backups"""
        # Use RemoteBrowser to show the browse dialog
        selected_file = self.remote_browser.browse_remote(mode='restore')
        if selected_file:
            success, message = self.backup_utils.restore_backup(selected_file)
            if not success:
                xbmcgui.Dialog().ok(ADDON_NAME, f"Failed to restore backup: {message}")

def show_main_menu():
    """Show the main menu with options"""
    options = ["Make Backup", "Restore Backup", "Settings"]
    selected = xbmcgui.Dialog().select(ADDON_NAME, options)
    
    if selected >= 0:
        backup_utils = BackupManager()
        
        if selected == 0:  # Make Backup
            success, message = backup_utils.create_backup()
            if not success:
                xbmcgui.Dialog().ok(ADDON_NAME, f"Backup failed: {message}")
            
        elif selected == 1:  # Restore Backup
            browser = BackupBrowser()
            browser.show_backups()
            
        elif selected == 2:  # Settings
            ADDON.openSettings()

def backup():
    """Create a backup"""
    backup_utils = BackupManager()
    success, message = backup_utils.create_backup()
    if not success:
        xbmcgui.Dialog().ok(ADDON_NAME, f"Backup failed: {message}")
    return success

def main():
    """Handle script arguments"""
    log("Addon started", xbmc.LOGINFO)
    
    # Check if we have specific arguments
    if len(sys.argv) > 1:
        args = sys.argv[1]
        log(f"Addon called with argument: {args}", xbmc.LOGINFO)

        if args == 'backup':
            backup()
        elif args == 'backup_now':
            backup()
        elif args == 'restore':
            browser = BackupBrowser()
            browser.show_backups()
        elif args == 'view':
            browser = BackupBrowser()
            browser.show_backups()
        elif args == 'browse_remote':
            browser = RemoteBrowser()
            browser.browse_remote()
        elif args == 'test_connection':
            # Get the current settings directly from the UI
            # This ensures we have the latest values even if they haven't been saved yet
            try:
                # Create a dialog to show we're working
                progress = xbmcgui.DialogProgress()
                progress.create("Testing Connection", "Preparing to test connection...")
                progress.update(25, "Saving current settings...")
                
                # Force settings to save
                xbmc.executebuiltin('UpdateLocalAddons')
                xbmc.sleep(1000)  # Give Kodi time to update
                
                progress.update(50, "Initializing connection test...")
                
                # Get the current settings
                addon = xbmcaddon.Addon()
                remote_type = int(addon.getSetting('remote_location_type'))
                remote_path = addon.getSetting('remote_path')
                username = addon.getSetting('remote_username')
                password = addon.getSetting('remote_password')
                port = addon.getSetting('remote_port')
                
                progress.update(75, "Testing connection...")
                
                # Test the remote connection with current settings
                browser = RemoteBrowser()
                result = browser.test_connection_with_params(remote_type, remote_path, username, password, port)
                
                progress.close()
                
                if result:
                    xbmcgui.Dialog().ok(ADDON_NAME, "Connection successful!")
                # No else needed as test_connection_with_params will show error dialogs
                
            except Exception as e:
                if 'progress' in locals() and progress:
                    progress.close()
                log(f"Error during test_connection: {str(e)}", xbmc.LOGERROR)
                xbmcgui.Dialog().ok(ADDON_NAME, f"Error testing connection: {str(e)}")
        elif args == 'menu':
            # Explicitly requested menu
            show_main_menu()
        else:
            # Unknown argument, show the menu as fallback
            show_main_menu()
    else:
        # When called as a script without arguments (user clicked the addon)
        # Show the main menu
        log("Addon clicked directly, showing main menu", xbmc.LOGINFO)
        show_main_menu()

if __name__ == '__main__':
    # This file is only used for script functionality, not service
    main() 