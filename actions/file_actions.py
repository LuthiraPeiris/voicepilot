import os
import winreg
from pathlib import Path

from database.database import find_file
from security.permissions import request_permission


SHELL_FOLDER_REGISTRY_PATH = (
    r"Software\Microsoft\Windows\CurrentVersion"
    r"\Explorer\User Shell Folders"
)


WINDOWS_FOLDER_KEYS = {
    "desktop": "Desktop",
    "documents": "Personal",
    "pictures": "My Pictures",
    "music": "My Music",
    "videos": "My Video",
    "downloads": (
        "{374DE290-123F-4565-9164-39C4925E467B}"
    ),
}


def get_windows_folder(folder_name):
    """
    Get the actual Windows path for a common
    user folder.
    """

    folder_name = folder_name.lower().strip()

    registry_value = WINDOWS_FOLDER_KEYS.get(
        folder_name
    )

    if not registry_value:
        return None

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            SHELL_FOLDER_REGISTRY_PATH,
        ) as key:
            folder_path, _ = winreg.QueryValueEx(
                key,
                registry_value,
            )

        folder_path = os.path.expandvars(
            folder_path
        )

        return Path(folder_path)

    except (
        FileNotFoundError,
        OSError,
    ):
        return None


def resolve_location(location_name):
    """
    Resolve a common Windows folder name.
    """

    location_name = (
        location_name.lower().strip()
    )

    path = get_windows_folder(
        location_name
    )

    if path and path.exists():
        return path

    return None


def create_folder(
    folder_name,
    location="desktop",
):
    """
    Create a folder inside a Windows
    user location.
    """

    if not request_permission(
        "create_folder"
    ):
        return "Permission denied."

    folder_name = folder_name.strip()

    if not folder_name:
        return "Folder name cannot be empty."

    base_path = resolve_location(
        location
    )

    if not base_path:
        return (
            f"I couldn't find your "
            f"{location} folder."
        )

    folder_path = (
        base_path / folder_name
    )

    try:
        if folder_path.exists():
            return (
                f"A folder called "
                f"{folder_name} already "
                f"exists in {location}."
            )

        folder_path.mkdir()

        return (
            f"Created folder "
            f"{folder_name} "
            f"in {location}."
        )

    except OSError as error:
        print(
            f"Create folder error: "
            f"{error}"
        )

        return (
            f"I couldn't create the "
            f"folder {folder_name}."
        )


def open_file(file_name):
    """
    Search the VoicePilot file index and
    open the matching file using its default
    Windows application.
    """

    if not request_permission(
        "open_file"
    ):
        return "Permission denied."

    file_name = file_name.strip()

    if not file_name:
        return "File name cannot be empty."

    result = find_file(file_name)

    if not result:
        return (
            f"I couldn't find a file "
            f"called {file_name}."
        )

    name, extension, path = result

    file_path = Path(path)

    # Make sure the indexed file still exists
    if not file_path.exists():
        return (
            f"I found {name}{extension} "
            "in the index, but the file "
            "no longer exists."
        )

    if not file_path.is_file():
        return (
            f"{name}{extension} "
            "is not a file."
        )

    try:
        os.startfile(file_path)

        return (
            f"Opening "
            f"{name}{extension}."
        )

    except OSError as error:
        print(
            f"Open file error: {error}"
        )

        return (
            f"I found {name}{extension}, "
            "but I couldn't open it."
        )