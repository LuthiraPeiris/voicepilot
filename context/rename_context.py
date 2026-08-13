_pending_rename = None


def set_pending_rename(
    item_type,
    old_name,
):
    """
    Store a pending rename operation.

    item_type:
        "file" or "folder"

    old_name:
        Current name of the item.
    """

    global _pending_rename

    if item_type not in [
        "file",
        "folder",
    ]:
        return False

    old_name = old_name.strip()

    if not old_name:
        return False

    _pending_rename = {
        "type": item_type,
        "old_name": old_name,
    }

    return True


def get_pending_rename():
    """
    Return the current pending rename operation.
    """

    return _pending_rename


def has_pending_rename():
    """
    Check whether VoicePilot is waiting
    for a new file or folder name.
    """

    return _pending_rename is not None


def clear_pending_rename():
    """
    Clear the pending rename operation.
    """

    global _pending_rename

    _pending_rename = None