#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
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

def main():
    """Main service function - runs in the background"""
    # Initialize the backup manager
    backup_manager = BackupManager()
    
    # Main service loop
    monitor = xbmc.Monitor()
    
    # Update schedule info at startup
    backup_manager.update_schedule_info()
    
    # Log service start
    log("Service started", xbmc.LOGINFO)
    
    # Main loop
    while not monitor.abortRequested():
        # Check if it's time to run a scheduled backup
        if backup_manager.should_run_backup():
            log("Running scheduled backup", xbmc.LOGINFO)
            success, message = backup_manager.create_backup()
            if success:
                log("Scheduled backup completed successfully", xbmc.LOGINFO)
            else:
                log(f"Scheduled backup failed: {message}", xbmc.LOGERROR)
            
            # Update schedule info after backup
            backup_manager.update_schedule_info()
        
        # Sleep for 60 seconds before checking again
        if monitor.waitForAbort(60):
            # Abort was requested while waiting
            break
    
    log("Service stopped", xbmc.LOGINFO)

if __name__ == '__main__':
    log("Starting service.py", xbmc.LOGINFO)
    main() 