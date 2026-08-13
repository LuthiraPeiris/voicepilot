import os
import winreg
from pathlib import Path

from context.folder_context import get_current_folder
from database.database import find_files
from security.permissions import request_permission
from send2trash import send2trash


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


# Files waiting for the user to choose between.
_pending_file_matches = []


def get_windows_folder(folder_name):
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
    location_name = (
        location_name.lower().strip()
    )

    path = get_windows_folder(
        location_name
    )

    if path and path.exists():
        return path

    return None


# ==================================================
# CREATE FOLDER
# ==================================================


def create_folder(
    folder_name,
    location=None,
):
    """
    Create a folder.

    If VoicePilot has a current working folder,
    the new folder is created there.

    Otherwise, Desktop is used by default.
    """

    if not request_permission(
        "create_folder"
    ):
        return "Permission denied."

    folder_name = folder_name.strip()

    if not folder_name:
        return "Folder name cannot be empty."

    current_folder = get_current_folder()

    if current_folder:
        base_path = current_folder
        location_label = current_folder.name

    else:
        if not location:
            location = "desktop"

        base_path = resolve_location(
            location
        )

        location_label = location

    if not base_path:
        return (
            f"I couldn't find your "
            f"{location_label} folder."
        )

    folder_path = (
        base_path / folder_name
    )

    try:
        if folder_path.exists():
            return (
                f"A folder called {folder_name} "
                f"already exists in "
                f"{location_label}."
            )

        folder_path.mkdir()

        return (
            f"Created folder {folder_name} "
            f"in {location_label}."
        )

    except OSError as error:
        print(
            f"Create folder error: {error}"
        )

        return (
            f"I couldn't create the folder "
            f"{folder_name}."
        )


# ==================================================
# CREATE FILE
# ==================================================


def create_file(file_name):
    """
    Create an empty file.

    If VoicePilot has a current working folder,
    the file is created there.

    Otherwise, Desktop is used.
    """

    if not request_permission(
        "create_file"
    ):
        return "Permission denied."

    file_name = file_name.strip()

    if not file_name:
        return "File name cannot be empty."

    current_folder = get_current_folder()

    if current_folder:
        base_path = current_folder
        location_label = current_folder.name

    else:
        base_path = resolve_location(
            "desktop"
        )

        location_label = "desktop"

    if not base_path:
        return (
            "I couldn't find a location "
            "to create the file."
        )

    file_path = (
        base_path / file_name
    )

    try:
        if file_path.exists():
            return (
                f"A file called {file_name} "
                f"already exists in "
                f"{location_label}."
            )

        file_path.touch()

        return (
            f"Created file {file_name} "
            f"in {location_label}."
        )

    except OSError as error:
        print(
            f"Create file error: {error}"
        )

        return (
            f"I couldn't create the file "
            f"{file_name}."
        )


# ==================================================
# SEARCH FILES INSIDE CURRENT FOLDER
# ==================================================


def find_files_in_current_folder(file_name):
    """
    Search only inside VoicePilot's current
    working folder.
    """

    current_folder = get_current_folder()

    if not current_folder:
        return []

    file_name = (
        file_name.lower().strip()
    )

    if not file_name:
        return []

    matches = []

    try:
        for item in current_folder.iterdir():

            if not item.is_file():
                continue

            stem = item.stem.lower()
            full_name = item.name.lower()

            normalized_stem = (
                stem.replace(
                    " ",
                    "",
                )
            )

            normalized_search = (
                file_name.replace(
                    " ",
                    "",
                )
            )

            # Exact full filename
            if full_name == file_name:
                matches.append(
                    (
                        item.stem,
                        item.suffix,
                        str(item),
                    )
                )
                continue

            # Exact name without extension
            if stem == file_name:
                matches.append(
                    (
                        item.stem,
                        item.suffix,
                        str(item),
                    )
                )
                continue

            # Ignore spaces
            if (
                normalized_stem
                == normalized_search
            ):
                matches.append(
                    (
                        item.stem,
                        item.suffix,
                        str(item),
                    )
                )
                continue

            # Partial match
            if file_name in stem:
                matches.append(
                    (
                        item.stem,
                        item.suffix,
                        str(item),
                    )
                )

    except (
        PermissionError,
        OSError,
    ):
        return []

    return matches[:5]


def find_file_in_current_folder(file_name):
    """
    Find one file inside the current folder.

    Returns:
    - matching file tuple
    - "MULTIPLE" if several match
    - None if nothing matches
    """

    matches = (
        find_files_in_current_folder(
            file_name
        )
    )

    if not matches:
        return None

    if len(matches) > 1:
        return "MULTIPLE"

    return matches[0]


# ==================================================
# SEARCH FOLDER INSIDE CURRENT FOLDER
# ==================================================


def find_folder_in_current_folder(
    folder_name,
):
    """
    Find a direct child folder inside the
    current working folder.
    """

    current_folder = get_current_folder()

    if not current_folder:
        return None

    folder_name = (
        folder_name.lower().strip()
    )

    try:
        for item in current_folder.iterdir():

            if (
                item.is_dir()
                and item.name.lower()
                == folder_name
            ):
                return item

    except (
        PermissionError,
        OSError,
    ):
        return None

    return None


# ==================================================
# RENAME FILE
# ==================================================


def rename_file(
    old_name,
    new_name,
):
    """
    Rename a file inside the current
    working folder.

    If the new filename has no extension,
    the old extension is preserved.
    """

    current_folder = get_current_folder()

    if not current_folder:
        return (
            "Open a folder first so I know "
            "which file you want to rename."
        )

    match = find_file_in_current_folder(
        old_name
    )

    if not match:
        return (
            f"I couldn't find a file called "
            f"{old_name} in "
            f"{current_folder.name}."
        )

    if match == "MULTIPLE":
        return (
            f"I found multiple files matching "
            f"{old_name}. "
            "Please be more specific."
        )

    name, extension, path = match

    old_path = Path(path)

    new_name = new_name.strip()

    if not new_name:
        return (
            "The new file name "
            "cannot be empty."
        )

    new_name_path = Path(
        new_name
    )

    # Preserve existing extension if the user
    # did not specify one.
    if (
        not new_name_path.suffix
        and extension
    ):
        new_name = (
            f"{new_name}{extension}"
        )

    target_path = (
        current_folder / new_name
    )

    if target_path.exists():
        return (
            f"A file called "
            f"{target_path.name} "
            "already exists."
        )

    allowed = request_permission(
        "rename_file",
        (
            f"Do you want me to rename "
            f"{old_path.name} to "
            f"{target_path.name}?"
        ),
    )

    if not allowed:
        return "Rename cancelled."

    try:
        old_name_for_response = (
            old_path.name
        )

        old_path.rename(
            target_path
        )

        return (
            f"Renamed {old_name_for_response} "
            f"to {target_path.name}."
        )

    except OSError as error:
        print(
            f"Rename file error: {error}"
        )

        return (
            f"I couldn't rename "
            f"{old_path.name}."
        )


# ==================================================
# RENAME FOLDER
# ==================================================


def rename_folder(
    old_name,
    new_name,
):
    """
    Rename a folder inside the current
    working folder.
    """

    current_folder = get_current_folder()

    if not current_folder:
        return (
            "Open a folder first so I know "
            "which folder you want to rename."
        )

    folder_path = (
        find_folder_in_current_folder(
            old_name
        )
    )

    if not folder_path:
        return (
            f"I couldn't find a folder "
            f"called {old_name} in "
            f"{current_folder.name}."
        )

    new_name = new_name.strip()

    if not new_name:
        return (
            "The new folder name "
            "cannot be empty."
        )

    target_path = (
        current_folder / new_name
    )

    if target_path.exists():
        return (
            f"A folder called "
            f"{new_name} already exists."
        )

    allowed = request_permission(
        "rename_folder",
        (
            f"Do you want me to rename "
            f"{folder_path.name} to "
            f"{new_name}?"
        ),
    )

    if not allowed:
        return "Rename cancelled."

    try:
        old_folder_name = (
            folder_path.name
        )

        folder_path.rename(
            target_path
        )

        return (
            f"Renamed folder "
            f"{old_folder_name} "
            f"to {target_path.name}."
        )

    except OSError as error:
        print(
            f"Rename folder error: {error}"
        )

        return (
            f"I couldn't rename the "
            f"{folder_path.name} folder."
        )


# ==================================================
# DELETE FILE
# ==================================================


def delete_file(file_name):
    """
    Move a file from the current working folder
    to the Windows Recycle Bin.
    """

    current_folder = get_current_folder()

    if not current_folder:
        return (
            "Open a folder first so I know "
            "which file you want to delete."
        )

    match = find_file_in_current_folder(
        file_name
    )

    if not match:
        return (
            f"I couldn't find a file called "
            f"{file_name} in "
            f"{current_folder.name}."
        )

    if match == "MULTIPLE":
        return (
            f"I found multiple files matching "
            f"{file_name} in "
            f"{current_folder.name}. "
            "Please be more specific."
        )

    name, extension, path = match

    file_path = Path(path)

    allowed = request_permission(
        "delete_file",
        (
            f"Do you want me to move "
            f"{name}{extension} "
            "to the Recycle Bin?"
        ),
    )

    if not allowed:
        return "Delete cancelled."

    try:
        send2trash(
            str(file_path)
        )

        return (
            f"Moved {name}{extension} "
            "to the Recycle Bin."
        )

    except Exception as error:
        print(
            f"Delete file error: {error}"
        )

        return (
            f"I couldn't delete "
            f"{name}{extension}."
        )


# ==================================================
# DELETE FOLDER
# ==================================================


def delete_folder(folder_name):
    """
    Move a folder from the current working folder
    to the Windows Recycle Bin.
    """

    current_folder = get_current_folder()

    if not current_folder:
        return (
            "Open a folder first so I know "
            "which folder you want to delete."
        )

    folder_path = (
        find_folder_in_current_folder(
            folder_name
        )
    )

    if not folder_path:
        return (
            f"I couldn't find a folder "
            f"called {folder_name} in "
            f"{current_folder.name}."
        )

    allowed = request_permission(
        "delete_folder",
        (
            f"Do you want me to move the "
            f"{folder_path.name} folder "
            "to the Recycle Bin?"
        ),
    )

    if not allowed:
        return "Delete cancelled."

    try:
        folder_name_for_response = (
            folder_path.name
        )

        send2trash(
            str(folder_path)
        )

        return (
            f"Moved the "
            f"{folder_name_for_response} folder "
            "to the Recycle Bin."
        )

    except Exception as error:
        print(
            f"Delete folder error: {error}"
        )

        return (
            f"I couldn't delete the "
            f"{folder_path.name} folder."
        )


# ==================================================
# OPEN FILE
# ==================================================


def _open_indexed_file(match):
    """
    Open one indexed file.
    """

    name, extension, path = match

    file_path = Path(path)

    if not file_path.exists():
        return {
            "response": (
                f"I found {name}{extension} "
                "in the index, but the file "
                "no longer exists."
            ),
            "success": False,
        }

    try:
        os.startfile(
            file_path
        )

        return {
            "response": (
                f"Opening {name}{extension}."
            ),
            "success": True,
        }

    except OSError as error:
        print(
            f"Open file error: {error}"
        )

        return {
            "response": (
                f"I found {name}{extension}, "
                "but I couldn't open it."
            ),
            "success": False,
        }


def _location_label(match):
    """
    Return a useful folder label for a file.
    """

    _, _, path = match

    file_path = Path(path)

    return file_path.parent.name


def open_file(file_name):
    """
    Find and open a file.

    Search order:
    1. Current working folder
    2. Global VoicePilot file index
    """

    global _pending_file_matches

    if not request_permission(
        "open_file"
    ):
        return {
            "response": "Permission denied.",
            "success": False,
            "needs_selection": False,
        }

    file_name = file_name.strip()

    if not file_name:
        return {
            "response": (
                "File name cannot be empty."
            ),
            "success": False,
            "needs_selection": False,
        }

    current_matches = (
        find_files_in_current_folder(
            file_name
        )
    )

    if current_matches:
        matches = current_matches

    else:
        matches = find_files(
            file_name,
            limit=5,
        )

        matches = [
            match
            for match in matches
            if Path(match[2]).exists()
        ]

    if not matches:
        _pending_file_matches = []

        current_folder = (
            get_current_folder()
        )

        if current_folder:
            return {
                "response": (
                    f"I couldn't find a file "
                    f"called {file_name} in "
                    f"{current_folder.name} "
                    "or in the file index."
                ),
                "success": False,
                "needs_selection": False,
            }

        return {
            "response": (
                f"I couldn't find a file "
                f"called {file_name}."
            ),
            "success": False,
            "needs_selection": False,
        }

    if len(matches) == 1:
        _pending_file_matches = []

        result = _open_indexed_file(
            matches[0]
        )

        result[
            "needs_selection"
        ] = False

        return result

    _pending_file_matches = matches

    descriptions = []

    for index, match in enumerate(
        matches,
        start=1,
    ):
        name, extension, path = match

        location = _location_label(
            match
        )

        descriptions.append(
            f"number {index}, "
            f"{name}{extension} "
            f"in {location}"
        )

    choices = ". ".join(
        descriptions
    )

    return {
        "response": (
            f"I found {len(matches)} matching files. "
            f"{choices}. "
            "Which one do you want?"
        ),
        "success": False,
        "needs_selection": True,
    }


# ==================================================
# FILE SELECTION STATE
# ==================================================


def has_pending_file_selection():
    return bool(
        _pending_file_matches
    )


def clear_pending_file_selection():
    global _pending_file_matches

    _pending_file_matches = []


def select_pending_file(selection):
    global _pending_file_matches

    if not _pending_file_matches:
        return {
            "response": (
                "There are no files waiting "
                "for selection."
            ),
            "success": False,
        }

    selection = (
        selection.lower().strip()
    )

    if selection in [
        "cancel",
        "never mind",
        "nevermind",
    ]:
        _pending_file_matches = []

        return {
            "response": (
                "File selection cancelled."
            ),
            "success": False,
        }

    ordinal_choices = {
        "1": 0,
        "one": 0,
        "first": 0,
        "first one": 0,
        "the first one": 0,

        "2": 1,
        "two": 1,
        "second": 1,
        "second one": 1,
        "the second one": 1,

        "3": 2,
        "three": 2,
        "third": 2,
        "third one": 2,
        "the third one": 2,

        "4": 3,
        "four": 3,
        "fourth": 3,
        "fourth one": 3,
        "the fourth one": 3,

        "5": 4,
        "five": 4,
        "fifth": 4,
        "fifth one": 4,
        "the fifth one": 4,
    }

    if selection in ordinal_choices:
        index = ordinal_choices[
            selection
        ]

        if index < len(
            _pending_file_matches
        ):
            match = (
                _pending_file_matches[
                    index
                ]
            )

            _pending_file_matches = []

            return _open_indexed_file(
                match
            )

    path_matches = []

    for match in _pending_file_matches:
        path = match[2].lower()

        if selection in path:
            path_matches.append(
                match
            )

    if len(path_matches) == 1:
        match = path_matches[0]

        _pending_file_matches = []

        return _open_indexed_file(
            match
        )

    if len(path_matches) > 1:
        return {
            "response": (
                "More than one of those files "
                "matches that location. "
                "Please say the file number."
            ),
            "success": False,
        }

    return {
        "response": (
            "I couldn't tell which file you meant. "
            "Please say first, second, third, "
            "or the folder name."
        ),
        "success": False,
    }