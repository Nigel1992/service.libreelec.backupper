#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

# Import the remote browser
from resources.lib.remote_browser import RemoteBrowser

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')

def log(message, level=xbmc.LOGINFO):
    """Log message to Kodi log"""
    xbmc.log(f'{ADDON_ID}: {message}', level)

def handle_settings_action(action):
    """Handle settings actions"""
    log(f"Handling settings action: {action}")
    
    if action == "browse_remote":
        # Launch the remote browser
        browser = RemoteBrowser()
        browser.browse_remote(mode='backup')
        
        # Refresh the settings screen to show updated values
        xbmc.executebuiltin('Container.Refresh')
    else:
        log(f"Unknown settings action: {action}", xbmc.LOGWARNING)

if __name__ == "__main__":
    # Get the action from command line arguments
    if len(sys.argv) > 1:
        action = sys.argv[1]
        handle_settings_action(action)
    else:
        log("No action specified", xbmc.LOGWARNING) 