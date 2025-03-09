#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import xbmc
import xbmcaddon
import xbmcvfs

# Add resources directory to path
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))

sys.path.insert(0, os.path.join(ADDON_PATH, 'resources', 'lib'))
from backup_utils import BackupManager

def log(message, level=xbmc.LOGINFO):
    xbmc.log(f'{ADDON_ID}: {message}', level)

class BackupService(xbmc.Monitor):
    def __init__(self):
        super(BackupService, self).__init__()
        self.backup_manager = BackupManager(ADDON)
        self.last_check = 0
        log("Backup service started")
        
        # Initialize schedule info
        self.backup_manager.update_schedule_info()
    
    def onSettingsChanged(self):
        """Called when addon settings are changed"""
        log("Settings changed")
        # Update schedule info when settings change
        self.backup_manager.update_schedule_info()
    
    def check_backup(self):
        """Check if it's time for a backup"""
        current_time = time.time()
        
        # Only check every minute
        if (current_time - self.last_check) < 60:
            return
        
        self.last_check = current_time
        
        if self.backup_manager.should_run_backup():
            log("Starting scheduled backup")
            success, message = self.backup_manager.create_backup()
            log(f"Scheduled backup completed: {message}")
            
            # Update schedule info after backup
            self.backup_manager.update_schedule_info()
    
    def run(self):
        """Main service loop"""
        while not self.abortRequested():
            # Sleep/wait for abort for 10 seconds
            if self.waitForAbort(10):
                # Abort was requested while waiting. We should exit
                break
            
            self.check_backup()

if __name__ == '__main__':
    service = BackupService()
    service.run() 