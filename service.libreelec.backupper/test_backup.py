#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Test script for the backup functionality.
This script simulates the backup process without requiring Kodi.
"""

import os
import sys
import shutil
from datetime import datetime

# Path to the config.txt file (for testing)
TEST_CONFIG_FILE = 'test_config.txt'
# Use a test directory that simulates the /storage/backup path
TEST_BACKUP_DIR = 'test_storage_backup'

def create_test_config():
    """Create a test config.txt file"""
    with open(TEST_CONFIG_FILE, 'w') as f:
        f.write("# This is a test config.txt file\n")
        f.write("test_setting=value\n")
        f.write("another_setting=123\n")
    print(f"Created test config file: {TEST_CONFIG_FILE}")

def backup_config():
    """Backup the test config.txt file"""
    if not os.path.exists(TEST_CONFIG_FILE):
        print(f"Test config file {TEST_CONFIG_FILE} not found")
        return False
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(TEST_BACKUP_DIR):
        os.makedirs(TEST_BACKUP_DIR)
        print(f"Created backup directory: {TEST_BACKUP_DIR}")
    
    # Create timestamp for the backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'config_backup_{timestamp}.txt'
    backup_path = os.path.join(TEST_BACKUP_DIR, backup_filename)
    
    try:
        # Copy the config file
        shutil.copy2(TEST_CONFIG_FILE, backup_path)
        print(f"Config file backed up to {backup_path}")
        return True
    except Exception as e:
        print(f"Error backing up config file: {str(e)}")
        return False

def list_backups():
    """List all backup files"""
    if not os.path.exists(TEST_BACKUP_DIR):
        print("No backups found")
        return
    
    backups = []
    for file in os.listdir(TEST_BACKUP_DIR):
        if file.startswith('config_backup_') and file.endswith('.txt'):
            backups.append(file)
    
    if not backups:
        print("No backups found")
        return
    
    print("\nAvailable backups:")
    for i, backup in enumerate(sorted(backups, reverse=True)):
        print(f"{i+1}. {backup}")

def main():
    """Main test function"""
    print("LibreELEC Config Backupper - Test Script")
    print("---------------------------------------")
    print(f"Backup directory: {os.path.abspath(TEST_BACKUP_DIR)}")
    
    # Create test config file if it doesn't exist
    if not os.path.exists(TEST_CONFIG_FILE):
        create_test_config()
    
    # Backup the config file
    print("\nBacking up config file...")
    backup_config()
    
    # List backups
    list_backups()
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main() 