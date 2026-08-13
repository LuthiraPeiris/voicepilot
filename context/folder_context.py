from pathlib import Path


_current_folder = None


def set_current_folder(path):
    """
    Set the folder that VoicePilot should treat
    as the current working folder.
    """

    global _current_folder

    if path is None:
        _current_folder = None
        return

    folder_path = Path(path)

    if folder_path.exists() and folder_path.is_dir():
        _current_folder = folder_path


def get_current_folder():
    """
    Return the current working folder.
    """

    return _current_folder


def clear_current_folder():
    """
    Clear the current folder context.
    """

    global _current_folder

    _current_folder = None


def has_current_folder():
    """
    Check whether VoicePilot currently has
    an active folder context.
    """

    return _current_folder is not None


def go_to_parent_folder():
    """
    Move VoicePilot's current folder context
    one level up.

    Example:

    Downloads\\Example
    ->
    Downloads
    """

    global _current_folder

    if _current_folder is None:
        return None

    parent_folder = _current_folder.parent

    # Already at drive root.
    if parent_folder == _current_folder:
        return _current_folder

    if (
        parent_folder.exists()
        and parent_folder.is_dir()
    ):
        _current_folder = parent_folder

        return _current_folder

    return None


def get_current_folder_name():
    """
    Return only the name of the current folder.
    """

    if _current_folder is None:
        return None

    return _current_folder.name