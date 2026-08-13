import json
import os
import winreg
from pathlib import Path

from database.database import (
    add_folder,
    add_file,
    clear_folders,
    clear_files,
)


CONFIG_PATH = Path("config") / "config.json"

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
    Windows user folder.
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

        path = Path(folder_path)

        if path.exists():
            return path

    except (
        FileNotFoundError,
        OSError,
    ):
        pass

    return None


def load_search_locations():
    """
    Load configured search locations.

    Desktop, Documents, Downloads and other
    Windows-known folders are resolved using
    their actual Windows locations.
    """

    locations = []

    # --------------------------------------------------
    # WINDOWS KNOWN FOLDERS
    # --------------------------------------------------

    for folder_name in [
        "desktop",
        "documents",
        "downloads",
    ]:
        path = get_windows_folder(
            folder_name
        )

        if (
            path
            and path.exists()
            and path not in locations
        ):
            locations.append(path)

    # --------------------------------------------------
    # USER CONFIGURED LOCATIONS
    # --------------------------------------------------

    try:
        with open(
            CONFIG_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            config = json.load(file)

        configured_locations = config.get(
            "search_locations",
            [],
        )

        for location in configured_locations:
            expanded_location = (
                os.path.expandvars(location)
            )

            path = Path(
                expanded_location
            )

            if (
                path.exists()
                and path not in locations
            ):
                locations.append(path)

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ):
        pass

    return locations


def build_folder_index():
    """
    Rebuild the complete file and folder index.
    """

    print(
        "Building file and folder index..."
    )

    clear_folders()
    clear_files()

    search_locations = (
        load_search_locations()
    )

    folder_count = 0
    file_count = 0

    for base_path in search_locations:
        print(
            f"Scanning: {base_path}"
        )

        add_folder(
            base_path.name,
            base_path,
        )

        folder_count += 1

        try:
            for (
                root,
                directories,
                files,
            ) in os.walk(base_path):

                root_path = Path(root)

                # --------------------------------------
                # FOLDERS
                # --------------------------------------

                for directory in directories:
                    folder_path = (
                        root_path
                        / directory
                    )

                    add_folder(
                        directory,
                        folder_path,
                    )

                    folder_count += 1

                # --------------------------------------
                # FILES
                # --------------------------------------

                for filename in files:
                    file_path = (
                        root_path
                        / filename
                    )

                    file_object = Path(
                        filename
                    )

                    add_file(
                        file_object.stem,
                        file_object.suffix,
                        file_path,
                    )

                    file_count += 1

        except (
            PermissionError,
            OSError,
        ):
            continue

    print(
        f"Indexing complete. "
        f"{folder_count} folders and "
        f"{file_count} files indexed."
    )


if __name__ == "__main__":
    from database.database import (
        create_tables,
    )

    create_tables()

    build_folder_index()