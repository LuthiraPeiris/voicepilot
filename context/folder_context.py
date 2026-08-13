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