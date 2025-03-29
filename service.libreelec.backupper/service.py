#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcaddon
import xbmcvfs
from datetime import datetime, timedelta
from resources.lib.backup_utils import BackupManager

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ADDON_DATA_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
LAST_BACKUP_FILE = os.path.join(ADDON_DATA_PATH, 'last_backup.txt')
LAST_ATTEMPT_FILE = os.path.join(ADDON_DATA_PATH, 'last_attempt.txt')

# Log function
def log(message, level=xbmc.LOGINFO):
    xbmc.log(f'{ADDON_ID}: {message}', level)

def get_last_backup_time():
    """Get the last backup time from file"""
    if os.path.exists(LAST_BACKUP_FILE):
        try:
            with open(LAST_BACKUP_FILE, 'r') as f:
                last_backup_str = f.read().strip()
                return datetime.strptime(last_backup_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None
    return None

def get_last_attempt_time():
    """Get the last backup attempt time from file"""
    if os.path.exists(LAST_ATTEMPT_FILE):
        try:
            with open(LAST_ATTEMPT_FILE, 'r') as f:
                last_attempt_str = f.read().strip()
                return datetime.strptime(last_attempt_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None
    return None

def save_last_backup_time(backup_time):
    """Save the last successful backup time to file"""
    if not os.path.exists(ADDON_DATA_PATH):
        os.makedirs(ADDON_DATA_PATH)
    with open(LAST_BACKUP_FILE, 'w') as f:
        f.write(backup_time.strftime('%Y-%m-%d %H:%M:%S'))

def save_last_attempt_time(attempt_time):
    """Save the last backup attempt time to file"""
    if not os.path.exists(ADDON_DATA_PATH):
        os.makedirs(ADDON_DATA_PATH)
    with open(LAST_ATTEMPT_FILE, 'w') as f:
        f.write(attempt_time.strftime('%Y-%m-%d %H:%M:%S'))

def check_reminders(current_time, schedule_time):
    """Check if we should show any reminder notifications"""
    if not ADDON.getSettingBool('enable_reminders'):
        return False, None

    # Calculate time difference in minutes
    current_minutes = current_time.hour * 60 + current_time.minute
    schedule_minutes = schedule_time.hour * 60 + schedule_time.minute
    time_diff = schedule_minutes - current_minutes

    # Check each reminder interval
    if time_diff == 60 and ADDON.getSettingBool('reminder_1hour'):
        return True, 60
    elif time_diff == 30 and ADDON.getSettingBool('reminder_30min'):
        return True, 30
    elif time_diff == 10 and ADDON.getSettingBool('reminder_10min'):
        return True, 10
    elif time_diff == 1 and ADDON.getSettingBool('reminder_1min'):
        return True, 1

    return False, None

def should_run_backup():
    """Check if it's time to run a scheduled backup"""
    if not ADDON.getSettingBool('enable_scheduler'):
        return False, False, None, False, False, None

    current_time = datetime.now()
    schedule_time = datetime.strptime(ADDON.getSetting('schedule_time'), '%H:%M').time()
    schedule_type = ADDON.getSettingInt('schedule_type')  # 0=Daily, 1=Weekly, 2=Monthly
    run_missed = ADDON.getSettingBool('run_missed_backups')

    # Get the target backup time for today
    target_time = datetime.combine(current_time.date(), schedule_time)
    
    # Get last backup and attempt times
    last_backup = get_last_backup_time()
    last_attempt = get_last_attempt_time()
    
    # Check if we're within the backup window
    current_minutes = current_time.hour * 60 + current_time.minute
    schedule_minutes = schedule_time.hour * 60 + schedule_time.minute
    time_diff = schedule_minutes - current_minutes
    
    # Check for reminders
    should_remind, reminder_minutes = check_reminders(current_time, schedule_time)
    
    # Return tuple of (should_run, is_missed, missed_date, show_warning, should_remind, reminder_minutes)
    def check_result(should_run, is_missed=False, missed_date=None, show_warning=False, should_remind=False, reminder_minutes=None):
        return (should_run, is_missed, missed_date, show_warning, should_remind, reminder_minutes)

    # If we've already attempted a backup today, don't try again
    if last_attempt and last_attempt.date() == current_time.date():
        return check_result(False)

    if schedule_type == 0:  # Daily
        if time_diff == 0:  # At scheduled time
            return check_result(True)
        elif run_missed and last_backup:
            # Run if we missed today's backup and haven't run yet
            if current_time > target_time and last_backup.date() < current_time.date():
                return check_result(True, True, target_time.date())
            
    elif schedule_type == 1:  # Weekly
        schedule_day = ADDON.getSettingInt('schedule_day')  # 0=Monday, 6=Sunday
        is_schedule_day = current_time.weekday() == schedule_day
        
        if is_schedule_day:
            if time_diff == 0:  # At scheduled time
                return check_result(True)
            elif run_missed and last_backup:
                # If it's still the scheduled day but we missed the window
                if current_time > target_time and last_backup.date() < current_time.date():
                    return check_result(True, True, target_time.date())
        elif run_missed and last_backup:
            # If we completely missed the last scheduled day
            last_schedule = current_time - timedelta(days=(current_time.weekday() - schedule_day) % 7)
            if current_time > last_schedule and (last_backup is None or last_backup < last_schedule):
                return check_result(True, True, last_schedule.date())
            
    elif schedule_type == 2:  # Monthly
        schedule_date = ADDON.getSettingInt('schedule_date') + 1  # Convert 0-based to 1-based
        is_schedule_date = current_time.day == schedule_date
        
        if is_schedule_date:
            if time_diff == 0:  # At scheduled time
                return check_result(True)
            elif run_missed and last_backup:
                # If it's still the scheduled date but we missed the window
                if current_time > target_time and last_backup.date() < current_time.date():
                    return check_result(True, True, target_time.date())
        elif run_missed and last_backup:
            # If we completely missed the last scheduled date
            if current_time.day > schedule_date:
                last_schedule = current_time.replace(day=schedule_date)
                if last_backup is None or last_backup < last_schedule:
                    return check_result(True, True, last_schedule.date())

    return check_result(False, should_remind=should_remind, reminder_minutes=reminder_minutes)

def main():
    """Main service function - runs in the background"""
    # Initialize backup manager
    backup_manager = BackupManager()
    
    # Main service loop
    monitor = xbmc.Monitor()
    last_check = datetime.now()
    
    # Log service start
    log("Service started", xbmc.LOGINFO)
    
    # Main loop
    while not monitor.abortRequested():
        current_time = datetime.now()
        
        # Check scheduler every minute
        if (current_time - last_check).total_seconds() >= 60:
            should_run, is_missed, missed_date, show_warning, should_remind, reminder_minutes = should_run_backup()
            
            if should_remind:
                # Calculate string ID based on reminder time
                if reminder_minutes == 1:
                    time_msg = ADDON.getLocalizedString(32104)  # 1 minute reminder
                elif reminder_minutes == 10:
                    time_msg = ADDON.getLocalizedString(32103)  # 10 minute reminder
                elif reminder_minutes == 30:
                    time_msg = ADDON.getLocalizedString(32102)  # 30 minute reminder
                else:
                    time_msg = ADDON.getLocalizedString(32101)  # 1 hour reminder
                backup_manager.notify(time_msg, persistent=False)
            elif should_run:
                if is_missed:
                    # Format the missed date
                    date_str = missed_date.strftime('%Y-%m-%d')
                    log(ADDON.getLocalizedString(32099) % date_str, xbmc.LOGINFO)
                    backup_manager.notify(ADDON.getLocalizedString(32098), date_str, persistent=True)
                else:
                    # Starting backup now
                    log(ADDON.getLocalizedString(32087), xbmc.LOGINFO)
                    backup_manager.notify(ADDON.getLocalizedString(32087), persistent=True)
                
                try:
                    # Save attempt time before starting
                    save_last_attempt_time(current_time)
                    
                    # Run the backup
                    success, message = backup_manager.create_backup()
                    
                    if success:
                        save_last_backup_time(current_time)
                        log(ADDON.getLocalizedString(32088), xbmc.LOGINFO)
                    else:
                        error_msg = f"{ADDON.getLocalizedString(32089)}: {message}"
                        log(error_msg, xbmc.LOGERROR)
                        # Show persistent notification for failed backup
                        backup_manager.notify(ADDON.getLocalizedString(32089), message, persistent=True)
                except Exception as e:
                    error_msg = f"{ADDON.getLocalizedString(32089)}: {str(e)}"
                    log(error_msg, xbmc.LOGERROR)
                    backup_manager.notify(ADDON.getLocalizedString(32089), str(e), persistent=True)
            last_check = current_time
        
        # Sleep for 30 seconds before checking again
        if monitor.waitForAbort(30):
            # Abort was requested while waiting
            break
    
    log("Service stopped", xbmc.LOGINFO)

if __name__ == '__main__':
    log("Starting service.py", xbmc.LOGINFO)
    main() 