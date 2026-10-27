# LibreELEC Backupper v1.5.2 (2026-10-27)

## Added

- Added an optional Kodi video database backup setting to preserve watched status and resume positions.
- Automatically finds the installed `MyVideosN.db`, including after Kodi database version upgrades.
- Creates a consistent snapshot through SQLite's online backup API while Kodi is running; committed write-ahead log (WAL) data is included in the snapshot.
- Stores the snapshot in the existing backup ZIP at `userdata/Database/MyVideosN.db`.

## Restore safety

- Validates the SQLite database before replacing a file.
- Skips restore when a database of the same or a newer version already exists, preserving the installed database.
- Uses a staged file and atomic replacement for the database restore.

Enable **Kodi Video Database (resume points)** in the add-on's **Backup Items** settings to include it in local or remote backups.
