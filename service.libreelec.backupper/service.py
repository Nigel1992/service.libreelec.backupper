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
    
    # Log service start
    log("Service started", xbmc.LOGINFO)
    
    # Main loop - just keep the service alive
    while not monitor.abortRequested():
        # Sleep for 60 seconds before checking again
        if monitor.waitForAbort(60):
            # Abort was requested while waiting
            break
    
    log("Service stopped", xbmc.LOGINFO)

if __name__ == '__main__':
    log("Starting service.py", xbmc.LOGINFO)
    main() 