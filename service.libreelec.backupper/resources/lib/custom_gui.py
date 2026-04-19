#!/usr/bin/python3
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os
import time
import xml.etree.ElementTree as ET


BACK_ACTIONS = {9, 10, 92, 216, 247, 257, 275, 61467, 61448}
SELECT_ACTIONS = {7, 100}
NAV_ACTIONS = {1, 2, 3, 4, 5, 6, 104, 105}


class CustomDashboardWindow(xbmcgui.WindowXMLDialog):
    """Custom dashboard window for the add-on main menu."""

    CONTROL_ACTION_LIST = 1000
    CONTROL_TITLE = 1100
    CONTROL_SUBTITLE = 1101
    CONTROL_DESCRIPTION = 2100

    CONTROL_BACKUP_COUNT = 2200
    CONTROL_STORED_SIZE = 2201
    CONTROL_LAST_BACKUP = 2202
    CONTROL_LOCATION = 2203
    CONTROL_SCHEDULER = 2204

    def __init__(self, *args, **kwargs):
        self.menu_items = []
        self.info = {}
        self.selected_action = None
        self.action_descriptions = {
            "backup": "Create a new backup snapshot with your selected data sources.",
            "restore": "Select and restore a previous backup package.",
            "browse": "Review available backups, timestamps, and sizes.",
            "settings": "Configure destinations, schedule, and backup scope.",
        }
        self.action_hints = {
            "backup": "Tip: Verify backup items in Settings first.",
            "restore": "Tip: Inspect backup details before restoring.",
            "browse": "Tip: Use browse mode before cleanup operations.",
            "settings": "Tip: Configure remote storage and notifications here.",
        }

    def set_data(self, menu_items, info):
        self.menu_items = menu_items or []
        self.info = info or {}

    def onInit(self):
        self._set_label(self.CONTROL_TITLE, self.info.get("title", "Backup Dashboard"))
        self._set_label(self.CONTROL_SUBTITLE, self.info.get("subtitle", "Choose an action"))

        self._set_label(self.CONTROL_BACKUP_COUNT, self.info.get("backup_count", "Backups Available: 0"))
        self._set_label(self.CONTROL_STORED_SIZE, self.info.get("stored_size", "Stored Size: 0 B"))
        self._set_label(self.CONTROL_LAST_BACKUP, self.info.get("last_backup", "Last Backup: No backup yet"))
        self._set_label(self.CONTROL_LOCATION, self.info.get("location", "Location: Unknown"))
        self._set_label(self.CONTROL_SCHEDULER, self.info.get("scheduler", "Scheduler: Disabled"))

        self._populate_action_list()
        self._update_description()

    def onClick(self, controlId):
        if controlId == self.CONTROL_ACTION_LIST:
            self._select_current_action()

    def onAction(self, action):
        action_id = action.getId()

        if action_id in BACK_ACTIONS:
            self.selected_action = None
            self.close()
            return

        if action_id in SELECT_ACTIONS:
            try:
                if self.getFocusId() == self.CONTROL_ACTION_LIST:
                    self._select_current_action()
                    return
            except Exception:
                pass

        if action_id in NAV_ACTIONS:
            self._update_description()

    def _set_label(self, control_id, text):
        try:
            self.getControl(control_id).setLabel(str(text))
        except Exception:
            pass

    def _set_text(self, control_id, text):
        try:
            self.getControl(control_id).setText(str(text))
        except Exception:
            pass

    def _populate_action_list(self):
        try:
            list_control = self.getControl(self.CONTROL_ACTION_LIST)
            list_control.reset()

            for item in self.menu_items:
                action_id = item.get("action", "")
                desc = self.action_descriptions.get(action_id, "Open this section.")
                list_item = xbmcgui.ListItem(label=item.get("label", "Action"), label2=desc)
                list_control.addItem(list_item)

            if self.menu_items:
                list_control.selectItem(0)
                self.setFocusId(self.CONTROL_ACTION_LIST)
        except Exception:
            pass

    def _update_description(self):
        try:
            list_control = self.getControl(self.CONTROL_ACTION_LIST)
            selected_pos = list_control.getSelectedPosition()
            if not (0 <= selected_pos < len(self.menu_items)):
                self._set_text(self.CONTROL_DESCRIPTION, "")
                return

            action_id = self.menu_items[selected_pos].get("action", "")
            action_label = self.menu_items[selected_pos].get("label", "Action")
            action_desc = self.action_descriptions.get(action_id, "Open this section.")
            action_hint = self.action_hints.get(action_id, "")

            lines = [
                f"[COLOR FF4FC3F7][B]{action_label}[/B][/COLOR]",
                "[COLOR FFB0BEC5]------------------------------------------------------------[/COLOR]",
                action_desc,
            ]

            if action_hint:
                lines.extend(["", f"[COLOR FF80CBC4]{action_hint}[/COLOR]"])

            self._set_text(self.CONTROL_DESCRIPTION, "\n".join(lines))
        except Exception:
            pass

    def _select_current_action(self):
        try:
            list_control = self.getControl(self.CONTROL_ACTION_LIST)
            selected_pos = list_control.getSelectedPosition()
            if 0 <= selected_pos < len(self.menu_items):
                self.selected_action = self.menu_items[selected_pos].get("action")
            else:
                self.selected_action = None
        except Exception:
            self.selected_action = None

        self.close()


class CustomBackupBrowserWindow(xbmcgui.WindowXMLDialog):
    """Custom backup browser window for restore/view flows."""

    CONTROL_BACKUP_LIST = 1000
    CONTROL_TITLE = 1100
    CONTROL_SUBTITLE = 1101
    CONTROL_DETAILS = 2100
    CONTROL_COUNTER = 2200

    def __init__(self, *args, **kwargs):
        self.backups = []
        self.mode = "view"
        self.addon_name = ""
        self.selected_index = None

    def set_data(self, backups, mode, addon_name):
        self.backups = backups or []
        self.mode = mode or "view"
        self.addon_name = addon_name or ""

    def onInit(self):
        mode_title = "Restore Backup" if self.mode == "restore" else "Browse Backups"
        mode_subtitle = "Select a backup to restore" if self.mode == "restore" else "Select a backup to inspect"

        self._set_label(self.CONTROL_TITLE, f"{self.addon_name} - {mode_title}" if self.addon_name else mode_title)
        self._set_label(self.CONTROL_SUBTITLE, mode_subtitle)

        self._populate_backup_list()
        self._update_details()

    def onClick(self, controlId):
        if controlId == self.CONTROL_BACKUP_LIST:
            self._select_current_backup()

    def onAction(self, action):
        action_id = action.getId()

        if action_id in BACK_ACTIONS:
            self.selected_index = None
            self.close()
            return

        if action_id in SELECT_ACTIONS:
            try:
                if self.getFocusId() == self.CONTROL_BACKUP_LIST:
                    self._select_current_backup()
                    return
            except Exception:
                pass

        if action_id in NAV_ACTIONS:
            self._update_details()

    def _set_label(self, control_id, text):
        try:
            self.getControl(control_id).setLabel(str(text))
        except Exception:
            pass

    def _set_text(self, control_id, text):
        try:
            self.getControl(control_id).setText(str(text))
        except Exception:
            pass

    def _populate_backup_list(self):
        try:
            list_control = self.getControl(self.CONTROL_BACKUP_LIST)
            list_control.reset()

            for entry in self.backups:
                label = entry.get("display", entry.get("name", "Backup"))
                label2 = entry.get("size", "")
                item = xbmcgui.ListItem(label=label, label2=label2)
                list_control.addItem(item)

            if self.backups:
                list_control.selectItem(0)
                self.setFocusId(self.CONTROL_BACKUP_LIST)

            self._set_label(self.CONTROL_COUNTER, f"Backups Found: {len(self.backups)}")
        except Exception:
            pass

    def _update_details(self):
        try:
            list_control = self.getControl(self.CONTROL_BACKUP_LIST)
            selected_pos = list_control.getSelectedPosition()
            if not (0 <= selected_pos < len(self.backups)):
                return

            entry = self.backups[selected_pos]
            lines = [
                "[COLOR FF4FC3F7][B]Backup Overview[/B][/COLOR]",
                "[COLOR FFB0BEC5]------------------------------------------------------------[/COLOR]",
                f"[COLOR FF90CAF9]Name:[/COLOR] {entry.get('name', 'Unknown')}",
                f"[COLOR FF90CAF9]Date:[/COLOR] {entry.get('date', 'Unknown date')}",
                f"[COLOR FF90CAF9]Size:[/COLOR] {entry.get('size', 'Unknown size')}",
            ]

            if entry.get("location"):
                lines.append(f"[COLOR FF90CAF9]Location:[/COLOR] {entry.get('location')}")

            if entry.get("extra"):
                lines.append("")
                lines.append("[COLOR FFFFD54F][B]Extra[/B][/COLOR]")
                lines.append("[COLOR FFB0BEC5]------------------------------------------------------------[/COLOR]")
                lines.append(str(entry.get("extra")))

            self._set_text(self.CONTROL_DETAILS, "\n".join(lines))
        except Exception:
            pass

    def _select_current_backup(self):
        try:
            list_control = self.getControl(self.CONTROL_BACKUP_LIST)
            selected_pos = list_control.getSelectedPosition()
            if 0 <= selected_pos < len(self.backups):
                self.selected_index = selected_pos
            else:
                self.selected_index = None
        except Exception:
            self.selected_index = None

        self.close()


class CustomSettingsWindow(xbmcgui.WindowXMLDialog):
    """Custom settings window that renders `resources/settings.xml` and
    allows editing common setting types from inside the add-on UI.
    """

    CONTROL_CAT_LIST = 1000
    CONTROL_SETTINGS_LIST = 1001
    CONTROL_TITLE = 1100
    CONTROL_SUBTITLE = 1101
    CONTROL_DETAILS = 2100
    CONTROL_COUNTER = 2200

    def __init__(self, *args, **kwargs):
        self.categories = []
        self.current_cat = 0
        self.addon = None
        self._last_setting_activation_key = None
        self._last_setting_activation_ts = 0.0

    def onInit(self):
        try:
            self.addon = xbmcaddon.Addon()
            self._set_label(self.CONTROL_TITLE, f"{self.addon.getAddonInfo('name')} - Settings")
            self._set_label(self.CONTROL_SUBTITLE, "Professional configuration dashboard")

            self._load_settings()
            self._populate_categories(selected_index=0)
            
            if self.categories:
                self._populate_settings(0, selected_index=0)
                self.current_cat = 0
            
            self._clear_details()
            self.setFocusId(self.CONTROL_CAT_LIST)
        except Exception as e:
            xbmc.log(f"CustomSettings: Error in onInit: {str(e)}", xbmc.LOGERROR)

    def onClick(self, controlId):
        if controlId == self.CONTROL_CAT_LIST:
            self._activate_selected_category(move_focus_to_settings=True)
        elif controlId == self.CONTROL_SETTINGS_LIST:
            self._on_setting_click()

    def onAction(self, action):
        action_id = action.getId()
        
        # Back button closes the window
        if action_id in BACK_ACTIONS:
            self.close()
            return
        
        # Select/Enter button
        if action_id in SELECT_ACTIONS:
            # Activation for category/settings controls is handled in onClick.
            # This avoids double-trigger behavior where Enter fires both onAction
            # and onClick, causing popups/actions to run twice.
            return
        
        # Navigation actions
        if action_id in NAV_ACTIONS:
            try:
                focus_id = self.getFocusId()
            except Exception:
                focus_id = None

            # Left/Right always switches category exactly one step.
            if action_id in (1, 2):
                if focus_id == self.CONTROL_SETTINGS_LIST:
                    # Settings list keeps focus and changes category manually.
                    direction = 1 if action_id == 2 else -1
                    self._move_category(direction, keep_settings_focus=True)
                elif focus_id == self.CONTROL_CAT_LIST:
                    # Category tab list already handles left/right movement via XML navigation.
                    # Only sync the settings panel to the newly selected tab.
                    self._activate_selected_category(move_focus_to_settings=False)
                return

            # Down from tabs enters the settings list.
            if action_id == 4 and focus_id == self.CONTROL_CAT_LIST:
                self._activate_selected_category(move_focus_to_settings=True)
                return
        
        # Update details when navigating within settings
        try:
            if self.getFocusId() == self.CONTROL_SETTINGS_LIST:
                self._update_details()
        except Exception:
            pass

    def _set_label(self, control_id, text):
        try:
            self.getControl(control_id).setLabel(str(text))
        except Exception:
            pass

    def _set_text(self, control_id, text):
        try:
            self.getControl(control_id).setText(str(text))
        except Exception:
            pass

    def _load_settings(self):
        try:
            addon_path = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))
            settings_file = os.path.join(addon_path, 'resources', 'settings.xml')
            self.categories = []

            tree = ET.parse(settings_file)
            root = tree.getroot()

            for cat in root.findall('category'):
                category_label_id = cat.attrib.get('label', '')
                try:
                    label_text = self.addon.getLocalizedString(int(category_label_id))
                except Exception:
                    label_text = category_label_id

                settings_list = []
                for setting in cat.findall('setting'):
                    stype = setting.attrib.get('type', 'text')
                    if stype in ('lsep', 'sep'):
                        # skip separators
                        continue

                    sid = setting.attrib.get('id')
                    setting_label_id = setting.attrib.get('label', '')
                    try:
                        s_label = self.addon.getLocalizedString(int(setting_label_id))
                    except Exception:
                        s_label = setting_label_id

                    s = {
                        'id': sid,
                        'type': stype,
                        'label': s_label,
                        'values': setting.attrib.get('values'),
                        'default': setting.attrib.get('default'),
                        'format': setting.attrib.get('format'),
                        'action': setting.attrib.get('action'),
                        'option': setting.attrib.get('option'),
                        'range': setting.attrib.get('range'),
                        'enable': setting.attrib.get('enable'),
                        'visible': setting.attrib.get('visible'),
                    }

                    # read current value when available
                    try:
                        if sid:
                            s['value'] = self.addon.getSetting(sid)
                        else:
                            s['value'] = None
                    except Exception:
                        s['value'] = None

                    settings_list.append(s)

                self.categories.append({
                    'label': label_text,
                    'label_id': str(category_label_id),
                    'settings': settings_list,
                })
        except Exception as e:
            xbmc.log(f"CustomSettings: Failed to load settings.xml: {str(e)}", xbmc.LOGERROR)
            self.categories = []

    def _is_credits_category(self, cat_index=None):
        """Return True when current category is Credits (label id 32005)."""
        try:
            idx = self.current_cat if cat_index is None else int(cat_index)
            if not (0 <= idx < len(self.categories)):
                return False
            return str(self.categories[idx].get('label_id', '')) == '32005'
        except Exception:
            return False

    def _is_credits_setting(self, setting_obj):
        """Return True for information-only fields in Credits."""
        try:
            sid = str((setting_obj or {}).get('id') or '')
            return sid in {'attribution', 'fanart_attribution', 'author', 'version'}
        except Exception:
            return False

    def _is_read_only_setting(self, setting_obj):
        """Return True for settings that should not be editable in custom UI."""
        try:
            if self._is_credits_setting(setting_obj):
                return True

            enable_expr = str((setting_obj or {}).get('enable') or '').strip().lower()
            return enable_expr in {'false', '0'}
        except Exception:
            return False

    def _populate_categories(self, selected_index=0):
        try:
            list_control = self.getControl(self.CONTROL_CAT_LIST)
            list_control.reset()
            for cat in self.categories:
                list_control.addItem(xbmcgui.ListItem(label=cat.get('label', '')))

            if self.categories:
                safe_index = selected_index if 0 <= selected_index < len(self.categories) else 0
                list_control.selectItem(safe_index)
                self.current_cat = safe_index
        except Exception:
            pass

    def _populate_settings(self, cat_index, selected_index=0):
        try:
            if not (0 <= cat_index < len(self.categories)):
                return
            
            self.current_cat = cat_index
            settings = self.categories[cat_index]['settings']
            is_credits = self._is_credits_category(cat_index)
            
            list_control = self.getControl(self.CONTROL_SETTINGS_LIST)
            list_control.reset()

            for s in settings:
                label = s.get('label', '')
                value = '' if is_credits else self._format_display_value(s)
                item = xbmcgui.ListItem(label=label, label2=value)
                list_control.addItem(item)

            # Update counter
            try:
                self._set_label(self.CONTROL_COUNTER, f"Settings: {len(settings)}")
            except Exception:
                pass
                
            # Keep a safe selected row after category changes.
            if len(settings) > 0:
                safe_index = selected_index if 0 <= selected_index < len(settings) else 0
                list_control.selectItem(safe_index)
        except Exception as e:
            xbmc.log(f"CustomSettings: Error in _populate_settings: {str(e)}", xbmc.LOGWARNING)

    def _move_category(self, direction, keep_settings_focus=False):
        try:
            if not self.categories:
                return

            tab_control = self.getControl(self.CONTROL_CAT_LIST)
            current_tab = tab_control.getSelectedPosition()
            if current_tab < 0:
                current_tab = self.current_cat

            selected_setting_index = 0
            if keep_settings_focus:
                try:
                    selected_setting_index = self.getControl(self.CONTROL_SETTINGS_LIST).getSelectedPosition()
                    if selected_setting_index < 0:
                        selected_setting_index = 0
                except Exception:
                    selected_setting_index = 0

            next_tab = (current_tab + direction) % len(self.categories)
            tab_control.selectItem(next_tab)
            self._populate_settings(next_tab, selected_index=selected_setting_index)

            if keep_settings_focus:
                self.setFocusId(self.CONTROL_SETTINGS_LIST)
                self._update_details()
            else:
                self.setFocusId(self.CONTROL_CAT_LIST)
                self._clear_details()
        except Exception as e:
            xbmc.log(f"CustomSettings: Error in _move_category: {str(e)}", xbmc.LOGWARNING)

    def _activate_selected_category(self, move_focus_to_settings=True):
        try:
            tab_control = self.getControl(self.CONTROL_CAT_LIST)
            pos = tab_control.getSelectedPosition()
            if not (0 <= pos < len(self.categories)):
                return

            self.current_cat = pos
            self._populate_settings(pos, selected_index=0)

            if move_focus_to_settings:
                self.setFocusId(self.CONTROL_SETTINGS_LIST)
                self._update_details()
            else:
                self.setFocusId(self.CONTROL_CAT_LIST)
                self._clear_details()
        except Exception as e:
            xbmc.log(f"CustomSettings: Error in _activate_selected_category: {str(e)}", xbmc.LOGWARNING)

    def _format_display_value(self, s):
        """Return a user-friendly display string for a setting dict."""
        try:
            sid = s.get('id')
            stype = s.get('type')
            raw = ''
            if sid:
                try:
                    raw = self.addon.getSetting(sid)
                except Exception:
                    raw = s.get('value') or ''
                if stype == 'slider' and (raw is None or str(raw) == ''):
                    raw = s.get('default') or raw
            else:
                raw = s.get('value') or ''

            # Actions: show a friendly hint rather than 'Not set'
            if stype == 'action':
                return 'Run'

            if stype == 'bool':
                return 'Enabled' if str(raw).lower() in ('true', '1') else 'Disabled'

            if stype == 'enum':
                vals = s.get('values') or ''
                vals_list = vals.split('|') if vals else []
                try:
                    idx = int(raw)
                    return vals_list[idx] if 0 <= idx < len(vals_list) else (raw or '')
                except Exception:
                    return raw or (vals_list[0] if vals_list else '')

            if stype == 'slider':
                fmt = s.get('format') or ''
                try:
                    value_num = int(float(raw))
                except Exception:
                    value_num = raw

                if fmt and '%d' in fmt:
                    try:
                        return fmt % int(value_num)
                    except Exception:
                        pass
                return str(value_num)

            # Passwords should not display the secret; indicate set/unset
            if stype == 'password':
                return 'Set' if raw else 'Not set'

            # default: show raw value, or 'Not set' when empty
            return raw if raw else 'Not set'
        except Exception:
            return ''

    def _get_setting_help(self, s):
        """Return short, user-friendly help text for a setting."""
        sid = str(s.get('id') or '')
        stype = str(s.get('type') or '')

        help_map = {
            'enable_verbose_logging': 'Writes extra diagnostic logs to help troubleshoot issues.',
            'backup_location_type': 'Choose whether backups are saved locally or to remote storage.',
            'backup_location': 'Folder where local backup ZIP files are stored.',
            'compression_level': 'Higher levels compress more but can take longer.',
            'enable_rotation': 'Automatically deletes older backups based on your rotation rule.',
            'backup_rotation': 'Choose which older backups are kept during rotation.',
            'max_backups': 'Maximum number of backups to keep before cleanup runs.',
            'remote_location_type': 'Select the remote protocol used for backup storage.',
            'remote_path': 'Server path or URL where remote backups are stored.',
            'browse_remote': 'Open remote browser to select and verify the remote path.',
            'remote_username': 'Username used to sign in to remote storage.',
            'remote_password': 'Password used for remote storage authentication.',
            'remote_port': 'Network port for remote storage. Use 0 for protocol default.',
            'test_connection': 'Checks remote access using the current remote settings.',
            'backup_configs': 'Include Kodi and LibreELEC configuration files in backups.',
            'backup_addons': 'Include installed add-ons in the backup.',
            'backup_userdata': 'Include userdata such as add-on settings and databases.',
            'backup_repositories': 'Include repository add-ons so sources can be restored quickly.',
            'backup_sources': 'Include your media source definitions and source files.',
            'backup_now': 'Start a backup immediately using current selections.',
            'restore_backup': 'Restore files from a selected backup archive.',
            'view_backups': 'Browse existing backups and inspect their details.',
            'enable_scheduler': 'Turn automatic scheduled backups on or off.',
            'run_missed_backups': 'Run missed backups after downtime or reboot.',
            'schedule_type': 'Choose how often scheduled backups should run.',
            'schedule_time': 'Set the time of day for scheduled backups.',
            'schedule_day': 'Pick the weekday used for weekly backups.',
            'schedule_date': 'Pick the calendar date used for monthly backups.',
            'show_notifications': 'Show on-screen notifications for backup events.',
            'detailed_notifications': 'Show more progress details in notifications.',
            'show_backup_summary_popup': 'Show a detailed summary popup after successful backups.',
            'enable_reminders': 'Enable reminder notifications before scheduled backups.',
            'reminder_1hour': 'Show reminder 1 hour before the scheduled backup.',
            'reminder_30min': 'Show reminder 30 minutes before the scheduled backup.',
            'reminder_10min': 'Show reminder 10 minutes before the scheduled backup.',
            'reminder_1min': 'Show reminder 1 minute before the scheduled backup.',
            'enable_email': 'Send backup and restore notifications by email.',
            'smtp_server': 'SMTP server hostname for outgoing email.',
            'smtp_port': 'SMTP server port used for sending mail.',
            'smtp_username': 'SMTP account username for authentication.',
            'smtp_password': 'SMTP account password for authentication.',
            'smtp_from': 'Sender email address shown in notifications.',
            'smtp_to': 'Recipient email address for notifications.',
            'smtp_use_tls': 'Use TLS encryption when connecting to SMTP server.',
            'test_email': 'Send a test email to verify email settings.',
            'attribution': 'Credits text for icon artwork. Information only.',
            'fanart_attribution': 'Credits text for fanart source. Information only.',
            'author': 'Addon author information. Information only.',
            'version': 'Current addon version information. Information only.',
        }

        if sid in help_map:
            return help_map[sid]

        if self._is_credits_category():
            return 'Information only. This entry is not editable.'

        type_help = {
            'bool': 'Toggle this setting on or off.',
            'enum': 'Choose one option from the available list.',
            'slider': 'Adjust this numeric value within the allowed range.',
            'action': 'Run this action using the current settings.',
            'folder': 'Select a folder path used by this setting.',
            'text': 'Enter text for this setting.',
            'password': 'Enter a value securely. The text is hidden.',
            'number': 'Enter a numeric value.',
            'time': 'Set a time value for this setting.',
        }
        return type_help.get(stype, 'Adjust this setting to match your backup workflow.')

    def _get_options_preview(self, values_csv):
        """Return a compact preview string for enum options."""
        values = [v.strip() for v in str(values_csv or '').split('|') if v.strip()]
        if not values:
            return ''
        if len(values) <= 6:
            return ', '.join(values)
        return ', '.join(values[:6]) + ', ...'

    def _on_category_click(self):
        self._activate_selected_category(move_focus_to_settings=True)

    def _is_duplicate_setting_activation(self, setting_pos):
        """Ignore immediate duplicate Enter/click events for the same setting."""
        try:
            key = (self.current_cat, int(setting_pos))
        except Exception:
            key = (self.current_cat, -1)

        now = time.monotonic()
        is_duplicate = (
            self._last_setting_activation_key == key and
            (now - self._last_setting_activation_ts) < 0.35
        )

        self._last_setting_activation_key = key
        self._last_setting_activation_ts = now
        return is_duplicate

    def _on_setting_click(self):
        try:
            list_control = self.getControl(self.CONTROL_SETTINGS_LIST)
            pos = list_control.getSelectedPosition()
            settings = self.categories[self.current_cat]['settings']
            if 0 <= pos < len(settings):
                setting_obj = settings[pos]
                if self._is_credits_category() or self._is_read_only_setting(setting_obj):
                    # Credits and explicitly disabled settings are informational only.
                    self._update_details()
                    return
                if self._is_duplicate_setting_activation(pos):
                    return
                self._edit_setting(setting_obj)
                # reload settings and refresh UI
                self._load_settings()
                self._populate_categories(selected_index=self.current_cat)
                self._populate_settings(self.current_cat, selected_index=pos)
                self.setFocusId(self.CONTROL_SETTINGS_LIST)
                self._update_details()
        except Exception:
            pass

    def _update_details(self):
        try:
            list_control = self.getControl(self.CONTROL_SETTINGS_LIST)
            pos = list_control.getSelectedPosition()
            settings = self.categories[self.current_cat]['settings']
            if not (0 <= pos < len(settings)):
                return

            s = settings[pos]
            is_credits = self._is_credits_category() or self._is_credits_setting(s)
            is_read_only = is_credits or self._is_read_only_setting(s)
            current = self._format_display_value(s) if not is_credits else 'Information'
            help_text = self._get_setting_help(s)
            lines = [f"[COLOR FF4FC3F7][B]{s.get('label','Setting')}[/B][/COLOR]",
                     "[COLOR FFB0BEC5]------------------------------------------------------------[/COLOR]",
                     f"What this does: {help_text}",
                     "",
                     f"Current value: {current}"]

            vals = s.get('values')
            if vals:
                options_preview = self._get_options_preview(vals)
                lines.append("")
                lines.append(f"[COLOR FF90CAF9]Options:[/COLOR] {options_preview}")

            lines.extend([
                "",
                "[COLOR FF9CB5C8]Controls:[/COLOR]",
                "- Enter: Edit selected setting" if not is_read_only else "- Enter: No action (information only)",
                "- Left/Right: Switch category",
                "- Up/Down: Switch between items",
            ])

            self._set_text(self.CONTROL_DETAILS, "\n".join(lines))
        except Exception:
            pass

    def _clear_details(self):
        """Clear the details pane when going back to category list."""
        try:
            self._set_text(self.CONTROL_DETAILS, "")
        except Exception:
            pass

    def _edit_setting(self, s):
        try:
            sid = s.get('id')
            stype = s.get('type')
            if stype == 'bool' and sid:
                cur = str(self.addon.getSetting(sid)).lower() == 'true'
                new = 'false' if cur else 'true'
                self.addon.setSetting(sid, new)
                xbmc.executebuiltin('XBMC.Notification(Setting Updated, {})'.format(s.get('label')))
                return

            if stype == 'enum' and sid:
                vals = s.get('values') or ''
                vals_list = vals.split('|') if vals else []
                try:
                    cur = int(self.addon.getSetting(sid))
                except Exception:
                    cur = 0
                sel = xbmcgui.Dialog().select(s.get('label'), vals_list)
                if sel != -1:
                    # try storing index; some Kodi versions accept the label instead
                    try:
                        self.addon.setSetting(sid, str(sel))
                    except Exception:
                        try:
                            self.addon.setSetting(sid, vals_list[sel])
                        except Exception:
                            pass
                return

            if stype in ('text', 'number', 'time', 'folder', 'password') and sid:
                cur = self.addon.getSetting(sid) or ''
                kb = xbmc.Keyboard(cur, f"Enter value for {s.get('label')}")
                kb.doModal()
                if kb.isConfirmed():
                    val = kb.getText()
                    try:
                        self.addon.setSetting(sid, val)
                    except Exception:
                        pass
                return

            if stype == 'slider' and sid:
                cur_raw = self.addon.getSetting(sid) or s.get('default') or '0'
                try:
                    cur_value = int(float(cur_raw))
                except Exception:
                    cur_value = 0

                # Use a simple list selector for max backups to improve reliability.
                if sid == 'max_backups':
                    options = [str(i) for i in range(1, 11)]
                    preselect = min(max(cur_value, 1), 10) - 1
                    heading = f"{s.get('label')} (1-10)"
                    try:
                        sel = xbmcgui.Dialog().select(heading, options, 0, preselect)
                    except Exception:
                        sel = xbmcgui.Dialog().select(heading, options)

                    if sel == -1:
                        return

                    snapped = int(options[sel])
                    saved = False
                    try:
                        if hasattr(self.addon, 'setSettingInt'):
                            self.addon.setSettingInt(sid, snapped)
                            saved = True
                    except Exception:
                        saved = False

                    if not saved:
                        try:
                            self.addon.setSetting(sid, str(snapped))
                            saved = True
                        except Exception:
                            saved = False

                    if saved:
                        try:
                            xbmc.executebuiltin('UpdateLocalAddons')
                        except Exception:
                            pass
                        try:
                            self.addon = xbmcaddon.Addon()
                        except Exception:
                            pass
                    return

                range_raw = s.get('range') or ''
                min_value, step_value, max_value = 0, 1, 100
                try:
                    range_parts = [p.strip() for p in range_raw.split(',') if p.strip()]
                    if len(range_parts) >= 3:
                        min_value = int(float(range_parts[0]))
                        step_value = int(float(range_parts[1]))
                        max_value = int(float(range_parts[2]))
                except Exception:
                    pass

                heading = f"{s.get('label')} ({min_value}-{max_value})"
                entered = xbmcgui.Dialog().numeric(0, heading, str(cur_value))
                if entered is not None and str(entered).strip() != '':
                    try:
                        new_value = int(float(entered))
                    except Exception:
                        new_value = cur_value

                    if step_value <= 0:
                        step_value = 1

                    if new_value < min_value:
                        new_value = min_value
                    if new_value > max_value:
                        new_value = max_value

                    # Snap to configured step from min_value.
                    snapped = min_value + (((new_value - min_value) + (step_value // 2)) // step_value) * step_value
                    if snapped < min_value:
                        snapped = min_value
                    if snapped > max_value:
                        snapped = max_value

                    saved = False
                    try:
                        if hasattr(self.addon, 'setSettingInt'):
                            self.addon.setSettingInt(sid, int(snapped))
                            saved = True
                    except Exception:
                        saved = False

                    if not saved:
                        try:
                            self.addon.setSetting(sid, str(snapped))
                            saved = True
                        except Exception:
                            saved = False

                    if saved:
                        try:
                            xbmc.executebuiltin('UpdateLocalAddons')
                        except Exception:
                            pass
                        try:
                            # Refresh handle so follow-up reads reflect the saved value.
                            self.addon = xbmcaddon.Addon()
                        except Exception:
                            pass
                return

            if stype == 'action' and s.get('action'):
                # actions in settings.xml are executable strings that can be passed to executebuiltin
                try:
                    xbmc.executebuiltin(s.get('action'))
                except Exception:
                    xbmc.executebuiltin(s.get('action') or '')
                return

            # fallback: show a simple info dialog
            show_message(self.addon.getAddonInfo('name'), f"Cannot edit setting type: {stype}")
        except Exception as e:
            xbmc.log(f"CustomSettings: Failed editing setting: {str(e)}", xbmc.LOGERROR)


class CustomMessageWindow(xbmcgui.WindowXMLDialog):
    """Simple scrollable message window used instead of xbmcgui.Dialog().textviewer/ok."""

    CONTROL_TITLE = 1100
    CONTROL_TEXT = 2100
    CONTROL_CLOSE = 2201

    def __init__(self, *args, **kwargs):
        self.title = ''
        self.text = ''

    def set_data(self, title, text):
        self.title = title or ''
        self.text = text or ''

    def onInit(self):
        try:
            self.getControl(self.CONTROL_TITLE).setLabel(str(self.title))
        except Exception:
            pass
        try:
            self.getControl(self.CONTROL_TEXT).setText(str(self.text))
        except Exception:
            pass

    def onAction(self, action):
        # Close on any back/ok action
        try:
            if action.getId() in BACK_ACTIONS | SELECT_ACTIONS:
                self.close()
        except Exception:
            pass

    def onClick(self, controlId):
        try:
            if controlId == self.CONTROL_CLOSE:
                self.close()
        except Exception:
            pass


class CustomConfirmWindow(xbmcgui.WindowXMLDialog):
    """Modal yes/no confirm window that returns True for yes, False for no."""

    CONTROL_TITLE = 1100
    CONTROL_TEXT = 2100
    CONTROL_YES = 2201
    CONTROL_NO = 2202

    def __init__(self, *args, **kwargs):
        self.title = ''
        self.text = ''
        self.yes_label = 'Yes'
        self.no_label = 'No'
        self.result = False

    def set_data(self, title, text, yes_label='Yes', no_label='No'):
        self.title = title or ''
        self.text = text or ''
        self.yes_label = yes_label or 'Yes'
        self.no_label = no_label or 'No'

    def onInit(self):
        try:
            self.getControl(self.CONTROL_TITLE).setLabel(str(self.title))
        except Exception:
            pass
        try:
            self.getControl(self.CONTROL_TEXT).setText(str(self.text))
        except Exception:
            pass
        try:
            self.getControl(self.CONTROL_YES).setLabel(self.yes_label)
        except Exception:
            pass
        try:
            self.getControl(self.CONTROL_NO).setLabel(self.no_label)
        except Exception:
            pass
        try:
            self.setFocusId(self.CONTROL_YES)
        except Exception:
            pass

    def onClick(self, controlId):
        try:
            if controlId == self.CONTROL_YES:
                self.result = True
                self.close()
            elif controlId == self.CONTROL_NO:
                self.result = False
                self.close()
        except Exception:
            pass

    def onAction(self, action):
        try:
            aid = action.getId()
            if aid in BACK_ACTIONS:
                self.result = False
                self.close()
            if aid in SELECT_ACTIONS:
                try:
                    focus_id = self.getFocusId()
                except Exception:
                    focus_id = self.CONTROL_YES

                self.result = (focus_id != self.CONTROL_NO)
                self.close()
        except Exception:
            pass


def show_textviewer(title, text):
    """Show a scrollable text viewer using the custom GUI when available."""
    try:
        win = CustomMessageWindow('custom_message.xml', xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'default', '1080i')
        win.set_data(title, text)
        win.doModal()
        del win
    except Exception:
        try:
            xbmcgui.Dialog().textviewer(title, text)
        except Exception:
            xbmc.log(f"CustomMessage: Failed to show message: {title}")


def show_message(title, text):
    """Show a simple message using the custom GUI when available (OK only)."""
    show_textviewer(title, text)


def ask_yesno(title, text, yes_label='Yes', no_label='No'):
    """Ask a yes/no question using the custom GUI when available. Returns True on yes."""
    try:
        win = CustomConfirmWindow('custom_confirm.xml', xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path')), 'default', '1080i')
        win.set_data(title, text, yes_label=yes_label, no_label=no_label)
        win.doModal()
        result = getattr(win, 'result', False)
        del win
        return result
    except Exception:
        try:
            return xbmcgui.Dialog().yesno(title, text, nolabel=no_label, yeslabel=yes_label)
        except Exception:
            xbmc.log(f"CustomConfirm: Failed to show confirm: {title}")
            return False
