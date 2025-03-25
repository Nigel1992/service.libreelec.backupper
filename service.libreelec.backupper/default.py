import sys
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.backup_utils import BackupManager

def main():
    """Main entry point"""
    addon = xbmcaddon.Addon()
    backup_manager = BackupManager(addon)
    
    # Get command line arguments
    if len(sys.argv) < 2:
        return
        
    command = sys.argv[1]
    
    if command == 'backup_now':
        backup_manager.create_backup()
    elif command == 'restore':
        backup_manager.restore_backup()
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
        dialog = xbmcgui.Dialog()
        
        # Get the current setting value
        is_enabled = addon.getSettingBool('enable_rotation')
        
        # Only show warning if trying to enable
        if is_enabled:
            confirmed = dialog.yesno(
                "Warning",
                "Backup rotation will automatically delete old backups when enabled.\n\nAre you sure you want to continue?",
                nolabel="No, Disable",
                yeslabel="Yes, Enable"
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