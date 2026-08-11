import os
from pathlib import Path


COMMON_FOLDERS = {
    "desktop": Path.home() / "Desktop",
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
}


def open_common_folder(folder_name):
    folder_name = folder_name.lower().strip()

    if folder_name not in COMMON_FOLDERS:
        return None

    path = COMMON_FOLDERS[folder_name]

    if path.exists():
        os.startfile(path)
        return f"Opening {folder_name}."

    return f"{folder_name} folder was not found."


def search_folder(folder_name):
    folder_name = folder_name.lower().strip()

    search_locations = [
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Downloads",
    ]

    matches = []

    for base_path in search_locations:
        if not base_path.exists():
            continue

        try:
            for root, directories, files in os.walk(base_path):
                for directory in directories:
                    if folder_name == directory.lower():
                        matches.append(Path(root) / directory)

        except PermissionError:
            continue

    if not matches:
        return None

    return matches[0]


def open_folder(folder_name):
    folder_name = folder_name.lower().strip()

    # First check common Windows folders
    common_result = open_common_folder(folder_name)

    if common_result:
        return common_result

    # Otherwise search for the folder
    match = search_folder(folder_name)

    if match:
        os.startfile(match)
        return f"Opening {match.name}."

    return f"I couldn't find a folder called {folder_name}."