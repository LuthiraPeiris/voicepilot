import os
from pathlib import Path
from security.permissions import request_permission

from database.database import find_folder


COMMON_FOLDERS = {
    "desktop": Path.home() / "Desktop",
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
}


def open_common_folder(folder_name):
    """
    Open common Windows user folders such as
    Desktop, Downloads, Documents, Pictures, Music, and Videos.
    """

    folder_name = folder_name.lower().strip()

    if folder_name not in COMMON_FOLDERS:
        return None

    path = COMMON_FOLDERS[folder_name]

    if path.exists():
        os.startfile(path)
        return f"Opening {folder_name}."

    return f"{folder_name} folder was not found."


def search_folder(folder_name):
    """
    Search for a folder using the SQLite folder index.
    """

    folder_name = folder_name.lower().strip()

    result = find_folder(folder_name)

    if not result:
        return None

    name, path = result

    folder_path = Path(path)

    # Make sure the folder still exists on the computer
    if folder_path.exists() and folder_path.is_dir():
        return folder_path

    return None


def open_folder(folder_name):
    """
    Open a folder.

    First checks common Windows folders.
    If it is not a common folder, search the SQLite folder index.
    """
    if not request_permission("open_folder"):
        return "Permission denied."

    folder_name = folder_name.lower().strip()

    # Check common Windows folders first
    common_result = open_common_folder(folder_name)

    if common_result:
        return common_result

    # Search SQLite folder index
    match = search_folder(folder_name)

    if match:
        try:
            os.startfile(match)
            return f"Opening {match}."

        except OSError:
            return f"I found {match}, but I couldn't open it."

    return f"I couldn't find a folder called {folder_name}."