#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import zipfile
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
from resources.lib.backup_utils import BackupManager
from resources.lib.remote_browser import RemoteBrowser
from resources.lib.email_utils import EmailNotifier

try:
    from resources.lib.custom_gui import CustomDashboardWindow, CustomBackupBrowserWindow
except Exception:
    CustomDashboardWindow = None
    CustomBackupBrowserWindow = None

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

    def show_backup_details(self, backup_path):
        """Show a detailed, scrollable backup information view."""
        lines = []
        backup_name = os.path.basename(backup_path)
        backup_date = self.backup_utils.format_backup_date(backup_path)

        lines.append("[COLOR FF4FC3F7][B]Backup Details[/B][/COLOR]")
        lines.append("[COLOR FFB0BEC5]============================================================[/COLOR]")
        lines.append(f"[COLOR FF90CAF9]Name:[/COLOR] {backup_name}")
        lines.append(f"[COLOR FF90CAF9]Date:[/COLOR] {backup_date}")

        # Remote placeholder details
        if isinstance(backup_path, str) and backup_path.endswith('.json') and os.path.exists(backup_path):
            try:
                with open(backup_path, 'r') as fp:
                    remote_info = json.load(fp)
                remote_type_names = ["SMB", "NFS", "FTP", "SFTP", "WebDAV"]
                remote_type = int(remote_info.get('remote_type', 0))
                remote_type_name = remote_type_names[remote_type] if 0 <= remote_type < len(remote_type_names) else f"Type {remote_type}"

                lines.append(f"[COLOR FF90CAF9]Storage:[/COLOR] Remote ({remote_type_name})")
                lines.append(f"[COLOR FF90CAF9]Remote File:[/COLOR] {remote_info.get('remote_file', 'Unknown')}")
                lines.append(f"[COLOR FF90CAF9]Remote Path:[/COLOR] {remote_info.get('remote_path', 'Unknown')}")
            except Exception as exc:
                lines.append(f"[COLOR FFEF5350]Failed to read remote backup info:[/COLOR] {exc}")

            xbmcgui.Dialog().textviewer(f"{ADDON_NAME} - Backup Details", "\n".join(lines))
            return

        if not os.path.exists(backup_path):
            lines.append("[COLOR FFEF5350]Backup file is not available locally.[/COLOR]")
            xbmcgui.Dialog().textviewer(f"{ADDON_NAME} - Backup Details", "\n".join(lines))
            return

        try:
            file_size = os.path.getsize(backup_path)
            lines.append(f"[COLOR FF90CAF9]Size:[/COLOR] {self.backup_utils.format_size(file_size)}")
        except Exception:
            lines.append("[COLOR FF90CAF9]Size:[/COLOR] Unknown")

        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                files = [info for info in zipf.filelist if info.filename != 'manifest.json']
                lines.append(f"[COLOR FF90CAF9]Archived Files:[/COLOR] {len(files)}")

                manifest = None
                try:
                    manifest = json.loads(zipf.read('manifest.json'))
                except Exception:
                    manifest = None

                if manifest:
                    items = manifest.get('items', [])
                    if items:
                        lines.append(f"[COLOR FF90CAF9]Included Items:[/COLOR] {', '.join(items)}")
                    if manifest.get('total_size_formatted'):
                        lines.append(f"[COLOR FF90CAF9]Original Data Size:[/COLOR] {manifest.get('total_size_formatted')}")

                section_counts = {}
                for info in files:
                    section = info.filename.split('/')[0] if '/' in info.filename else 'root'
                    section_bucket = section_counts.setdefault(section, {'files': 0, 'bytes': 0})
                    section_bucket['files'] += 1
                    section_bucket['bytes'] += info.file_size

                if section_counts:
                    lines.append("")
                    lines.append("[COLOR FFFFD54F][B]Sections[/B][/COLOR]")
                    lines.append("[COLOR FFB0BEC5]------------------------------------------------------------[/COLOR]")
                    for section in sorted(section_counts.keys()):
                        section_info = section_counts[section]
                        section_label = self.backup_utils.format_section_name(section)
                        lines.append(
                            f"* {section_label}: {section_info['files']} files ({self.backup_utils.format_size(section_info['bytes'])})"
                        )
        except Exception as exc:
            lines.append(f"[COLOR FFEF5350]Failed to inspect backup content:[/COLOR] {exc}")

        xbmcgui.Dialog().textviewer(f"{ADDON_NAME} - Backup Details", "\n".join(lines))

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
            xbmcgui.Dialog().ok(
                ADDON_NAME,
                "No backup files were found.\n\n"
                "Tip: Create your first backup from the main menu, then return here to restore or inspect it."
            )
            return

        # Create backup options with detailed information
        xbmc.log("BackupBrowser: Processing backup list...", xbmc.LOGDEBUG)
        backup_options = []
        for backup in backups:
            try:
                backup_name = os.path.basename(backup)
                xbmc.log(f"BackupBrowser: Processing backup: {backup_name}", xbmc.LOGDEBUG)

                # Get backup date from filename/metadata (supports old and new formats)
                backup_date = self.backup_utils.format_backup_date(backup)

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

                # Create display string and metadata entry for custom GUI
                display_name = f"{backup_date} - {backup_name}"
                if backup_size_formatted != "Unknown size":
                    display_name += f" ({backup_size_formatted})"

                backup_options.append({
                    'display': display_name,
                    'path': backup,
                    'name': backup_name,
                    'date': backup_date,
                    'size': backup_size_formatted,
                    'location': self.backup_utils.backup_dir if self.backup_utils.location_type == 0 else 'Remote location',
                    'extra': f"Mode: {mode.capitalize()}"
                })
                xbmc.log(f"BackupBrowser: Added backup option: {display_name}", xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log(f"BackupBrowser: Error processing backup {backup}: {str(e)}", xbmc.LOGERROR)
                continue

        xbmc.log(f"BackupBrowser: Created {len(backup_options)} backup options", xbmc.LOGINFO)

        if not backup_options:
            xbmc.log("BackupBrowser: No valid backup options created", xbmc.LOGWARNING)
            xbmcgui.Dialog().ok(ADDON_NAME, "No valid backup files found")
            return

        dialog = xbmcgui.Dialog()
        selected = -1
        custom_window_loaded = False

        # Prefer custom backup browser window for a polished, cross-Kodi UI.
        if CustomBackupBrowserWindow is not None:
            try:
                backup_window = CustomBackupBrowserWindow('custom_backup_browser.xml', ADDON_PATH, 'default', '1080i')
                backup_window.set_data(backup_options, mode, ADDON_NAME)
                backup_window.doModal()
                selected = backup_window.selected_index if backup_window.selected_index is not None else -1
                custom_window_loaded = True
                del backup_window
            except Exception as e:
                xbmc.log(f"BackupBrowser: Custom backup window failed, falling back to dialog: {str(e)}", xbmc.LOGWARNING)

        if not custom_window_loaded:
            title = "Select backup to restore" if mode == 'restore' else "Available backups"
            xbmc.log(f"BackupBrowser: Showing selection dialog with title: {title}", xbmc.LOGINFO)
            selected = dialog.select(title, [opt['display'] for opt in backup_options])

        if selected == -1:  # User cancelled
            xbmc.log("BackupBrowser: User cancelled backup selection", xbmc.LOGINFO)
            return

        selected_backup = backup_options[selected]['path']
        selected_display = backup_options[selected]['display']
        xbmc.log(f"BackupBrowser: User selected backup: {selected_display}", xbmc.LOGINFO)

        if mode == 'restore':
            # Confirm restore
            xbmc.log("BackupBrowser: Showing restore confirmation dialog", xbmc.LOGDEBUG)
            confirmed = dialog.yesno(
                ADDON_NAME,
                f"Restore backup: {os.path.basename(selected_backup)}?",
                nolabel="No",
                yeslabel="Yes"
            )

            if confirmed:
                # Show detailed warning about what will happen
                final_confirm = dialog.yesno(
                    ADDON_NAME,
                    "This will restore the following:\n"
                    "• User settings and Kodi configuration\n"
                    "• Add-on configurations\n"
                    "• Userdata (settings, databases, etc.)\n\n"
                    "Existing files will be overwritten.\n"
                    "This process cannot be undone.",
                    nolabel="Cancel",
                    yeslabel="Restore"
                )
                
                if final_confirm:
                    xbmc.log(f"BackupBrowser: Starting backup restoration: {selected_backup}", xbmc.LOGINFO)
                    success, message = self.backup_utils.restore_backup(selected_backup)
                    if success:
                        xbmc.log("BackupBrowser: Backup restoration completed successfully", xbmc.LOGINFO)
                        self.backup_utils.show_last_operation_summary()
                    else:
                        xbmc.log(f"BackupBrowser: Backup restoration failed: {message}", xbmc.LOGERROR)
                        dialog.ok(ADDON_NAME, f"Failed to restore backup: {message}")
                else:
                    xbmc.log("BackupBrowser: User cancelled restore after warning", xbmc.LOGINFO)
            else:
                xbmc.log("BackupBrowser: User cancelled backup restoration", xbmc.LOGINFO)
        else:
            # For view mode, show detailed backup information
            xbmc.log("BackupBrowser: Showing detailed backup information", xbmc.LOGDEBUG)
            self.show_backup_details(selected_backup)

def show_main_menu():
    """Show the main menu with options"""
    backup_utils = BackupManager()
    browser = BackupBrowser()

    menu_items = [
        {
            'action': 'backup',
            'label': 'Create Backup',
            'description': 'Create a fresh backup using your current settings.'
        },
        {
            'action': 'restore',
            'label': 'Restore Backup',
            'description': 'Restore Kodi data from an existing backup archive.'
        },
        {
            'action': 'browse',
            'label': 'Browse Backup Details',
            'description': 'Inspect backup contents, size, and included sections.'
        },
        {
            'action': 'settings',
            'label': 'Open Settings',
            'description': 'Configure backup items, schedule, locations, and notifications.'
        },
        {
            'action': 'exit',
            'label': 'Close Dashboard',
            'description': 'Exit the addon dashboard.'
        },
    ]

    while True:
        backup_utils.update_backup_location()
        backups = backup_utils.get_all_backups()
        backup_count = len(backups)
        last_backup = backup_utils.get_last_successful_backup()

        total_backup_size = 0
        if backup_utils.location_type == 0:
            for backup_path in backups:
                if os.path.exists(backup_path):
                    try:
                        total_backup_size += os.path.getsize(backup_path)
                    except Exception:
                        pass

        if backup_utils.location_type == 0:
            location_text = f"Local ({backup_utils.backup_dir})"
        else:
            location_text = f"Remote ({getattr(backup_utils, 'remote_path', 'Not configured')})"

        scheduler_text = "Enabled" if ADDON.getSettingBool('enable_scheduler') else "Disabled"

        selected_action = None
        custom_window_loaded = False

        if CustomDashboardWindow is not None:
            try:
                dashboard_info = {
                    'title': ADDON_NAME,
                    'subtitle': 'Professional Backup Dashboard',
                    'backup_count': f"Backups Available: {backup_count}",
                    'stored_size': f"Stored Size: {backup_utils.format_size(total_backup_size)}",
                    'last_backup': f"Last Backup: {last_backup}",
                    'location': f"Location: {location_text}",
                    'scheduler': f"Scheduler: {scheduler_text}",
                }
                dashboard_window = CustomDashboardWindow('custom_dashboard.xml', ADDON_PATH, 'default', '1080i')
                dashboard_window.set_data(menu_items, dashboard_info)
                dashboard_window.doModal()
                selected_action = dashboard_window.selected_action
                custom_window_loaded = True
                del dashboard_window
            except Exception as e:
                xbmc.log(f"MainMenu: Custom dashboard failed, falling back to default dialog: {str(e)}", xbmc.LOGWARNING)

        if not custom_window_loaded:
            fallback_options = [
                "Create Backup - Save selected items",
                "Restore Backup - Recover from an existing backup",
                "Browse Backup Details - Inspect backup contents",
                "Settings - Configure addon options",
                "Close"
            ]
            selected = xbmcgui.Dialog().select(ADDON_NAME, fallback_options)
            if selected == -1 or selected == 4:
                return
            selected_action = ['backup', 'restore', 'browse', 'settings'][selected]

        if selected_action in (None, 'exit'):
            return

        if selected_action == 'backup':
            success, message = backup_utils.create_backup()
            if success:
                if not backup_utils.show_last_operation_summary():
                    xbmcgui.Dialog().ok(ADDON_NAME, "Backup completed successfully")
            else:
                xbmcgui.Dialog().ok(ADDON_NAME, f"Backup failed: {message}")
                if "No items selected" in str(message):
                    open_settings = xbmcgui.Dialog().yesno(
                        ADDON_NAME,
                        "No backup items are selected.\n\nOpen settings now to choose what to include?",
                        yeslabel="Open Settings",
                        nolabel="Not Now"
                    )
                    if open_settings:
                        ADDON.openSettings()
        elif selected_action == 'restore':
            browser.show_backups(mode='restore')
        elif selected_action == 'browse':
            browser.show_backups(mode='view')
        elif selected_action == 'settings':
            ADDON.openSettings()

def backup():
    """Create a backup"""
    backup_utils = BackupManager()
    success, message = backup_utils.create_backup()
    if success:
        backup_utils.show_last_operation_summary()
    else:
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
