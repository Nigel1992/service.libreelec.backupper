#!/usr/bin/python3
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui


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

    def _populate_action_list(self):
        try:
            list_control = self.getControl(self.CONTROL_ACTION_LIST)
            list_control.reset()

            for item in self.menu_items:
                list_item = xbmcgui.ListItem(label=item.get("label", "Action"), label2=item.get("description", ""))
                list_item.setProperty("description", item.get("description", ""))
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
            if 0 <= selected_pos < len(self.menu_items):
                description = self.menu_items[selected_pos].get("description", "")
                self._set_label(self.CONTROL_DESCRIPTION, description)
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
