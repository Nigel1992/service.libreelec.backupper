"""Helpers for the unified storage type setting."""

STORAGE_TYPES = ("Local", "SMB", "NFS", "FTP", "SFTP", "WebDAV")


def get_storage_type(addon):
    """Return the unified storage type, migrating pre-1.5.5 settings."""
    raw_value = addon.getSetting("backup_location_type") or "0"
    try:
        storage_type = int(raw_value)
    except (TypeError, ValueError):
        storage_type = 0

    # Before 1.5.5, 1 meant Remote and the protocol lived in a second setting.
    if storage_type == 1:
        try:
            legacy_type = int(addon.getSetting("remote_location_type") or "0")
        except (TypeError, ValueError):
            legacy_type = 0
        storage_type = legacy_type + 1
        addon.setSetting("backup_location_type", str(storage_type))

    return storage_type if 0 <= storage_type < len(STORAGE_TYPES) else 0
