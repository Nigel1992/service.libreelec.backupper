import sys
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.backup_utils import BackupManager

try:
    from resources.lib.custom_gui import ask_yesno, show_message
except Exception:
    ask_yesno = None
    show_message = None


def popup_message(title, text):
    """Show a message popup using custom GUI when available."""
    try:
        if show_message is not None:
            show_message(title, text)
        else:
            xbmcgui.Dialog().ok(title, text)
    except Exception:
        xbmcgui.Dialog().ok(title, text)


def popup_confirm(title, text, yes_label='Yes', no_label='No'):
    """Show a yes/no popup using custom GUI when available."""
    try:
        if ask_yesno is not None:
            return ask_yesno(title, text, yes_label=yes_label, no_label=no_label)
        return xbmcgui.Dialog().yesno(title, text, yeslabel=yes_label, nolabel=no_label)
    except Exception:
        try:
            return xbmcgui.Dialog().yesno(title, text, yeslabel=yes_label, nolabel=no_label)
        except Exception:
            return False

def main():
    """Main entry point"""
    addon = xbmcaddon.Addon()
    backup_manager = BackupManager(addon)
    
    # Set author and version in settings
    addon.setSetting('author', 'Nigel1992')
    addon.setSetting('version', 'Version 1.5.0')
    
    # Get command line arguments
    if len(sys.argv) < 2:
        return
        
    command = sys.argv[1]
    
    if command == 'backup_now':
        success, message = backup_manager.create_backup()
        if success:
            try:
                show_popup = addon.getSettingBool('show_backup_summary_popup')
            except Exception:
                show_popup = str(addon.getSetting('show_backup_summary_popup')).lower() in ('true', '1')

            if show_popup:
                backup_manager.show_last_operation_summary()
        else:
            popup_message(addon.getAddonInfo("name"), f"Backup failed: {message}")
    elif command == 'restore':
        success, message = backup_manager.restore_backup()
        if success:
            backup_manager.show_last_operation_summary()
        elif message not in ("Backup restore cancelled", "No backup files found"):
            popup_message(addon.getAddonInfo("name"), f"Restore failed: {message}")
    elif command == 'view':
        backup_manager.view_backups()
    elif command == 'test_connection':
        backup_manager.test_connection()
    elif command == 'test_email':
        backup_manager.test_email()
    elif command == 'browse_remote':
        backup_manager.browse_remote()
    elif command == 'rotation_warning':
        # Show warning dialog when enabling rotation
        addon = xbmcaddon.Addon()
        
        # Get the current setting value
        is_enabled = addon.getSettingBool('enable_rotation')
        
        # Only show warning if trying to enable
        if is_enabled:
            confirmed = popup_confirm(
                "Warning",
                "Backup rotation will automatically delete old backups when enabled.\n\nAre you sure you want to continue?",
                no_label="No, Disable",
                yes_label="Yes, Enable"
            )
            
            if not confirmed:
                # User chose to disable rotation
                addon.setSetting('enable_rotation', 'false')
                xbmc.log("User disabled backup rotation after warning", xbmc.LOGINFO)
                dialog.notification(
                    addon.getAddonInfo("name"),
                    "Backup rotation has been disabled",
                    xbmcgui.NOTIFICATION_INFO,
                    5000
                )

if __name__ == '__main__':
    main() 