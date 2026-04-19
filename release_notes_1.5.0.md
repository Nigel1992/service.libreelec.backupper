# LibreELEC Backupper v1.5.0 - Feature Release (2026-04-12)

## Compared to v1.4.1.7

This release focuses on a major UX refresh, clearer settings guidance, and stronger reliability across backup flows.

## Added

- Full custom GUI suite with dedicated windows for:
  - Dashboard
  - Settings
  - Backup Browser
  - Confirm/Message dialogs
- 1080i and 720p skin coverage for key custom windows.
- Per-setting help text in custom settings details panel.
- Optional post-backup summary popup setting (`show_backup_summary_popup`).
- Dashboard remote storage status reporting (used/total/free when available).
- Additional WebDAV storage quota fallback detection methods.

## Changed

- Dashboard layout redesigned with clearer separation between:
  - Selection guidance
  - System status
- Settings navigation refined for predictable one-step category movement.
- Settings details panel now uses compact option previews to avoid text crowding.
- Operation summary display now prefers custom GUI style viewer when available.
- Popup handling now routes message/confirm/textviewer dialogs through custom GUI wrappers.
- Remote Settings Test Connection output now uses cleaner, consistent structured reports per protocol.

## Fixed

- Backup creation no longer blocked by empty default backup-item selection on first use.
- Enter key no longer triggers duplicate setting popups.
- Left/right category switching no longer skips two tabs in edge cases.
- Credits category entries are now strictly informational and non-editable.
- Up/down behavior in settings list now remains stable and item-by-item.

## Notes

- WebDAV servers vary in quota support; when full capacity is unavailable, dashboard falls back to known backup usage details.
- Local checker script `scripts/run-addon-check-local.sh` was not present in this repository during local validation runs.
