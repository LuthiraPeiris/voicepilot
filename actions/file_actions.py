import os
import winreg
from pathlib import Path

from database.database import find_files
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
    location_name = location_name.lower().strip()

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
                f"A folder called {folder_name} "
                f"already exists in {location}."
            )

        folder_path.mkdir()

        return (
            f"Created folder {folder_name} "
            f"in {location}."
        )

    except OSError as error:
        print(
            f"Create folder error: {error}"
        )

        return (
            f"I couldn't create the folder "
            f"{folder_name}."
        )


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
        os.startfile(file_path)

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

    If several files match, remember them and
    ask the user to choose one.
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
            "response": "File name cannot be empty.",
            "success": False,
            "needs_selection": False,
        }

    matches = find_files(
        file_name,
        limit=5,
    )

    # Remove stale index entries
    matches = [
        match
        for match in matches
        if Path(match[2]).exists()
    ]

    if not matches:
        _pending_file_matches = []

        return {
            "response": (
                f"I couldn't find a file "
                f"called {file_name}."
            ),
            "success": False,
            "needs_selection": False,
        }

    # Only one result
    if len(matches) == 1:
        _pending_file_matches = []

        result = _open_indexed_file(
            matches[0]
        )

        result["needs_selection"] = False

        return result

    # Several results
    _pending_file_matches = matches

    descriptions = []

    for index, match in enumerate(
        matches,
        start=1,
    ):
        name, extension, path = match

        location = _location_label(match)

        descriptions.append(
            f"number {index}, "
            f"{name}{extension} "
            f"in {location}"
        )

    choices = ". ".join(descriptions)

    return {
        "response": (
            f"I found {len(matches)} matching files. "
            f"{choices}. "
            "Which one do you want?"
        ),
        "success": False,
        "needs_selection": True,
    }


def has_pending_file_selection():
    """
    Check whether VoicePilot is waiting for the
    user to choose between matching files.
    """

    return bool(
        _pending_file_matches
    )


def clear_pending_file_selection():
    global _pending_file_matches

    _pending_file_matches = []


def select_pending_file(selection):
    """
    Resolve a follow-up answer such as:

    first
    second
    the second one
    downloads
    documents
    """

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
            "response": "File selection cancelled.",
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

    # --------------------------------------------------
    # SELECT BY NUMBER
    # --------------------------------------------------

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

    # --------------------------------------------------
    # SELECT BY FOLDER / PATH
    # Example: "downloads"
    # --------------------------------------------------

    path_matches = []

    for match in _pending_file_matches:
        path = match[2].lower()

        if selection in path:
            path_matches.append(match)

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