#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Change to the service.libreelec.backupper directory
os.chdir('/home/nigel/service.libreelec.backupper/service.libreelec.backupper')
# Add the current directory to the path
sys.path.insert(0, '.')

# Mock the Kodi modules for testing
class MockXBMC:
    LOGINFO = 1
    LOGDEBUG = 0
    LOGERROR = 4
    LOGWARNING = 2
    LOGNONE = 5
    
    @staticmethod
    def log(message, level):
        level_names = {0: 'DEBUG', 1: 'INFO', 2: 'WARNING', 4: 'ERROR', 5: 'NONE'}
        print(f"LOG[{level_names.get(level, level)}]: {message}")

    @staticmethod
    def executebuiltin(command):
        print(f"EXECUTE: {command}")

    @staticmethod
    def translatePath(path):
        return path

    @staticmethod
    def sleep(ms):
        pass

class MockXBMCGUI:
    class Dialog:
        def ok(self, title, message):
            print(f"DIALOG OK: {title} - {message}")

        def select(self, title, items):
            print(f"DIALOG SELECT: {title} - {items}")
            return 0

        def browse(self, *args):
            print(f"DIALOG BROWSE: {args}")
            return "smb://testserver/testshare"

        def textviewer(self, title, message):
            print(f"DIALOG TEXTVIEWER: {title} - {message}")

        def notification(self, title, message, icon):
            print(f"DIALOG NOTIFICATION: {title} - {message}")

    class DialogProgress:
        def create(self, title, message):
            print(f"PROGRESS CREATE: {title} - {message}")

        def update(self, percent, message):
            print(f"PROGRESS UPDATE: {percent}% - {message}")

        def close(self):
            print("PROGRESS CLOSE")

class MockXBMCADDON:
    instance = None
    
    def __init__(self):
        self.settings = {
            'remote_location_type': '0',  # SMB
            'remote_path': 'testserver/testshare',
            'remote_username': '',
            'remote_password': '',
            'remote_port': ''
        }

    def getAddonInfo(self, key):
        if key == 'id':
            return 'service.libreelec.backupper'
        elif key == 'path':
            return '/home/nigel/service.libreelec.backupper'
        return ''

    def getSetting(self, key):
        return self.settings.get(key, '')

    def setSetting(self, key, value):
        self.settings[key] = value
        print(f"SETTING: {key} = {value}")

    def getLocalizedString(self, id):
        return f"String {id}"
    
    def getSettingBool(self, key):
        return self.settings.get(key, 'false') == 'true'

class MockXBMCADDONModule:
    def __init__(self):
        self._instance = MockXBMCADDON()
    
    def Addon(self):
        return self._instance

# Mock the modules
sys.modules['xbmc'] = MockXBMC()
sys.modules['xbmcgui'] = MockXBMCGUI()
sys.modules['xbmcvfs'] = MockXBMC()
sys.modules['xbmcaddon'] = MockXBMCADDONModule()

# Now test the RemoteBrowser
from resources.lib.remote_browser import RemoteBrowser

def test_remote_browser():
    print("=== Testing RemoteBrowser Fix ===")

    # Test 1: Create RemoteBrowser instance
    print("\n1. Creating RemoteBrowser instance...")
    browser = RemoteBrowser()

    # Test 2: Check if password attribute exists
    print("\n2. Checking if password attribute exists...")
    if hasattr(browser, 'password'):
        print("✓ SUCCESS: password attribute exists")
        print(f"  Password value: '{browser.password}'")
    else:
        print("✗ FAILED: password attribute does not exist")
        return False

    # Test 3: Check other attributes
    print("\n3. Checking other attributes...")
    print(f"  remote_type: {browser.remote_type}")
    print(f"  remote_path: {browser.remote_path}")
    print(f"  username: '{browser.username}'")
    print(f"  port: '{browser.port}'")

    # Test 4: Test connection method (should not crash)
    print("\n4. Testing connection method...")
    try:
        # This should not crash with the AttributeError anymore
        result = browser.test_connection()
        print(f"✓ SUCCESS: test_connection() completed without AttributeError")
        print(f"  Result: {result}")
    except AttributeError as e:
        if "password" in str(e):
            print(f"✗ FAILED: AttributeError still occurs: {e}")
            return False
        else:
            print(f"✗ FAILED: Different AttributeError: {e}")
            return False
    except Exception as e:
        print(f"✓ SUCCESS: test_connection() completed (other error is expected in test environment: {e})")

    print("\n=== All tests passed! ===")
    return True

if __name__ == "__main__":
    success = test_remote_browser()
    sys.exit(0 if success else 1)