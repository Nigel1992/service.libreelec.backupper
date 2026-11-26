# LibreELEC Backupper Release Notes - 1.5.6 (2026-11-26)

- Prevented backups from growing on every run by excluding the backup destination and accumulating directories (addon packages, caches, temp files, VCS metadata)
- Improved backup file collection for both single-file and directory backup items