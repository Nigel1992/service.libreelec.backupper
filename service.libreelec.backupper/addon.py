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
from resources.lib.email_utils import EmailNotifier

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

    def show_backups(self, mode='view'):
        """Display a list of available backups for selection
        mode: 'view' for viewing/listing, 'restore' for selecting to restore"""
        xbmc.log(f"BackupBrowser: Showing backups in {mode} mode", xbmc.LOGINFO)

        # Get list of available backups
        xbmc.log("BackupBrowser: Retrieving backup list...", xbmc.LOGDEBUG)
        backups = self.backup_utils.get_all_backups()
        xbmc.log(f"BackupBrowser: Found {len(backups)} backups", xbmc.LOGINFO)

        if not backups:
            xbmc.log("BackupBrowser: No backup files found", xbmc.LOGWARNING)
            xbmcgui.Dialog().ok(ADDON_NAME, "No backup files found")
            return

        # Create backup options with detailed information
        xbmc.log("BackupBrowser: Processing backup list...", xbmc.LOGDEBUG)
        backup_options = []
        for backup in backups:
            try:
                backup_name = os.path.basename(backup)
                xbmc.log(f"BackupBrowser: Processing backup: {backup_name}", xbmc.LOGDEBUG)

                # Get backup date from filename (format: backup_items_timestamp.zip)
                # Extract timestamp from filename
                try:
                    # Split by underscore and find the timestamp part
                    parts = backup_name.replace('.zip', '').split('_')
                    if len(parts) >= 3:
                        # Find the timestamp (should be the last part that's all digits)
                        timestamp_part = None
                        for part in reversed(parts):
                            if part.isdigit() and len(part) == 14:  # YYYYMMDDHHMMSS format
                                timestamp_part = part
                                break

                        if timestamp_part:
                            # Parse timestamp: YYYYMMDDHHMMSS
                            year = int(timestamp_part[0:4])
                            month = int(timestamp_part[4:6])
                            day = int(timestamp_part[6:8])
                            hour = int(timestamp_part[8:10])
                            minute = int(timestamp_part[10:12])
                            second = int(timestamp_part[12:14])

                            from datetime import datetime
                            backup_date = datetime(year, month, day, hour, minute, second).strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            backup_date = "Unknown date"
                    else:
                        backup_date = "Unknown date"
                except Exception as e:
                    xbmc.log(f"BackupBrowser: Error parsing backup date for {backup_name}: {str(e)}", xbmc.LOGWARNING)
                    backup_date = "Unknown date"

                # Get backup size
                try:
                    if self.backup_utils.location_type == 0:  # Local
                        backup_size = os.path.getsize(backup)
                    else:
                        # For remote backups, size info may not be available
                        backup_size = 0
                    backup_size_formatted = self.backup_utils.format_size(backup_size)
                except Exception as e:
                    xbmc.log(f"BackupBrowser: Error getting backup size for {backup_name}: {str(e)}", xbmc.LOGWARNING)
                    backup_size_formatted = "Unknown size"

                # Create display string
                display_name = f"{backup_date} - {backup_name}"
                if backup_size_formatted != "Unknown size":
                    display_name += f" ({backup_size_formatted})"

                backup_options.append((display_name, backup))
                xbmc.log(f"BackupBrowser: Added backup option: {display_name}", xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log(f"BackupBrowser: Error processing backup {backup}: {str(e)}", xbmc.LOGERROR)
                continue

        xbmc.log(f"BackupBrowser: Created {len(backup_options)} backup options", xbmc.LOGINFO)

        if not backup_options:
            xbmc.log("BackupBrowser: No valid backup options created", xbmc.LOGWARNING)
            xbmcgui.Dialog().ok(ADDON_NAME, "No valid backup files found")
            return

        # Show dialog to select backup
        dialog = xbmcgui.Dialog()
        title = "Select backup to restore" if mode == 'restore' else "Available backups"
        xbmc.log(f"BackupBrowser: Showing selection dialog with title: {title}", xbmc.LOGINFO)
        selected = dialog.select(title, [opt[0] for opt in backup_options])

        if selected == -1:  # User cancelled
            xbmc.log("BackupBrowser: User cancelled backup selection", xbmc.LOGINFO)
            return

        selected_backup = backup_options[selected][1]
        selected_display = backup_options[selected][0]
        xbmc.log(f"BackupBrowser: User selected backup: {selected_display}", xbmc.LOGINFO)

        if mode == 'restore':
            # Confirm restore
            xbmc.log("BackupBrowser: Showing restore confirmation dialog", xbmc.LOGDEBUG)
            confirmed = dialog.yesno(
                ADDON_NAME,
                f"Restore backup: {os.path.basename(selected_backup)}?",
                "This will overwrite existing files. Continue?"
            )

            if confirmed:
                xbmc.log(f"BackupBrowser: Starting backup restoration: {selected_backup}", xbmc.LOGINFO)
                success, message = self.backup_utils.restore_backup(selected_backup)
                if success:
                    xbmc.log("BackupBrowser: Backup restoration completed successfully", xbmc.LOGINFO)
                    dialog.ok(ADDON_NAME, "Backup restored successfully")
                else:
                    xbmc.log(f"BackupBrowser: Backup restoration failed: {message}", xbmc.LOGERROR)
                    dialog.ok(ADDON_NAME, f"Failed to restore backup: {message}")
            else:
                xbmc.log("BackupBrowser: User cancelled backup restoration", xbmc.LOGINFO)
        else:
            # For view mode, just show backup info
            xbmc.log("BackupBrowser: Showing backup information dialog", xbmc.LOGDEBUG)
            dialog.ok(ADDON_NAME, f"Backup: {os.path.basename(selected_backup)}")

def show_main_menu():
    """Show the main menu with options"""
    backup_utils = BackupManager()
    last_backup = backup_utils.get_last_successful_backup()
    next_backup = backup_utils.get_next_scheduled_backup()
    
    # Create menu items with backup information
    options = [
        "Make Backup",
        "Restore Backup",
        "Settings",
        "----------------------------------------",  # Divider line
        f"Last Backup: {last_backup}",
        f"Next Backup: {next_backup}"
    ]
    
    selected = xbmcgui.Dialog().select(ADDON_NAME, options)
    
    if selected >= 0:
        if selected == 0:  # Make Backup
            success, message = backup_utils.create_backup()
            if not success:
                xbmcgui.Dialog().ok(ADDON_NAME, f"Backup failed: {message}")
        elif selected == 1:  # Restore Backup
            browser = BackupBrowser()
            browser.show_backups(mode='restore')
        elif selected == 2:  # Settings
            ADDON.openSettings()

def backup():
    """Create a backup"""
    backup_utils = BackupManager()
    success, message = backup_utils.create_backup()
    if not success:
        xbmcgui.Dialog().ok(ADDON_NAME, f"Backup failed: {message}")
    return success

def test_email():
    """Test email notification settings"""
    dialog = xbmcgui.Dialog()
    
    # Force settings to save
    xbmc.executebuiltin('UpdateLocalAddons')
    xbmc.sleep(1000)  # Give Kodi time to update
    
    # Reload addon to get fresh settings
    addon = xbmcaddon.Addon()
    
    # Show progress dialog
    dialog.notification(
        ADDON.getAddonInfo('name'),
        ADDON.getLocalizedString(32132),  # "Sending test email..."
        xbmcgui.NOTIFICATION_INFO
    )
    
    # Send test email
    email_notifier = EmailNotifier()
    success, message = email_notifier.test_email()
    
    if success:
        dialog.ok(
            ADDON.getLocalizedString(32130),  # "Email Test Successful"
            ADDON.getLocalizedString(32133)   # "Test email sent successfully!"
        )
    else:
        dialog.ok(
            ADDON.getLocalizedString(32131),  # "Email Test Failed"
            f"{ADDON.getLocalizedString(32134)}: {message}"  # "Failed to send test email: {error}"
        )

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
            browser.show_backups(mode='restore')
        elif args == 'view':
            browser = BackupBrowser()
            browser.show_backups(mode='view')
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
        elif args == 'test_email':
            test_email()
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
