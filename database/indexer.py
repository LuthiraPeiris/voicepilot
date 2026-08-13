import json
import os
from pathlib import Path

from database.database import (
    add_folder,
    add_file,
    clear_folders,
    clear_files,
)


CONFIG_PATH = Path("config") / "config.json"


def load_search_locations():
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

        locations = []

        for location in configured_locations:
            expanded_location = os.path.expandvars(
                location
            )

            path = Path(expanded_location)

            if path.exists():
                locations.append(path)

        return locations

    except (
        FileNotFoundError,
        json.JSONDecodeError,
    ):
        return []


def build_folder_index():
    """
    Rebuild both the folder and file indexes.
    """

    print("Building file and folder index...")

    clear_folders()
    clear_files()

    search_locations = load_search_locations()

    folder_count = 0
    file_count = 0

    for base_path in search_locations:
        print(f"Scanning: {base_path}")

        # Store the base folder itself
        add_folder(
            base_path.name,
            base_path,
        )

        folder_count += 1

        try:
            for root, directories, files in os.walk(
                base_path
            ):
                root_path = Path(root)

                # --------------------------------------
                # INDEX FOLDERS
                # --------------------------------------

                for directory in directories:
                    folder_path = (
                        root_path / directory
                    )

                    add_folder(
                        directory,
                        folder_path,
                    )

                    folder_count += 1

                # --------------------------------------
                # INDEX FILES
                # --------------------------------------

                for filename in files:
                    file_path = (
                        root_path / filename
                    )

                    file_object = Path(filename)

                    file_name = file_object.stem
                    extension = file_object.suffix

                    add_file(
                        file_name,
                        extension,
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
    from database.database import create_tables

    create_tables()

    build_folder_index()