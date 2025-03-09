#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
from resources.lib.backup_utils import BackupManager

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

def run():
    """Main entry point"""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        backup_utils = BackupManager()
        
        if arg == "backup_now":
            success, message = backup_utils.create_backup()
            if not success:
                xbmcgui.Dialog().ok(ADDON_NAME, f"Backup failed: {message}")
            
        elif arg == "restore":
            browser = BackupBrowser()
            browser.show_backups()
            
        elif arg == "view":
            browser = BackupBrowser()
            browser.show_backups()
    else:
        show_main_menu()

if __name__ == '__main__':
    run() 